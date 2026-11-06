import pathlib
import re

from .activity import implicit_signals
from .config import resolve
from .items import FB_RE, LINK_RE, parse_digest, valid_date
from .items import verdict as _verdict  # noqa: F401 - compatibility for existing integrations
from .storage import LOCK, decay_weight, read_json, utc_now, write_json, write_text

TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+\-]{2,}")
STOP = set("the a an of to in for on and or is are be with you your this that it as at "
           "from by we our how why what new using use into about over under via".split())


def title_keywords(title):
    return {t.lower() for t in TOKEN.findall(title or "")
            if t.lower() not in STOP and len(t) >= 4}


def _paths(cfg):
    s = cfg.get("state", {})
    return (
        pathlib.Path(resolve(s.get("feedback_log", "data/feedback_log.json"))),
        pathlib.Path(resolve(s.get("feedback_state", "data/feedback_state.json"))),
    )


def _load_json(p, default):
    return read_json(p, default)


def _state(cfg):
    _, sp = _paths(cfg)
    return _load_json(sp, {})


def _parse_digest(text):
    return [{k: it[k] for k in ("title", "link", "source", "bucket")} | {
        "verdict": 1 if it["verdict"] == "pos" else -1
    } for it in parse_digest(text) if it["verdict"]]


def _prec(pos, tot):
    return round(pos / tot, 2) if tot else None


def _aggregate(cfg, log):
    fb = cfg.get("feedback", {})
    step, cap, keep = fb.get("bias_step", 6), fb.get("bias_cap", 24), fb.get("remember", 12)
    kstep, kcap = fb.get("keyword_bias_step", 3), fb.get("keyword_bias_cap", 12)
    min_s, drop_p = fb.get("min_source_samples", 4), fb.get("source_drop_precision", 0.34)

    src_net, src_pos, src_tot, kw_net = {}, {}, {}, {}
    bpos, btot = {"rel": 0, "explore": 0}, {"rel": 0, "explore": 0}
    pos = neg = 0
    for e in log:
        v, s, b = e["verdict"], e.get("source", ""), e.get("bucket", "rel")
        weight = decay_weight(e.get("updated_at") or e.get("date"), fb.get("half_life_days", 0))
        src_net[s] = src_net.get(s, 0) + v * weight
        src_tot[s] = src_tot.get(s, 0) + 1
        btot[b] = btot.get(b, 0) + 1
        if v > 0:
            pos += 1
            src_pos[s] = src_pos.get(s, 0) + 1
            bpos[b] = bpos.get(b, 0) + 1
        else:
            neg += 1
        for k in title_keywords(e.get("title", "")):
            kw_net[k] = kw_net.get(k, 0) + v * weight

    source_bias = {s: round(max(-cap, min(cap, n * step)), 2) for s, n in src_net.items() if n}
    keyword_bias = {k: round(max(-kcap, min(kcap, n * kstep)), 2) for k, n in kw_net.items() if n}
    implicit = implicit_signals(cfg, log)
    implicit_src, implicit_kw = {}, {}
    for e in implicit:
        s, weight = e.get("source", ""), e["weight"]
        implicit_src[s] = implicit_src.get(s, 0) + weight
        for k in title_keywords(e.get("title", "")):
            implicit_kw[k] = implicit_kw.get(k, 0) + weight
    # Reading signals have their own small cap; they never alter explicit precision statistics.
    for s, weight in implicit_src.items():
        source_bias[s] = round(min(cap, source_bias.get(s, 0) + min(3, weight * step)), 2)
    for k, weight in implicit_kw.items():
        keyword_bias[k] = round(min(kcap, keyword_bias.get(k, 0) + min(1.5, weight * kstep)), 2)
    keyword_bias = dict(sorted(keyword_bias.items(), key=lambda kv: abs(kv[1]), reverse=True)[:60])

    recent = [e for e in sorted(log, key=lambda e: e.get("updated_at") or e.get("date", ""), reverse=True)
              if decay_weight(e.get("updated_at") or e.get("date"), fb.get("half_life_days", 0)) >= .1]
    liked = [e["title"] for e in recent if e["verdict"] > 0][:keep]
    disliked = [e["title"] for e in recent if e["verdict"] < 0][:keep]

    quality = {
        "overall": _prec(pos, pos + neg),
        "rel": _prec(bpos["rel"], btot["rel"]),
        "explore": _prec(bpos["explore"], btot["explore"]),
        "counts": {"pos": pos, "neg": neg},
    }
    low_sources = []
    for s in src_tot:
        if src_tot[s] < min_s:
            continue
        p = _prec(src_pos.get(s, 0), src_tot[s])
        if p is not None and p < drop_p:
            low_sources.append(s)

    base = cfg.get("digest", {}).get("exploration_ratio", 0.7)
    ratio = base
    if fb.get("adaptive_exploration", True) and btot["explore"] >= 6 and btot["rel"] >= 3:
        ep = bpos["explore"] / btot["explore"]
        rp = bpos["rel"] / btot["rel"]
        if ep < rp - 0.2:
            ratio = max(0.3, base - 0.2)       # 拓展老踩雷 → 收一点
        elif ep > rp + 0.1:
            ratio = min(0.85, base + 0.1)      # 拓展反而更准 → 放更开

    return {
        "source_bias": source_bias, "keyword_bias": keyword_bias,
        "liked": liked, "disliked": disliked, "quality": quality,
        "low_sources": low_sources, "adaptive_ratio": round(ratio, 2), "base_ratio": base,
        "implicit_count": len(implicit),
    }


def collect_feedback(cfg):
    """Reconcile each readable edition by (date, link), including edits and deletions.

    Missing/archived editions keep their history. Any unreadable edition aborts before
    writing, so a transient file error cannot erase feedback. Old duplicate keys collapse.
    """
    with LOCK:
        return _collect_feedback(cfg)


def _collect_feedback(cfg):
    out_dir = pathlib.Path(resolve(cfg["digest"]["output_dir"]))
    log_path, state_path = _paths(cfg)
    old = {(e["date"], e["link"]): e for e in _load_json(log_path, [])}
    current = dict(old)
    if out_dir.exists():
        for f in sorted(out_dir.glob("*.md")):
            if not valid_date(f.stem):
                continue
            # Read the complete file before dropping that date's previous records.
            text = f.read_text(encoding="utf-8")
            current = {key: e for key, e in current.items() if key[0] != f.stem}
            for it in _parse_digest(text):
                key = (f.stem, it["link"])
                entry = {"date": f.stem, **it}
                previous = old.get(key)
                if previous and all(previous.get(k) == v for k, v in entry.items()):
                    current[key] = previous
                else:
                    current[key] = {**entry, "updated_at": utc_now()}
    new = len(current.keys() - old.keys())
    removed = len(old.keys() - current.keys())
    updated = sum(old[k] != current[k] for k in current.keys() & old.keys())
    log = [current[key] for key in sorted(current)]
    state = _aggregate(cfg, log)
    write_json(log_path, log)
    write_json(state_path, state)
    return {"new": new, "updated": updated, "removed": removed,
            "changed": new + updated + removed, **state}


def load_state(cfg):
    """读取上一轮聚合出的反馈状态（来源/关键词偏置、liked/disliked、命中率等）。"""
    return _state(cfg)


_LOCK = LOCK


def set_verdict(cfg, date, link, verdict):
    """把一条简报条目的 反馈:: 行改成 好/差（或清空）。

    直接改 vault 里的 markdown——与用户在 Obsidian 里手写完全等效，
    下次 collect_feedback 自然学到。返回是否真的改了文件。
    """
    token = {"pos": "好", "neg": "差", None: ""}[verdict]
    if not valid_date(date):
        return False
    path = pathlib.Path(resolve(cfg["digest"]["output_dir"])) / f"{date}.md"
    if not path.exists():
        return False
    with _LOCK:
        lines = path.read_text(encoding="utf-8").splitlines()
        hits = [i for i, ln in enumerate(lines) if (m := LINK_RE.match(ln)) and m[2] == link]
        if not hits:
            return False
        for hit in reversed(hits):
            end = next((j for j in range(hit + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
            found = next((j for j in range(hit + 1, end) if FB_RE.match(lines[j])), None)
            label = "Feedback" if any(FB_RE.match(ln) and ln.lower().startswith("feedback")
                                      for ln in lines) else "反馈"
            value = ({"pos": "good", "neg": "bad", None: ""}[verdict]
                     if label == "Feedback" else token)
            replacement = f"{label}::" + (f" {value}" if value else "")
            if found is None:
                lines.insert(end, replacement)
            else:
                lines[found] = replacement
        write_text(path, "\n".join(lines) + "\n")
    return True


def load_source_bias(cfg):
    return _state(cfg).get("source_bias", {})


def load_keyword_bias(cfg):
    return _state(cfg).get("keyword_bias", {})


def load_adaptive_ratio(cfg):
    return _state(cfg).get("adaptive_ratio")


def feedback_for_profile(cfg):
    st = _state(cfg)
    liked, disliked = st.get("liked", []), st.get("disliked", [])
    if not liked and not disliked:
        return ""
    block = "\n\n【用户最近的明确反馈，请据此微调画像侧重】\n"
    if liked:
        block += "觉得有价值：" + "；".join(liked) + "\n"
    if disliked:
        block += "觉得是噪音：" + "；".join(disliked) + "\n"
    return block

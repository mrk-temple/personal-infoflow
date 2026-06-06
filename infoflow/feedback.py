import re
import json
import pathlib

from .client import resolve

POS = {"好", "赞", "+", "👍", "有用", "有价值", "good"}
NEG = {"差", "噪音", "-", "👎", "无用", "没用", "bad"}

LINK_RE = re.compile(r"^##\s+\[(.*?)\]\((.+?)\)\s*$")
META_RE = re.compile(r"^\*\*\d+\*\*(.*)$")
FB_RE = re.compile(r"^反馈::\s*(.*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+\-]{2,}")
STOP = set("the a an of to in for on and or is are be with you your this that it as at "
           "from by we our how why what new using use into about over under via".split())


def title_keywords(title):
    return {t.lower() for t in TOKEN.findall(title or "")
            if t.lower() not in STOP and len(t) >= 4}


def _verdict(token):
    t = token.strip()
    if t in POS:
        return 1
    if t in NEG:
        return -1
    return None


def _paths(cfg):
    s = cfg["state"]
    return (
        pathlib.Path(resolve(s.get("feedback_log", "data/feedback_log.json"))),
        pathlib.Path(resolve(s.get("feedback_state", "data/feedback_state.json"))),
    )


def _load_json(p, default):
    p = pathlib.Path(p)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _state(cfg):
    _, sp = _paths(cfg)
    return _load_json(sp, {})


def _parse_digest(text):
    items, cur = [], None
    for line in text.splitlines():
        m = LINK_RE.match(line)
        if m:
            cur = {"title": m.group(1), "link": m.group(2), "source": "", "bucket": "rel"}
            continue
        if cur and line.startswith("**"):
            mm = META_RE.match(line)
            if mm:
                segs = [p.strip() for p in mm.group(1).split("·") if p.strip()]
                cur["bucket"] = "explore" if any(s == "拓展" for s in segs) else "rel"
                for s in segs:                       # source = 跳过"拓展"和"也被…"后的第一段
                    if s == "拓展" or s.startswith("也被"):
                        continue
                    cur["source"] = s
                    break
            continue
        fm = FB_RE.match(line)
        if fm and cur:
            v = _verdict(fm.group(1))
            if v is not None:
                items.append({**cur, "verdict": v})
            cur = None
    return items


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
        src_net[s] = src_net.get(s, 0) + v
        src_tot[s] = src_tot.get(s, 0) + 1
        btot[b] = btot.get(b, 0) + 1
        if v > 0:
            pos += 1
            src_pos[s] = src_pos.get(s, 0) + 1
            bpos[b] = bpos.get(b, 0) + 1
        else:
            neg += 1
        for k in title_keywords(e.get("title", "")):
            kw_net[k] = kw_net.get(k, 0) + v

    source_bias = {s: max(-cap, min(cap, n * step)) for s, n in src_net.items() if n}
    keyword_bias = {k: max(-kcap, min(kcap, n * kstep)) for k, n in kw_net.items() if n}
    keyword_bias = dict(sorted(keyword_bias.items(), key=lambda kv: abs(kv[1]), reverse=True)[:60])

    liked = [e["title"] for e in reversed(log) if e["verdict"] > 0][:keep]
    disliked = [e["title"] for e in reversed(log) if e["verdict"] < 0][:keep]

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
        "low_sources": low_sources, "adaptive_ratio": round(ratio, 2),
    }


def collect_feedback(cfg):
    out_dir = pathlib.Path(resolve(cfg["digest"]["output_dir"]))
    log_path, state_path = _paths(cfg)
    log = _load_json(log_path, [])
    seen = {(e["date"], e["link"]) for e in log}

    new = 0
    if out_dir.exists():
        for f in sorted(out_dir.glob("*.md")):
            if not DATE_RE.match(f.stem):
                continue
            for it in _parse_digest(f.read_text(encoding="utf-8")):
                key = (f.stem, it["link"])
                if key in seen:
                    continue
                seen.add(key)
                log.append({"date": f.stem, **it})
                new += 1

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")

    state = _aggregate(cfg, log)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"new": new, **state}


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

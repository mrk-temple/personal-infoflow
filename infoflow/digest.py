import pathlib
from collections import defaultdict
from datetime import date

from .config import resolve
from .feedback import load_adaptive_ratio
from .storage import LOCK, write_text


def write_digest(cfg, ranked, picked_out=None):
    d = cfg["digest"]
    max_items = d["max_items"]
    max_per_source = d.get("max_per_source", 0)
    ratio = load_adaptive_ratio(cfg)
    if ratio is None:
        ratio = d.get("exploration_ratio", 0.7)
    min_rel = d.get("min_score", 0)
    n_explore = round(max_items * ratio)
    n_main = max_items - n_explore

    per_source = defaultdict(int)
    picked, chosen = [], set()

    def can_take(r):
        return not (max_per_source and per_source[r["source"]] >= max_per_source)

    def take(r, bucket):
        r["bucket"] = bucket
        picked.append(r)
        chosen.add(r["link"])
        per_source[r["source"]] += 1

    for r in sorted(ranked, key=lambda x: x.get("relevance", 0), reverse=True):
        if len([p for p in picked if p["bucket"] == "rel"]) >= n_main:
            break
        if r["link"] in chosen or not can_take(r) or r.get("relevance", 0) < min_rel:
            continue
        take(r, "rel")

    for r in sorted((x for x in ranked if x["link"] not in chosen),
                    key=lambda x: x.get("exploration", 0), reverse=True):
        if len([p for p in picked if p["bucket"] == "explore"]) >= n_explore:
            break
        if not can_take(r):
            continue
        take(r, "explore")

    for r in sorted(ranked, key=lambda x: x["score"], reverse=True):
        if len(picked) >= max_items:
            break
        if r["link"] in chosen or not can_take(r):
            continue
        take(r, "explore")

    n_rel = sum(1 for p in picked if p["bucket"] == "rel")
    n_exp = len(picked) - n_rel
    picked.sort(key=lambda x: x["score"], reverse=True)
    if picked_out is not None:
        picked_out.extend(picked)
    en = cfg.get("language") == "en"

    from datetime import datetime
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M")
    out_dir = pathlib.Path(resolve(d["output_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.md"
    appending = path.exists()

    lines = []
    if appending:
        # 同一天再次运行：追加到已有文件底部，不覆盖
        lines += ["", "---", "", f"## 🕐 {now} " + ("Update" if en else "追加")]
    else:
        lines += [
            f"# {'Personal InfoFlow' if en else '信息简报'} {today}",
            "",
            ("Write good or bad after `Feedback::` to teach the next run." if en else
             "标注方法：在每条的 `反馈::` 后写 好 或 差，下次运行自动学习。"),
        ]
        note = cfg.get("portrait", {}).get("note_path")
        if note:
            lines += ["", f"画像 → [[{pathlib.Path(note).stem}]]"]

    lines += [
        "",
        (f"{now} Edition: {len(picked)} stories ({n_rel} relevant · {n_exp} explore), "
         f"{len(per_source)} sources, exploration ratio {ratio}." if en else
         f"{now} 本轮：精选 {len(picked)} 条（贴合 {n_rel} · 拓展 {n_exp}），"
         f"覆盖 {len(per_source)} 个来源，拓展比例 {ratio}。"),
        "",
    ]

    for r in picked:
        tag = (" · Explore" if en else " · 拓展") if r.get("bucket") == "explore" else ""
        dup = ((f" · also in {r['dup_count'] - 1} other sources" if en else
                f" · 也被 {r['dup_count'] - 1} 个其他源报道") if r.get("dup_count", 1) > 1 else "")
        mark = " 📄" if r.get("enriched") else ""
        title = str(r["title"]).replace("\n", " ").replace("\r", " ")
        source = str(r["source"]).replace("\n", " ").replace("\r", " ")
        reason = "\n".join("> " + ln for ln in str(r["reason"]).splitlines())
        lines += [
            f"## [{title}]({r['link']})",
            f"**{r['score']}**{tag} · {source}{dup}{mark}",
            "",
            reason,
            "",
            "Feedback:: " if en else "反馈:: ",
            "",
        ]

    text = "\n".join(lines)
    with LOCK:
        previous = path.read_text(encoding="utf-8") if path.exists() else ""
        write_text(path, previous + text + "\n")
    return path, len(picked)

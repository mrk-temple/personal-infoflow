import pathlib
from datetime import date
from collections import defaultdict

from .client import resolve
from .feedback import load_adaptive_ratio


def write_digest(cfg, ranked):
    d = cfg["digest"]
    max_items = d["max_items"]
    max_per_source = d.get("max_per_source", 0)
    ratio = load_adaptive_ratio(cfg) or d.get("exploration_ratio", 0.7)  # D2 自适应
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
        lines += ["", "---", "", f"## 🕐 {now} 追加"]
    else:
        lines += [
            f"# 信息简报 {today}",
            "",
            "标注方法：在每条的 `反馈::` 后写 好 或 差，下次运行自动学习。",
        ]
        note = cfg.get("portrait", {}).get("note_path")
        if note:
            lines += ["", f"画像 → [[{pathlib.Path(note).stem}]]"]

    lines += [
        "",
        f"{now} 本轮：精选 {len(picked)} 条（贴合 {n_rel} · 拓展 {n_exp}），"
        f"覆盖 {len(per_source)} 个来源，拓展比例 {ratio}。",
        "",
    ]

    for r in picked:
        tag = " · 拓展" if r.get("bucket") == "explore" else ""
        dup = f" · 也被 {r['dup_count'] - 1} 个其他源报道" if r.get("dup_count", 1) > 1 else ""
        mark = " 📄" if r.get("enriched") else ""
        lines += [
            f"## [{r['title']}]({r['link']})",
            f"**{r['score']}**{tag} · {r['source']}{dup}{mark}",
            "",
            f"> {r['reason']}",
            "",
            "反馈:: ",
            "",
        ]

    text = "\n".join(lines)
    with open(path, "a" if appending else "w", encoding="utf-8") as f:
        f.write(text if appending else text + "\n")
    return path, len(picked)

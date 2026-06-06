from .client import chat, extract_json
from .feedback import load_source_bias, load_keyword_bias, title_keywords

RANK_SYS = """你是为特定用户做内容筛选的助手。给你这位用户的"兴趣画像"和一批候选文章。
为每篇文章打两个分（都是 0-100）：
- relevance：与他已有兴趣 / 当前关注的契合度
- exploration：作为"拓展视野"的价值——邻近、新鲜、能帮他打开新方向的给高分；
  老生常谈或他必然已熟知的给低分。哪怕不完全落在现有笔记范围内，只要相关领域的边缘、
  有启发性，exploration 就该高。
reason：一句简短中文，必须具体说出"这条对他到底有什么用 / 为什么值得看"，
  而不是泛泛复述标题。若有具体的关键点（新方法、关键数据、可借鉴之处）就点出来。
只输出 JSON，格式严格为：{"items":[{"id":0,"relevance":80,"exploration":40,"reason":"..."}]}
不要任何额外文字。"""


def rank_items(client, cfg, profile, items):
    results = {}
    batch = cfg["rank"]["batch_size"]
    model = cfg["models"]["rank"]
    w = cfg["rank"].get("breadth_weight", 0.4)
    src_bias = load_source_bias(cfg)          # 来源级偏置（D 反馈）
    kw_bias = load_keyword_bias(cfg)          # 关键词级偏置（D1）

    for i in range(0, len(items), batch):
        chunk = items[i:i + batch]
        listing = "\n\n".join(
            f'[{j}] 标题：{it["title"]}\n来源：{it["source"]}\n摘要：{it["summary"]}'
            for j, it in enumerate(chunk)
        )
        user = f"兴趣画像：\n{profile}\n\n候选文章：\n{listing}"
        raw = chat(client, model, RANK_SYS, user, temperature=0.2)

        try:
            parsed = extract_json(raw).get("items", [])
        except Exception:
            parsed = []

        for r in parsed:
            idx = r.get("id")
            if isinstance(idx, int) and 0 <= idx < len(chunk):
                it = chunk[idx]
                rel = r.get("relevance", 0)
                exp = r.get("exploration", 0)
                base = rel * (1 - w) + exp * w
                kb = sum(kw_bias.get(k, 0) for k in title_keywords(it["title"]))
                kb = max(-15, min(15, kb))
                sb = it.get("_sim_boost", 0)          # 与"点过好"的内容语义相近的加分
                score = max(0, min(100, round(base) + src_bias.get(it["source"], 0) + kb + sb))
                results[it["link"]] = {
                    **it,
                    "relevance": rel, "exploration": exp,
                    "score": score, "reason": r.get("reason", ""),
                }
        print(f"  打分进度 {min(i + batch, len(items))}/{len(items)}")

    return sorted(results.values(), key=lambda x: x["score"], reverse=True)

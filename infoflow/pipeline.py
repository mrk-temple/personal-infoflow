"""核心编排：CLI 和 Hermes skill 都调这里，逻辑只此一份。"""
import json
import pathlib

from .client import resolve
from .feedback import collect_feedback
from .profile import load_profile
from .fetch import fetch_items
from .cluster import cluster_items
from . import embed as _embed
from .semantic import embed_items, cluster_semantic, build_anchors, liked_similarity
from .enrich import enrich
from .rank import rank_items
from .digest import write_digest
from .portrait import generate_portrait, write_profile_note


def load_seen(path):
    p = pathlib.Path(resolve(path))
    if p.exists():
        return set(json.loads(p.read_text(encoding="utf-8")))
    return set()


def save_seen(path, seen):
    p = pathlib.Path(resolve(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")


def run(cfg, client, refresh_profile=False, portrait=False, feedback_only=False, log=print):
    """跑一轮信息流。返回结果 dict（供 skill / 调用方使用）。"""
    result = {"digest_path": None, "picked": 0, "feedback": None}

    log("· 收集反馈 ...")
    fb = collect_feedback(cfg)
    result["feedback"] = fb
    log(f"  新增标注 {fb['new']} 条（累计 赞 {fb['quality']['counts']['pos']} / 踩 {fb['quality']['counts']['neg']}）")
    q = fb.get("quality", {})
    if q.get("overall") is not None:
        log(f"  命中率：总体 {q['overall']} | 贴合 {q.get('rel')} | 拓展 {q.get('explore')}")
    if fb.get("adaptive_ratio") is not None:
        log(f"  自适应拓展比例：{fb['adaptive_ratio']}")
    if fb.get("low_sources"):
        log("  建议下线（命中率持续偏低）：" + "，".join(fb["low_sources"]))
    if feedback_only:
        return result

    use_emb = _embed.available(cfg)
    if cfg.get("embedding", {}).get("enabled", False) and not use_emb:
        log("  语义层：已开启但缺 fastembed，回退标题去重")
    elif use_emb:
        log(f"  语义层：开启（锚点 {build_anchors(cfg)} 条）")

    log("· 加载兴趣画像 ...")
    profile = load_profile(client, cfg, refresh=refresh_profile)

    if (refresh_profile or portrait) and cfg.get("portrait", {}).get("enabled", True):
        log("· 生成画像配图 ...")
        try:
            img, prompt = generate_portrait(client, cfg, profile)
            note = write_profile_note(cfg, profile, img, prompt)
            log(f"  配图已存 {img}")
            result["portrait"] = str(img)
        except Exception as e:
            log(f"  画像生成失败（跳过）：{e}")

    log("· 抓取内容源 ...")
    items = fetch_items(cfg)
    seen = load_seen(cfg["state"]["seen_path"])
    fresh = [it for it in items if it["link"] not in seen]
    log(f"  共 {len(items)} 条，去掉已见后 {len(fresh)} 条新内容")
    if not fresh:
        log("没有新内容，结束。")
        return result

    cl = cfg.get("cluster", {})
    cluster_on = cl.get("enabled", True)
    if use_emb:
        embed_items(cfg, fresh)
        thr = cfg.get("embedding", {}).get("cluster_threshold", 0.86)
        clustered = cluster_semantic(fresh, thr) if cluster_on else fresh
        liked_similarity(cfg, clustered)
        boost_max = cfg.get("embedding", {}).get("liked_boost_max", 12)
        for it in clustered:
            it["_sim_boost"] = round(it.get("_sim_liked", 0.0) * boost_max)
        log(f"  语义去重后 {len(clustered)} 条")
    else:
        clustered = cluster_items(fresh, cl.get("title_threshold", 0.82)) if cluster_on else fresh
        log(f"  聚类去重后 {len(clustered)} 条")

    if cfg.get("fetch", {}).get("full_text"):
        log("· 抓正文 ...")
        enrich(clustered, cfg)

    log("· 打分排序 ...")
    ranked = rank_items(client, cfg, profile, clustered)

    log("· 写入简报 ...")
    path, n = write_digest(cfg, ranked)
    log(f"  已写入 {path}（精选 {n} 条）")
    result["digest_path"] = str(path)
    result["picked"] = n

    for it in fresh:
        seen.add(it["link"])
    save_seen(cfg["state"]["seen_path"], seen)
    log("完成。")
    return result

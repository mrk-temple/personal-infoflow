"""核心编排：CLI 和 Hermes skill 都调这里，逻辑只此一份。"""
import pathlib

from . import embed as _embed
from .capture import CaptureError, sync_telegram
from .cluster import cluster_items
from .config import resolve
from .digest import write_digest
from .enrich import enrich
from .feedback import collect_feedback
from .fetch import fetch_items
from .portrait import generate_portrait, write_profile_note
from .profile import load_profile
from .rank import rank_items
from .semantic import build_anchors, cluster_semantic, embed_items, liked_similarity
from .storage import read_json, write_json


def load_seen(path):
    p = pathlib.Path(resolve(path))
    return set(read_json(p, []))


def save_seen(path, seen):
    p = pathlib.Path(resolve(path))
    write_json(p, sorted(seen))


def run(cfg, client, refresh_profile=False, portrait=False, feedback_only=False, log=print):
    """跑一轮信息流。返回结果 dict（供 skill / 调用方使用）。"""
    result = {"digest_path": None, "picked": 0, "feedback": None}
    en = cfg.get("language") == "en"

    def say(zh, english):
        log(english if en else zh)

    say("· 收集反馈 ...", "· Synchronizing feedback ...")
    fb = collect_feedback(cfg)
    result["feedback"] = fb
    say(f"  新增 {fb['new']} · 更新 {fb['updated']} · 清除 {fb['removed']} 条标注",
        f"  Feedback: {fb['new']} new · {fb['updated']} updated · {fb['removed']} cleared")
    q = fb.get("quality", {})
    if q.get("overall") is not None:
        say(f"  命中率：总体 {q['overall']} | 贴合 {q.get('rel')} | 拓展 {q.get('explore')}",
            f"  Precision: overall {q['overall']} | relevant {q.get('rel')} | explore {q.get('explore')}")
    if fb.get("adaptive_ratio") is not None:
        say(f"  自适应拓展比例：{fb['adaptive_ratio']}", f"  Exploration ratio: {fb['adaptive_ratio']}")
    if fb.get("low_sources"):
        say("  建议检查低命中来源：" + "，".join(fb["low_sources"]),
            "  Sources with low precision: " + ", ".join(fb["low_sources"]))
    if feedback_only:
        return result

    if cfg.get("telegram", {}).get("enabled"):
        say("· 同步 Telegram 捕获 ...", "· Receiving Telegram captures ...")
        try:
            result["telegram"] = sync_telegram(cfg)
            say(f"  接收 {result['telegram']['received']} 条", f"  Received {result['telegram']['received']} captures")
        except CaptureError as exc:
            result["telegram_error"] = str(exc)
            say(f"  Telegram 暂未同步：{exc}", f"  Telegram sync skipped: {exc}")

    use_emb = _embed.available(cfg)
    if cfg.get("embedding", {}).get("enabled", False) and not use_emb:
        say("  语义层未就绪，回退标题去重", "  Embeddings unavailable; using title deduplication")
    elif use_emb:
        count = build_anchors(cfg)
        say(f"  语义层：开启（锚点 {count} 条）", f"  Embeddings enabled ({count} anchors)")

    say("· 加载兴趣画像 ...", "· Loading your interest profile ...")
    profile = load_profile(client, cfg, refresh=refresh_profile)

    if portrait or (refresh_profile and cfg.get("portrait", {}).get("enabled", False)):
        say("· 生成画像配图 ...", "· Generating a profile illustration ...")
        try:
            img, prompt = generate_portrait(client, cfg, profile)
            write_profile_note(cfg, profile, img, prompt)
            say(f"  配图已存 {img}", f"  Illustration saved: {img}")
            result["portrait"] = str(img)
        except Exception as e:
            if portrait:
                raise
            say(f"  配图生成失败（跳过）：{e}", f"  Illustration skipped: {e}")
    if portrait:
        return result

    say("· 抓取内容源 ...", "· Fetching sources ...")
    items = fetch_items(cfg, log=log)
    result["sources"] = cfg.get("_source_report", [])
    seen = load_seen(cfg["state"]["seen_path"])
    fresh = [it for it in items if it["link"] not in seen]
    result["fetched"], result["fresh"] = len(items), len(fresh)
    say(f"  共 {len(items)} 条，去掉已见后 {len(fresh)} 条新内容",
        f"  {len(items)} fetched · {len(fresh)} unpublished stories")
    if not fresh:
        say("没有新内容，结束。", "No unpublished stories. Finished.")
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
        say(f"  语义去重后 {len(clustered)} 条", f"  {len(clustered)} stories after semantic deduplication")
    else:
        clustered = cluster_items(fresh, cl.get("title_threshold", 0.82)) if cluster_on else fresh
        say(f"  聚类去重后 {len(clustered)} 条", f"  {len(clustered)} stories after title deduplication")

    if cfg.get("fetch", {}).get("full_text"):
        say("· 抓正文 ...", "· Retrieving article text ...")
        enrich(clustered, cfg, log=log)

    say("· 打分排序 ...", "· Ranking stories ...")
    ranked = rank_items(client, cfg, profile, clustered, log=log)

    say("· 写入简报 ...", "· Writing your digest ...")
    picked = []
    path, n = write_digest(cfg, ranked, picked_out=picked)
    say(f"  已写入 {path}（精选 {n} 条）", f"  Saved {n} stories to {path}")
    result["digest_path"] = str(path)
    result["picked"] = n

    for it in picked:
        seen.add(it["link"])
        seen.update(it.get("dup_links", []))
    save_seen(cfg["state"]["seen_path"], seen)
    say("完成。", "Finished.")
    return result

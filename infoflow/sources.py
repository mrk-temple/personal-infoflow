import re
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

import feedparser

UA = {"User-Agent": "infoflow/0.1 (personal feed)"}


def _within_days(entry, days):
    pub = entry.get("published_parsed") or entry.get("updated_parsed")
    if not pub:
        return True
    dt = datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def _get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


# ---- 各类源的适配器：都返回 {title, link, summary, source} 列表 ----

def from_rss(spec, cfg):
    url = spec.get("url")
    if not url:
        raise ValueError("rss 源缺少 url 字段（检查 config 里这一条是不是漏写/缩进错了 url）")
    d = feedparser.parse(url)
    source = spec.get("name") or d.feed.get("title", spec["url"])
    out = []
    for e in d.entries[: spec.get("limit", cfg["fetch"]["per_feed"])]:
        if not e.get("link") or not _within_days(e, cfg["fetch"]["days"]):
            continue
        out.append({
            "title": e.get("title", "(无标题)"),
            "link": e["link"],
            "summary": e.get("summary", "")[:500],
            "source": source,
        })
    return out


def from_hackernews(spec, cfg):
    n = spec.get("limit", 30)
    data = _get_json(f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={n}")
    out = []
    for h in data.get("hits", []):
        link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        out.append({
            "title": h.get("title", "(无标题)"),
            "link": link,
            "summary": f"{h.get('points', 0)} 分 · {h.get('num_comments', 0)} 评论",
            "source": "Hacker News",
        })
    return out


def from_reddit(spec, cfg):
    sub = spec["subreddit"]
    n = spec.get("limit", 25)
    window = spec.get("window", "day")
    data = _get_json(f"https://www.reddit.com/r/{sub}/top.json?t={window}&limit={n}")
    out = []
    for c in data.get("data", {}).get("children", []):
        p = c.get("data", {})
        link = p.get("url_overridden_by_dest") or ("https://www.reddit.com" + p.get("permalink", ""))
        out.append({
            "title": p.get("title", "(无标题)"),
            "link": link,
            "summary": (p.get("selftext", "") or "")[:500],
            "source": f"r/{sub}",
        })
    return out


def from_arxiv(spec, cfg):
    cat = spec["category"]
    n = spec.get("limit", 30)
    url = (f"http://export.arxiv.org/api/query?search_query=cat:{cat}"
           f"&sortBy=submittedDate&sortOrder=descending&max_results={n}")
    d = feedparser.parse(url)
    out = []
    for e in d.entries:
        if not e.get("link"):
            continue
        out.append({
            "title": e.get("title", "(无标题)").replace("\n", " ").strip(),
            "link": e["link"],
            "summary": e.get("summary", "")[:500],
            "source": f"arXiv {cat}",
        })
    return out


def from_googlenews(spec, cfg):
    """按关键词搜新闻——专门用来拉"邻近但你笔记里没有"的主题，主动加宽面。"""
    out = []
    for q in spec.get("queries", []):
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q) + "&hl=en-US&gl=US&ceid=US:en"
        d = feedparser.parse(url)
        for e in d.entries[: spec.get("limit", 10)]:
            if not e.get("link") or not _within_days(e, cfg["fetch"]["days"]):
                continue
            out.append({
                "title": e.get("title", "(无标题)"),
                "link": e["link"],
                "summary": e.get("summary", "")[:300],
                "source": f"News: {q}",
            })
    return out


def from_github(spec, cfg):
    """又新又火：取最近 since_days 天内新建、按 star 排序的仓库。"""
    since = (datetime.now(timezone.utc) - timedelta(days=spec.get("since_days", 14))).strftime("%Y-%m-%d")
    q = f"created:>={since}"
    if spec.get("language"):
        q += f" language:{spec['language']}"
    if spec.get("topic"):
        q += f" topic:{spec['topic']}"
    n = spec.get("limit", 15)
    url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q)
           + f"&sort=stars&order=desc&per_page={n}")
    data = _get_json(url)
    out = []
    for repo in data.get("items", []):
        desc = (repo.get("description") or "")[:200]
        out.append({
            "title": repo.get("full_name", "(无名仓库)"),
            "link": repo.get("html_url"),
            "summary": f"★{repo.get('stargazers_count', 0)} · {desc}",
            "source": "GitHub 新热",
        })
    return [it for it in out if it["link"]]


_CID_RE = re.compile(r'"(?:channelId|externalId)":"(UC[0-9A-Za-z_\-]{20,})"')


def _resolve_handle(handle):
    """把 @handle 解析成 channel_id（抓频道页提取）。"""
    h = handle.lstrip("@")
    try:
        req = urllib.request.Request(f"https://www.youtube.com/@{h}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read(800000).decode("utf-8", "ignore")
        m = _CID_RE.search(html) or re.search(r"/channel/(UC[0-9A-Za-z_\-]{20,})", html)
        return m.group(1) if m else None
    except Exception:
        return None


def from_youtube(spec, cfg):
    """YouTube 频道/播放列表/@handle 的原生 RSS——免费、无需 API key。"""
    targets = [("channel_id", c) for c in spec.get("channels", [])]
    targets += [("playlist_id", p) for p in spec.get("playlists", [])]
    for h in spec.get("handles", []):                 # 支持直接填 @handle，自动解析
        cid = _resolve_handle(h)
        if cid:
            targets.append(("channel_id", cid))
        else:
            print(f"  [youtube] 解析不了 handle {h}，跳过")
    out = []
    for kind, ident in targets:
        d = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?{kind}={ident}")
        source = d.feed.get("title", ident)
        for e in d.entries[: spec.get("limit", 10)]:
            if not e.get("link") or not _within_days(e, cfg["fetch"]["days"]):
                continue
            summary = e.get("media_description") or e.get("summary") or ""
            out.append({
                "title": e.get("title", "(无标题)"),
                "link": e["link"],
                "summary": summary[:500],
                "source": f"YouTube · {source}",
            })
    return out


def from_twitter(spec, cfg):
    """X/推特：必须指向你自建的 RSSHub（X 没有免费公共 RSS）。"""
    base = spec.get("base", "").rstrip("/")
    if not base:
        raise ValueError("twitter 源需要 base（指向你自建的 RSSHub），X 没有免费公共 RSS")
    out = []
    for handle in spec.get("handles", []):
        h = handle.lstrip("@")
        d = feedparser.parse(f"{base}/twitter/user/{h}")
        for e in d.entries[: spec.get("limit", 15)]:
            if not e.get("link") or not _within_days(e, cfg["fetch"]["days"]):
                continue
            out.append({
                "title": (e.get("title", "") or "")[:120] or "(推文)",
                "link": e["link"],
                "summary": e.get("summary", "")[:500],
                "source": f"X · @{h}",
            })
    return out


ADAPTERS = {
    "rss": from_rss,
    "hackernews": from_hackernews,
    "reddit": from_reddit,
    "arxiv": from_arxiv,
    "googlenews": from_googlenews,
    "github": from_github,
    "youtube": from_youtube,
    "twitter": from_twitter,
}


def _label(spec):
    return spec.get("name") or spec.get("url") or spec.get("subreddit") \
        or spec.get("category") or spec.get("topic") or spec.get("language") \
        or ",".join(spec.get("channels", []) + spec.get("playlists", []) + spec.get("handles", [])) \
        or ",".join(spec.get("queries", [])) or ""


def gather(cfg):
    items, seen = [], set()

    specs = list(cfg.get("sources", []))
    # 兼容旧的 feeds: 列表，按 rss 处理
    for url in cfg.get("feeds", []):
        specs.append({"type": "rss", "url": url})

    for spec in specs:
        if not spec.get("enabled", True):
            continue
        fn = ADAPTERS.get(spec.get("type"))
        if not fn:
            print(f"  跳过未知来源类型：{spec.get('type')}")
            continue
        try:
            kept = 0
            for it in fn(spec, cfg):
                if it.get("link") and it["link"] not in seen:
                    seen.add(it["link"])
                    items.append(it)
                    kept += 1
            print(f"  [{spec['type']}] {_label(spec)} → {kept} 条")
        except Exception as e:
            print(f"  [{spec.get('type')}] {_label(spec)} 抓取失败（跳过）：{e}")

    return items

import re
import urllib.request
from html.parser import HTMLParser

try:
    import trafilatura  # 装了就用它，正文提取质量高很多
except ImportError:
    trafilatura = None

UA = {"User-Agent": "Mozilla/5.0 (infoflow personal feed)"}
_SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript"}


class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in _SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.out.append(data.strip())


def _strip_html(html):
    p = _Stripper()
    try:
        p.feed(html)
    except Exception:
        pass
    return re.sub(r"\s+", " ", " ".join(p.out)).strip()


def fetch_fulltext(url, timeout=20, cap=4000):
    if not url.startswith(("http://", "https://")):
        return ""
    if trafilatura:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                txt = trafilatura.extract(downloaded, include_comments=False) or ""
                if txt.strip():
                    return txt[:cap]
        except Exception:
            pass
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ct = r.headers.get("Content-Type", "")
            if ct and "html" not in ct and "xml" not in ct:
                return ""
            html = r.read(1_500_000).decode("utf-8", "ignore")
        return _strip_html(html)[:cap]
    except Exception:
        return ""


def enrich(items, cfg):
    """给排在前面的若干条抓正文，替换掉截断的 RSS 摘要。limit 控成本/时间。"""
    f = cfg.get("fetch", {})
    if not f.get("full_text"):
        return items
    limit = f.get("full_text_limit", 40)
    cap = f.get("full_text_max_chars", 4000)
    to = f.get("full_text_timeout", 20)

    done = 0
    for it in items:
        if done >= limit:
            break
        # GitHub / YouTube 这类摘要本身够用或抓正文无意义，跳过省时间
        if it.get("source", "").startswith(("GitHub", "YouTube", "X ·")):
            continue
        txt = fetch_fulltext(it.get("link", ""), to, cap)
        done += 1
        if txt and len(txt) > len(it.get("summary", "")):
            it["summary"] = txt
            it["enriched"] = True
        print(f"  抓正文 {done}/{min(limit, len(items))}", end="\r")
    if done:
        print()
    return items

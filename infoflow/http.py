"""极简 HTTP 工具：统一 User-Agent、超时与读取上限。

各源/抓取模块原本各写一份 urllib + UA，散落且不一致。集中到这里，
行为可预期，也方便以后统一加重试/缓存。
"""
import json
import urllib.request

# 抓 API/RSS 用的中性 UA；抓网页正文时有的站点对 UA 挑剔，调用方可自带 headers。
DEFAULT_UA = "infoflow/0.3 (personal feed)"
BROWSER_UA = "Mozilla/5.0 (infoflow personal feed)"


def get_bytes(url, *, timeout=30, headers=None, ua=DEFAULT_UA, max_bytes=None):
    """GET 原始字节。``max_bytes`` 给定时只读这么多（防超大页面撑爆内存）。"""
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        content_type = r.headers.get("Content-Type", "")
        data = r.read(max_bytes) if max_bytes else r.read()
    return data, content_type


def get_text(url, *, timeout=30, headers=None, ua=DEFAULT_UA, max_bytes=None, encoding="utf-8"):
    """GET 并按 ``encoding`` 解码为文本（解码错误忽略）。返回 ``(text, content_type)``。"""
    data, content_type = get_bytes(
        url, timeout=timeout, headers=headers, ua=ua, max_bytes=max_bytes
    )
    return data.decode(encoding, "ignore"), content_type


def get_json(url, *, timeout=30, headers=None, ua=DEFAULT_UA):
    """GET 并解析 JSON。"""
    text, _ = get_text(url, timeout=timeout, headers=headers, ua=ua, max_bytes=5_000_000)
    return json.loads(text)


def post_json(url, payload, *, timeout=60, headers=None, ua=DEFAULT_UA):
    """POST JSON 并解析返回的 JSON（给本地 ollama 这类用）。"""
    h = {"User-Agent": ua, "Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=h
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(5_000_000))

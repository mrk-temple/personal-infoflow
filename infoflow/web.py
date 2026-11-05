"""Web 界面：``python -m infoflow --web`` 后浏览器打开。

极简实现——标准库 http.server，零新增依赖。vault 里的 markdown 仍是唯一事实源：
网页上点「好/差」直接写回简报的 ``反馈::`` 行（与 Obsidian 手写等效），
跑一轮就是调同一份 ``pipeline.run``，进度实时推到页面。
"""
import json
import re
import threading
import urllib.parse
from datetime import date
from pathlib import Path

from . import webapp
from .client import model_status
from .config import resolve
from .feedback import set_verdict

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---- 共享状态：一轮管线的进度日志与运行标志 ----

class RunState:
    """当前/最近一轮的进度。单进程内一个 Web 页消费，加锁保平安。"""

    def __init__(self):
        self._lock = threading.Lock()
        self.lines = []          # 进度行
        self.running = False
        self.error = None
        self.done = False        # 本轮是否已结束（成功或失败）
        self.result = None       # pipeline.run 的返回 dict

    def _reset_locked(self):
        self.lines, self.running = [], True
        self.error, self.done, self.result = None, False, None

    def try_start(self):
        """原子地开新一轮：没在跑才重置并置 running。返回是否成功。"""
        with self._lock:
            if self.running:
                return False
            self._reset_locked()
            return True

    def log(self, msg):
        with self._lock:
            self.lines.append(str(msg))

    def finish(self, result=None, error=None):
        with self._lock:
            self.running, self.done = False, True
            self.error, self.result = error, result

    def snapshot(self):
        with self._lock:
            return {
                "running": self.running,
                "done": self.done,
                "error": self.error,
                "lines": list(self.lines),
                "result": self.result,
            }


RUN = RunState()


def run_async(cfg, refresh_profile=False, feedback_only=False):
    """后台线程跑一轮管线，进度写入 RUN。同一时刻只允许一轮。"""

    def work():
        from .client import get_client
        from .pipeline import run
        try:
            # 本地反馈汇总不调用模型，也不应要求先配置密钥。
            client = None if feedback_only else get_client()
            result = run(cfg, client, refresh_profile=refresh_profile,
                         feedback_only=feedback_only, log=RUN.log)
            RUN.finish(result=result)
        except BaseException as e:                      # 线程里要兜住一切，送到页面
            RUN.finish(error=f"{type(e).__name__}: {e}")

    if not RUN.try_start():
        raise RuntimeError("已有任务在跑")
    threading.Thread(target=work, daemon=True).start()


# ---- 简报解析：把当日 markdown 拆成结构化条目（供前端渲染）----

_ITEM_RE = re.compile(r"^##\s+\[(.*?)\]\((.+?)\)\s*$")
_META_RE = re.compile(r"^\*\*(\d+)\*\*(.*)$")
_DUP_RE = re.compile(r"也被\s*(\d+)\s*个其他源报道")
_FB_RE = re.compile(r"^反馈::\s*(.*)$")


def parse_digest(text):
    """解析简报 markdown → [{title, link, score, source, bucket, enriched,
    dup_count, reason, verdict}]。与 feedback._parse_digest 同一套格式约定。"""
    items, cur = [], None
    for line in text.splitlines():
        m = _ITEM_RE.match(line)
        if m:
            cur = {"title": m.group(1), "link": m.group(2), "score": "",
                   "source": "", "bucket": "rel", "dup_count": 1,
                   "enriched": False, "reason": "", "verdict": None}
            items.append(cur)
            continue
        if cur is None:
            continue
        mm = _META_RE.match(line)
        if mm:
            cur["score"] = mm.group(1)
            rest = mm.group(2)
            cur["enriched"] = "📄" in rest
            segs = [p.strip() for p in rest.split("·") if p.strip() and p.strip() != "📄"]
            cur["bucket"] = "explore" if any(s == "拓展" for s in segs) else "rel"
            for s in segs:                       # 先扫全段拿"也被…"，再取第一个来源
                dm = _DUP_RE.search(s)
                if dm:
                    cur["dup_count"] = int(dm.group(1)) + 1
            cur["source"] = next((s for s in segs
                                  if s != "拓展" and not _DUP_RE.search(s)), "")
            continue
        fm = _FB_RE.match(line)
        if fm:
            t = fm.group(1).strip()
            cur["verdict"] = "pos" if t in ("好", "赞", "+", "👍", "有用", "有价值", "good") \
                else ("neg" if t in ("差", "噪音", "-", "👎", "无用", "没用", "bad") else None)
            cur = None                                     # 条目到此结束
            continue
        if line.startswith("> ") and not cur["reason"]:
            cur["reason"] = line[2:].strip()
    return items


def today_digest_path(cfg):
    d = Path(resolve(cfg["digest"]["output_dir"])) / f"{date.today().isoformat()}.md"
    return d


# ---- HTTP 服务 ----

class Handler:
    """混进 http.server.BaseHTTPRequestHandler 的方法集（见 serve()）。"""

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # -- API --

    def api_status(self, cfg, q):
        p = today_digest_path(cfg)
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        items = parse_digest(text) if text else []
        marked = sum(1 for it in items if it["verdict"])
        return {
            "today": date.today().isoformat(),
            "digest_exists": bool(text),
            "items": len(items),
            "marked": marked,
            "run": RUN.snapshot(),
            "profile_exists": Path(resolve(cfg["profile"]["cache_path"])).exists(),
            "sources": [s.get("type") for s in cfg.get("sources", [])],
            "demo_label": cfg.get("demo_label", ""),
            "model": model_status(cfg),
            "exploration_ratio": cfg["digest"].get("exploration_ratio", 0.7),
        }

    def api_digest(self, cfg, q):
        want = q.get("date", [""])[0]
        day = want if _DATE_RE.match(want) else date.today().isoformat()
        p = Path(resolve(cfg["digest"]["output_dir"])) / f"{day}.md"
        if not p.exists():
            return {"date": day, "exists": False, "text": "", "items": []}
        text = p.read_text(encoding="utf-8")
        return {"date": day, "exists": True, "text": text, "items": parse_digest(text)}

    def api_dates(self, cfg, q):
        out_dir = Path(resolve(cfg["digest"]["output_dir"]))
        days = sorted((f.stem for f in out_dir.glob("*.md") if _DATE_RE.match(f.stem)),
                      reverse=True) if out_dir.exists() else []
        return {"dates": days}

    def api_feedback(self, cfg, q):
        """body: {date, link, verdict: pos|neg|null} → 写回简报的 反馈:: 行。"""
        b = self._body()
        ok = False
        if b.get("date") and b.get("link"):
            v = b.get("verdict")
            ok = set_verdict(cfg, b["date"], b["link"],
                             v if v in ("pos", "neg") else None)
        return {"ok": ok}

    def api_run(self, cfg, q):
        """body: {refresh_profile?, feedback_only?} → 后台跑一轮，进度走 /api/status 轮询。"""
        b = self._body()
        try:
            run_async(cfg, refresh_profile=bool(b.get("refresh_profile")),
                      feedback_only=bool(b.get("feedback_only")))
        except RuntimeError as e:
            return self._json({"ok": False, "error": str(e)}, 409)
        return {"ok": True}

    ROUTES = {
        "/api/status": api_status,
        "/api/digest": api_digest,
        "/api/dates": api_dates,
        "/api/run": api_run,
        "/api/feedback": api_feedback,
    }


def serve(cfg, host="127.0.0.1", port=7781, open_browser=True):
    import threading
    import webbrowser
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(Handler, BaseHTTPRequestHandler):
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            fn = Handler.ROUTES.get(u.path)
            if fn:
                try:
                    return self._json(fn(self, cfg, q))
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
            return self._page()

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            fn = Handler.ROUTES.get(u.path)
            if fn and u.path in ("/api/run", "/api/feedback"):
                try:
                    return self._json(fn(self, cfg, {}))
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 500)
            self.send_error(404)

        def _page(self):
            body = webapp.INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):                 # 静默默认访问日志
            pass

    srv = ThreadingHTTPServer((host, port), H)
    url = f"http://{host}:{port}/"
    print(f"信息流 Web 界面：{url}（Ctrl+C 停止）")
    if open_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()   # 等端口起来再开
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n再见。")

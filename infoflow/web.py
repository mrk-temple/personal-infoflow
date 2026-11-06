"""Local, same-origin reader; Markdown remains the feedback source of truth."""
import copy
import json
import threading
import urllib.parse
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import webapp
from .activity import load_activity, record_activity
from .capture import load_captures
from .client import model_status
from .config import resolve
from .feedback import collect_feedback, load_state, set_verdict
from .items import parse_digest, valid_date
from .settings import public_settings, save_settings
from .storage import LOCK


class RunState:
    def __init__(self):
        self._lock = threading.Lock()
        self.lines, self.running = [], False
        self.error, self.done, self.result = None, False, None

    def try_start(self):
        with self._lock:
            if self.running:
                return False
            self.lines, self.running = [], True
            self.error, self.done, self.result = None, False, None
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
            return {"running": self.running, "done": self.done, "error": self.error,
                    "lines": list(self.lines), "result": self.result}


RUN = RunState()


def run_async(cfg, refresh_profile=False, feedback_only=False, language=None, portrait=False):
    run_cfg = copy.deepcopy(cfg)
    if language in {"en", "zh-CN"}:
        run_cfg["language"] = language

    def work():
        from .client import get_client
        from .pipeline import run
        try:
            client = None if feedback_only else get_client(run_cfg)
            result = run(run_cfg, client, refresh_profile=refresh_profile,
                         feedback_only=feedback_only, portrait=portrait, log=RUN.log)
            RUN.finish(result=result)
        except BaseException as exc:
            RUN.finish(error=f"{type(exc).__name__}: {exc}")

    if not RUN.try_start():
        raise RuntimeError("A run is already in progress")
    threading.Thread(target=work, daemon=True).start()


def today_digest_path(cfg):
    return Path(resolve(cfg["digest"]["output_dir"])) / f"{date.today().isoformat()}.md"


class ApiError(ValueError):
    def __init__(self, code, status=400):
        self.code, self.status = code, status
        super().__init__(code)


class Handler:
    def _json(self, obj, status=200):
        self._send(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def _send(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ApiError("invalid_json") from None
        if not 0 <= length <= 65536:
            raise ApiError("body_too_large", 413)
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise ValueError()
            return body
        except (ValueError, UnicodeError):
            raise ApiError("invalid_json") from None

    def _items(self, cfg, day):
        path = Path(resolve(cfg["digest"]["output_dir"])) / f"{day}.md"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        activity = load_activity(cfg)
        items = []
        for item in parse_digest(text):
            saved = activity.get(f"{day}\t{item['link']}", {})
            items.append({**item, "date": day, "read": saved.get("read", False), "saved": saved.get("saved", False)})
        return text, items

    def api_status(self, cfg, q):
        text, items = self._items(cfg, date.today().isoformat())
        state = load_state(cfg)
        return {"today": date.today().isoformat(), "digest_exists": bool(text), "items": len(items),
                "marked": sum(bool(it["verdict"]) for it in items), "run": RUN.snapshot(),
                "profile_exists": Path(resolve(cfg["profile"]["cache_path"])).exists(),
                "sources": [s.get("type") for s in cfg.get("sources", [])],
                "demo_label": cfg.get("demo_label", ""), "model": model_status(cfg),
                "language": cfg.get("language", "zh-CN"),
                "implicit_feedback": cfg.get("reading", {}).get("implicit_feedback", False),
                "exploration_ratio": (state.get("adaptive_ratio", cfg["digest"].get("exploration_ratio", .7))
                                      if state.get("base_ratio") == cfg["digest"].get("exploration_ratio", .7)
                                      else cfg["digest"].get("exploration_ratio", .7)),
                "quality": state.get("quality", {}),
                "saved": sum(bool(e.get("saved")) for e in load_activity(cfg).values())}

    def api_digest(self, cfg, q):
        want = q.get("date", [""])[0]
        if want and not valid_date(want):
            raise ApiError("invalid_date")
        day = want or date.today().isoformat()
        text, items = self._items(cfg, day)
        return {"date": day, "exists": bool(text), "text": text, "items": items}

    def api_dates(self, cfg, q):
        out = Path(resolve(cfg["digest"]["output_dir"]))
        return {"dates": sorted((p.stem for p in out.glob("*.md") if valid_date(p.stem)), reverse=True)}

    def api_saved(self, cfg, q):
        editions, saved = {}, []
        for e in reversed(list(load_activity(cfg).values())):
            if not e.get("saved"):
                continue
            day = e["date"]
            if day not in editions:
                editions[day] = {it["link"]: it for it in self._items(cfg, day)[1]}
            saved.append(editions[day].get(e["link"], {**e, "verdict": None, "score": "", "reason": "",
                                                     "dup_count": 1, "enriched": False}))
        return {"items": saved}

    def api_profile(self, cfg, q):
        path = Path(resolve(cfg["profile"]["cache_path"]))
        base = Path(resolve(cfg["portrait"]["output_path"]))
        images = sorted((p for p in base.parent.glob(f"{base.stem}-*.png") if p.is_file() and not p.is_symlink()),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        return {"text": path.read_text(encoding="utf-8") if path.exists() else "",
                "image_url": "/api/portrait-image?name=" + urllib.parse.quote(images[0].name) if images else None,
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else None,
                "captures": len(load_captures(cfg)["items"]),
                "half_life_days": cfg.get("feedback", {}).get("half_life_days", 0),
                "implicit_feedback": cfg.get("reading", {}).get("implicit_feedback", False)}

    def api_settings(self, cfg, q):
        return public_settings(cfg)

    def api_save_settings(self, cfg, q):
        if RUN.snapshot()["running"]:
            raise ApiError("already_running", 409)
        try:
            result = save_settings(cfg, self._body())
            return {"ok": True, "settings": result}
        except ValueError:
            raise ApiError("invalid_settings") from None

    def _target(self, cfg, body):
        day, link = body.get("date"), body.get("link")
        if not valid_date(day) or not isinstance(link, str):
            raise ApiError("invalid_item")
        item = next((it for it in self._items(cfg, day)[1] if it["link"] == link), None)
        if item is None:
            raise ApiError("item_not_found", 404)
        return day, item

    def api_feedback(self, cfg, q):
        body = self._body()
        if "verdict" not in body or body["verdict"] not in ("pos", "neg", None):
            raise ApiError("invalid_verdict")
        with LOCK:
            day, item = self._target(cfg, body)
            ok = set_verdict(cfg, day, item["link"], body["verdict"])
            state = collect_feedback(cfg) if ok else {}
        return {"ok": ok, "feedback": state}

    def api_activity(self, cfg, q):
        body = self._body()
        with LOCK:
            day, item = self._target(cfg, body)
            if body.get("event") == "dwell" and not cfg.get("reading", {}).get("implicit_feedback", False):
                raise ApiError("implicit_disabled", 403)
            try:
                entry = record_activity(cfg, day, item, body.get("event"), body.get("value"))
            except ValueError:
                raise ApiError("invalid_event") from None
            if cfg.get("reading", {}).get("implicit_feedback", False):
                collect_feedback(cfg)
        return {"ok": True, "activity": entry}

    def api_run(self, cfg, q):
        body = self._body()
        language = body.get("language", cfg.get("language", "zh-CN"))
        if language not in {"en", "zh-CN"}:
            raise ApiError("invalid_language")
        try:
            run_async(cfg, bool(body.get("refresh_profile")), bool(body.get("feedback_only")), language,
                      portrait=bool(body.get("portrait")))
        except RuntimeError:
            raise ApiError("already_running", 409) from None
        return {"ok": True}

    ROUTES = {"/api/status": api_status, "/api/digest": api_digest, "/api/dates": api_dates,
              "/api/saved": api_saved, "/api/profile": api_profile, "/api/settings": api_settings}
    WRITES = {"/api/run": api_run, "/api/feedback": api_feedback, "/api/activity": api_activity,
              "/api/settings": api_save_settings}


def make_server(cfg, host="127.0.0.1", port=7781):
    class H(Handler, BaseHTTPRequestHandler):
        def _guard(self):
            host_header = self.headers.get("Host", "")
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}",
                       f"{host}:{self.server.server_port}"}
            origin = self.headers.get("Origin")
            if host_header not in allowed or (origin and origin != f"http://{host_header}") \
                    or self.headers.get("Sec-Fetch-Site") == "cross-site":
                raise ApiError("origin_rejected", 403)

        def _dispatch(self, write=False):
            try:
                self._guard()
                url = urllib.parse.urlsplit(self.path)
                if not write and url.path == "/api/portrait-image":
                    name = urllib.parse.parse_qs(url.query).get("name", [""])[0]
                    base = Path(resolve(cfg["portrait"]["output_path"]))
                    image = base.parent / name
                    if not name or Path(name).name != name or not name.startswith(base.stem + "-") \
                            or image.suffix != ".png" or image.is_symlink() or not image.is_file() \
                            or image.resolve().parent != base.parent.resolve() or image.stat().st_size > 25 * 1024 * 1024:
                        raise ApiError("not_found", 404)
                    return self._send(image.read_bytes(), "image/png")
                fn = (Handler.WRITES if write else Handler.ROUTES).get(url.path)
                if fn:
                    return self._json(fn(self, cfg, urllib.parse.parse_qs(url.query)))
                assets = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8")}
                assets["/settings.js"] = ("settings.js", "text/javascript; charset=utf-8")
                if not write and url.path in assets:
                    name, content_type = assets[url.path]
                    return self._send(webapp.asset(name), content_type)
                raise ApiError("not_found", 404)
            except ApiError as exc:
                return self._json({"ok": False, "error": exc.code}, exc.status)
            except Exception:
                return self._json({"ok": False, "error": "server_error"}, 500)

        def do_GET(self):
            self._dispatch()

        def do_POST(self):
            self._dispatch(write=True)

        def log_message(self, fmt, *args):
            pass

    return ThreadingHTTPServer((host, port), H)


def serve(cfg, host="127.0.0.1", port=7781, open_browser=True):
    import webbrowser
    srv = make_server(cfg, host, port)
    print(f"Personal InfoFlow: http://{host}:{srv.server_port}/ (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(.8, webbrowser.open, args=(f"http://{host}:{srv.server_port}/",)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()

import copy
import json
import threading
import urllib.error
import urllib.request

import pytest

from infoflow.config import DEFAULTS
from infoflow.web import make_server


@pytest.fixture
def server(tmp_path):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["digest"]["output_dir"] = str(tmp_path / "digests")
    cfg["profile"]["cache_path"] = str(tmp_path / "profile.md")
    cfg["portrait"]["output_path"] = str(tmp_path / "portrait.png")
    cfg["sources"] = [{"type": "hackernews", "limit": 10}]
    cfg["state"] = {k: str(tmp_path / f"{k}.json") for k in cfg["state"]}
    (tmp_path / "digests").mkdir()
    (tmp_path / "digests" / "2026-11-06.md").write_text(
        "# Daily Flow\n## [Research](https://example.com/a)\n**80** · Explore · Test 📄\n\n> Worth reading\n\nFeedback::\n",
        encoding="utf-8")
    srv = make_server(cfg, port=0)
    worker = threading.Thread(target=srv.serve_forever, daemon=True)
    worker.start()
    yield f"http://127.0.0.1:{srv.server_port}", cfg
    srv.shutdown()
    srv.server_close()
    worker.join(2)


def request(base, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=3) as r:
        return r.read(), r.headers


def test_feedback_edits_and_clear_work_over_real_http(server):
    base, cfg = server
    for value, count in (("pos", {"pos": 1, "neg": 0}), ("neg", {"pos": 0, "neg": 1}),
                         (None, {"pos": 0, "neg": 0})):
        raw, _ = request(base, "/api/feedback", {"date": "2026-11-06", "link": "https://example.com/a", "verdict": value})
        assert json.loads(raw)["feedback"]["quality"]["counts"] == count
    raw, _ = request(base, "/api/digest?date=2026-11-06")
    assert json.loads(raw)["items"][0]["verdict"] is None


def test_read_later_persists_across_editions(server):
    base, _ = server
    request(base, "/api/activity", {"date": "2026-11-06", "link": "https://example.com/a", "event": "save", "value": True})
    raw, _ = request(base, "/api/saved")
    assert json.loads(raw)["items"][0]["saved"]
    request(base, "/api/activity", {"date": "2026-11-06", "link": "https://example.com/a", "event": "save", "value": False})
    assert json.loads(request(base, "/api/saved")[0])["items"] == []


@pytest.mark.parametrize("path,body", [("/api/feedback", {"date": "../../outside", "link": "x", "verdict": "pos"}),
    ("/api/feedback", {"date": "2026-11-06", "link": "https://example.com/a", "verdict": "unknown"}),
    ("/api/activity", {"date": "2026-11-06", "link": "https://example.com/a", "event": "dwell", "value": 30})])
def test_invalid_requests_and_disabled_dwell_rejected(server, path, body):
    with pytest.raises(urllib.error.HTTPError) as exc:
        request(server[0], path, body)
    assert exc.value.code in (400, 403)


def test_get_cannot_run_pipeline_and_cross_origin_post_is_rejected(server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        request(server[0], "/api/run")
    assert exc.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as exc:
        request(server[0], "/api/feedback", {}, {"Origin": "https://untrusted.example"})
    assert exc.value.code == 403


def test_packaged_bilingual_assets_and_privacy_headers(server):
    raw, headers = request(server[0], "/")
    assert b'/app.js' in raw and b'/styles.css' in raw
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert b"Save for later" in request(server[0], "/app.js")[0]
    with pytest.raises(urllib.error.HTTPError):
        request(server[0], "/config.yaml")


def test_settings_survive_new_server_and_history_includes_all_dates(server, tmp_path):
    base, cfg = server
    original = copy.deepcopy(cfg)
    (tmp_path / "digests" / "2026-11-05.md").write_text("# Earlier edition", encoding="utf-8")
    request(base, "/api/settings", {"models": {"provider": "codex"},
                                  "digest": {"max_items": 8, "exploration_ratio": .5}})
    raw, _ = request(base, "/api/dates")
    assert json.loads(raw)["dates"] == ["2026-11-06", "2026-11-05"]
    assert json.loads(request(base, "/api/digest?date=2026-11-05")[0])["text"] == "# Earlier edition"
    from infoflow.settings import load_saved_settings
    restarted = make_server(load_saved_settings(original), port=0)
    worker = threading.Thread(target=restarted.serve_forever, daemon=True)
    worker.start()
    try:
        new_base = f"http://127.0.0.1:{restarted.server_port}"
        assert json.loads(request(new_base, "/api/settings")[0])["digest"]["max_items"] == 8
        assert json.loads(request(new_base, "/api/dates")[0])["dates"] == ["2026-11-06", "2026-11-05"]
    finally:
        restarted.shutdown()
        restarted.server_close()
        worker.join(2)
    assert (tmp_path / "digests" / "2026-11-05.md").read_text(encoding="utf-8") == "# Earlier edition"


def test_portrait_route_does_not_serve_arbitrary_local_files(server):
    for value in ("../config.yaml", "portrait.txt", "../../portrait-a.png"):
        with pytest.raises(urllib.error.HTTPError) as exc:
            request(server[0], "/api/portrait-image?name=" + value)
        assert exc.value.code == 404

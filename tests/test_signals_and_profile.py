import copy
import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from infoflow.activity import implicit_signals, load_activity, record_activity
from infoflow.capture import CaptureError, add_capture, capture_context, load_captures, sync_telegram
from infoflow.config import DEFAULTS
from infoflow.feedback import _aggregate
from infoflow.profile import collect_notes, load_profile
from infoflow.storage import decay_weight, read_json


@pytest.fixture
def cfg(tmp_path):
    config = copy.deepcopy(DEFAULTS)
    config["state"] = {key: str(tmp_path / key / "state.json") for key in config["state"]}
    config["profile"]["cache_path"] = str(tmp_path / "profile.md")
    config["reading"]["implicit_feedback"] = True
    config["telegram"]["allowed_chat_ids"] = [123]
    return config


ITEM = {"title": "Transformer research", "link": "https://example.com/a", "source": "Test", "bucket": "rel"}


def test_local_activity_is_reversible_and_open_is_not_a_read(cfg):
    record_activity(cfg, "2026-11-06", ITEM, "open")
    assert not next(iter(load_activity(cfg).values()))["read"]
    record_activity(cfg, "2026-11-06", ITEM, "save", True)
    assert len(implicit_signals(cfg)) == 1
    record_activity(cfg, "2026-11-06", ITEM, "save", False)
    assert implicit_signals(cfg) == []
    record_activity(cfg, "2026-11-06", ITEM, "read", True)
    assert implicit_signals(cfg) == []


def test_dwell_retries_are_idempotent_and_explicit_dislike_wins(cfg):
    for seconds in (30, 30, 20, 60):
        record_activity(cfg, "2026-11-06", ITEM, "dwell", seconds)
    assert next(iter(load_activity(cfg).values()))["dwell_seconds"] == 60
    explicit = [{**ITEM, "date": "2026-11-06", "verdict": -1}]
    assert implicit_signals(cfg, explicit) == []
    state = _aggregate(cfg, explicit)
    assert state["source_bias"]["Test"] < 0
    assert state["quality"]["counts"] == {"pos": 0, "neg": 1}
    cfg["reading"]["implicit_feedback"] = False
    assert implicit_signals(cfg) == []


@pytest.mark.parametrize("seconds", [-1, float("nan"), float("inf"), True, "30"])
def test_invalid_dwell_rejected(cfg, seconds):
    with pytest.raises(ValueError):
        record_activity(cfg, "2026-11-06", ITEM, "dwell", seconds)


def test_time_decay_has_measurable_half_life():
    now = datetime.now(timezone.utc)
    assert decay_weight((now - timedelta(days=30)).isoformat(), 30, now) == pytest.approx(.5)
    assert decay_weight("invalid", 30, now) == 0
    assert decay_weight((now + timedelta(days=1)).isoformat(), 30, now) == 1


def test_manual_capture_deduplicates_and_enters_profile_context(cfg):
    assert add_capture(cfg, "Read about ecology https://example.com/ecology")
    assert not add_capture(cfg, "Read about ecology https://example.com/ecology")
    assert "ecology" in capture_context(cfg)
    assert load_captures(cfg)["items"][0]["links"] == ["https://example.com/ecology"]


def test_telegram_allowlist_offsets_edits_and_retry(cfg, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    updates = [{"update_id": 1, "message": {"message_id": 1, "chat": {"id": 123},
                 "date": int(time.time()), "text": "Saved paper https://example.com/a"}},
               {"update_id": 2, "message": {"message_id": 2, "chat": {"id": 456}, "text": "Private outsider"}}]
    requests = []

    def reply(url, payload, **kwargs):
        requests.append(payload)
        return {"ok": True, "result": updates}

    monkeypatch.setattr("infoflow.capture.http.post_json", reply)
    assert sync_telegram(cfg)["received"] == 1
    assert sync_telegram(cfg)["received"] == 0
    assert requests[1]["offset"] == 3
    updates[:] = [{"update_id": 3, "edited_message": {**updates[0]["message"], "text": "Edited paper"}}]
    assert sync_telegram(cfg)["received"] == 1
    state = load_captures(cfg)
    assert len(state["items"]) == 1 and state["items"][0]["text"] == "Edited paper"
    assert state["offset"] == 4


def test_telegram_refuses_unconfigured_allowlist_and_redacts_failure(cfg, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "never-echo-this-token")
    def fail(*args, **kwargs):
        raise OSError("https://api.telegram.org/botnever-echo-this-token/getUpdates")
    monkeypatch.setattr("infoflow.capture.http.post_json", fail)
    with pytest.raises(CaptureError) as exc:
        sync_telegram(cfg)
    assert "never-echo" not in str(exc.value)
    assert not os.path.exists(cfg["state"]["captures_path"])
    cfg["telegram"]["allowed_chat_ids"] = []
    with pytest.raises(CaptureError, match="allowed_chat_ids"):
        sync_telegram(cfg)


def test_profile_excludes_generated_digest_and_truncates_large_notes(tmp_path):
    (tmp_path / "notes.md").write_text("Useful notes " * 1000, encoding="utf-8")
    generated = tmp_path / "digests"
    generated.mkdir()
    (generated / "2026-11-06.md").write_text("SHOULD NOT BECOME AN INTEREST", encoding="utf-8")
    text, count = collect_notes(str(tmp_path), 200, [], [str(generated)])
    assert count == 1 and len(text) == 200
    assert "Useful notes" in text and "SHOULD NOT" not in text


def test_live_capture_layer_updates_without_rebuilding_cached_profile(cfg, tmp_path):
    path = tmp_path / "profile.md"
    path.write_text("Stable knowledge", encoding="utf-8")
    assert load_profile(None, cfg) == "Stable knowledge"
    add_capture(cfg, "New current project: ecology experiments")
    assert "ecology experiments" in load_profile(None, cfg)
    assert path.read_text(encoding="utf-8") == "Stable knowledge"


def test_corrupt_state_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        read_json(path, {})
    assert path.read_text(encoding="utf-8") == "{broken"

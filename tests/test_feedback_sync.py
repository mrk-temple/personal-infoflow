import json

import pytest

from infoflow.feedback import collect_feedback, set_verdict


def digest(mark="好", title="Transformer research", link="https://example.com/a"):
    return f"## [{title}]({link})\n**80** · Hacker News\n\n> A useful paper\n\n反馈:: {mark}\n"


@pytest.fixture
def env(tmp_path):
    out = tmp_path / "digests"
    out.mkdir()
    path = out / "2026-11-06.md"
    path.write_text(digest(), encoding="utf-8")
    cfg = {"digest": {"output_dir": str(out)}, "state": {
        "feedback_log": str(tmp_path / "logs" / "feedback.json"),
        "feedback_state": str(tmp_path / "state" / "feedback.json"),
    }}
    return cfg, path


def test_edited_and_cleared_feedback_replaces_all_learned_bias(env):
    cfg, path = env
    first = collect_feedback(cfg)
    assert first["new"] == 1
    assert first["source_bias"]["Hacker News"] == 6
    path.write_text(digest("差"), encoding="utf-8")
    changed = collect_feedback(cfg)
    assert changed["updated"] == 1 and changed["new"] == 0
    assert changed["source_bias"]["Hacker News"] == -6
    assert changed["keyword_bias"]["transformer"] == -3
    assert changed["liked"] == []
    assert changed["quality"]["counts"] == {"pos": 0, "neg": 1}
    path.write_text(digest(""), encoding="utf-8")
    cleared = collect_feedback(cfg)
    assert cleared["removed"] == 1
    assert cleared["source_bias"] == cleared["keyword_bias"] == {}
    assert cleared["liked"] == cleared["disliked"] == []
    assert json.loads(open(cfg["state"]["feedback_log"], encoding="utf-8").read()) == []


def test_sync_is_idempotent_and_keeps_archived_dates(env):
    cfg, path = env
    collect_feedback(cfg)
    assert collect_feedback(cfg)["changed"] == 0
    path.rename(path.with_suffix(".archive"))
    assert collect_feedback(cfg)["quality"]["counts"]["pos"] == 1


def test_legacy_duplicates_and_removed_items_are_reconciled(env):
    cfg, path = env
    collect_feedback(cfg)
    log_path = cfg["state"]["feedback_log"]
    records = json.loads(open(log_path, encoding="utf-8").read())
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records * 2, f)
    collect_feedback(cfg)
    assert len(json.loads(open(log_path, encoding="utf-8").read())) == 1
    path.write_text("# Empty edition\n", encoding="utf-8")
    assert collect_feedback(cfg)["removed"] == 1


def test_set_verdict_handles_long_items_and_missing_feedback(env):
    cfg, path = env
    path.write_text(digest().replace("反馈:: 好", "\n" * 20 + "反馈:: 好"), encoding="utf-8")
    assert set_verdict(cfg, path.stem, "https://example.com/a", "neg")
    assert "反馈:: 差" in path.read_text(encoding="utf-8")
    path.write_text(digest().replace("反馈:: 好", ""), encoding="utf-8")
    assert set_verdict(cfg, path.stem, "https://example.com/a", "pos")
    assert "反馈:: 好" in path.read_text(encoding="utf-8")


def test_invalid_dates_cannot_escape_digest_directory(env):
    cfg, _ = env
    assert not set_verdict(cfg, "../../outside", "https://example.com/a", "pos")
    assert not set_verdict(cfg, "2026-99-99", "https://example.com/a", "pos")


def test_new_rating_on_old_edition_decays_from_rating_time_and_does_not_refresh_on_scan(env):
    cfg, path = env
    cfg["feedback"] = {"half_life_days": 30}
    old = path.with_name("2020-01-01.md")
    path.rename(old)
    first = collect_feedback(cfg)
    assert first["source_bias"]["Hacker News"] >= 5.9
    records = json.loads(open(cfg["state"]["feedback_log"], encoding="utf-8").read())
    stamp = records[0]["updated_at"]
    assert collect_feedback(cfg)["changed"] == 0
    assert json.loads(open(cfg["state"]["feedback_log"], encoding="utf-8").read())[0]["updated_at"] == stamp

import copy
import json

import pytest

from infoflow.config import DEFAULTS
from infoflow.items import parse_digest
from infoflow.pipeline import run
from infoflow.rank import rank_items


def config(tmp_path):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["models"] = {"rank": "test", "profile": "test"}
    cfg["digest"].update(output_dir=str(tmp_path / "out"), max_items=1)
    cfg["state"] = {k: str(tmp_path / f"{k}.json") for k in cfg["state"]}
    return cfg


def item(n):
    return {"title": f"Research {n}", "link": f"https://example.com/{n}", "summary": "", "source": "Test",
            "relevance": 80, "exploration": 90, "score": 85, "reason": "Useful"}


def test_only_published_candidates_become_seen(tmp_path, monkeypatch):
    cfg = config(tmp_path)
    cfg["cluster"]["enabled"] = False
    monkeypatch.setattr("infoflow.pipeline.load_profile", lambda *a, **kw: "Profile")
    monkeypatch.setattr("infoflow.pipeline.fetch_items", lambda *a, **kw: [item(1), item(2), item(3)])
    monkeypatch.setattr("infoflow.pipeline.rank_items", lambda *a, **kw: [item(1), item(2), item(3)])
    result = run(cfg, None, log=lambda msg: None)
    assert result["picked"] == 1
    seen = json.loads(open(cfg["state"]["seen_path"], encoding="utf-8").read())
    assert len(seen) == 1


@pytest.mark.parametrize("reply", ['not json', '{"items": []}', '{"items":[{"id":0,"relevance":"bad","exploration":90}]}'])
def test_invalid_model_output_fails_instead_of_silently_losing_candidates(tmp_path, monkeypatch, reply):
    monkeypatch.setattr("infoflow.rank.chat", lambda *a, **kw: reply)
    with pytest.raises(ValueError, match="No items were marked seen"):
        rank_items(None, config(tmp_path), "Profile", [item(1)])


def test_english_digest_round_trips_feedback_and_source(tmp_path):
    from infoflow.digest import write_digest
    cfg = config(tmp_path)
    cfg["language"] = "en"
    path, _ = write_digest(cfg, [item(1)])
    text = path.read_text(encoding="utf-8")
    assert "Feedback::" in text and "Edition:" in text
    parsed = parse_digest(text.replace("Feedback:: ", "Feedback:: bad"))
    assert parsed[0]["verdict"] == "neg" and parsed[0]["source"] == "Test"

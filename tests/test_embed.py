import sys
from types import SimpleNamespace

from infoflow import embed


def test_model_cache_stays_in_configured_workspace_and_changes_with_it(tmp_path, monkeypatch):
    calls = []
    class FakeModel:
        def __init__(self, **kwargs):
            calls.append(kwargs)
        def embed(self, texts):
            return [[1, 0] for text in texts]
    monkeypatch.setitem(sys.modules, "fastembed", SimpleNamespace(TextEmbedding=FakeModel))
    monkeypatch.setattr(embed, "_MODEL", None)
    first = {"embedding": {"model": "test", "model_cache_path": str(tmp_path / "one")}}
    second = {"embedding": {"model": "test", "model_cache_path": str(tmp_path / "two")}}
    assert embed._fastembed(first, ["text"]) == [[1., 0.]]
    embed._fastembed(first, ["another"])
    embed._fastembed(second, ["text"])
    assert [c["cache_dir"] for c in calls] == [str(tmp_path / "one"), str(tmp_path / "two")]

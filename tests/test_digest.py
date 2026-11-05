import copy

from infoflow.config import DEFAULTS
from infoflow.digest import write_digest


def _cfg(tmp_path):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["digest"].update({
        "output_dir": str(tmp_path / "out"),
        "max_items": 4,
        "max_per_source": 0,
        "exploration_ratio": 0.5,
        "min_score": 0,
    })
    # state 指向空目录 → load_adaptive_ratio 返回 None，回退到 exploration_ratio
    cfg["state"] = {"feedback_state": str(tmp_path / "fb_state.json")}
    return cfg


def _item(link, rel, exp, score, source="S"):
    return {"title": link, "link": link, "source": source,
            "relevance": rel, "exploration": exp, "score": score, "reason": "r"}


def test_writes_file_and_picks_split(tmp_path):
    cfg = _cfg(tmp_path)
    ranked = [
        _item("a", 90, 10, 90),
        _item("b", 80, 20, 80),
        _item("c", 10, 95, 70),
        _item("d", 5, 90, 60),
        _item("e", 1, 1, 5),
    ]
    path, n = write_digest(cfg, ranked)
    assert path.exists()
    assert n == 4  # max_items
    text = path.read_text(encoding="utf-8")
    # 高相关的进了贴合位，高拓展的进了拓展位
    assert "](a)" in text or "(a)" in text
    assert "反馈::" in text
    assert "拓展比例 0.5" in text


def test_append_on_second_run(tmp_path):
    cfg = _cfg(tmp_path)
    ranked = [_item("a", 90, 10, 90), _item("c", 10, 95, 70)]
    p1, _ = write_digest(cfg, ranked)
    first = p1.read_text(encoding="utf-8")
    p2, _ = write_digest(cfg, ranked)
    second = p2.read_text(encoding="utf-8")
    assert p1 == p2
    assert len(second) > len(first)
    assert "追加" in second

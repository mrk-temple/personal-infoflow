import pytest

from infoflow.config import ConfigError, _deep_merge, load_config


def _write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_deep_merge_recurses():
    base = {"a": {"x": 1, "y": 2}, "b": 1}
    out = _deep_merge(base, {"a": {"y": 9}, "c": 3})
    assert out == {"a": {"x": 1, "y": 9}, "b": 1, "c": 3}
    assert base["a"]["y"] == 2  # 不改原始


def test_defaults_filled(tmp_path):
    cfg = load_config(_write(tmp_path, """
models: {profile: p, rank: r}
digest: {output_dir: /tmp/out}
sources: [{type: hackernews}]
"""))
    # 用户没写的回退到默认
    assert cfg["fetch"]["days"] == 10
    assert cfg["embedding"]["enabled"] is False
    assert cfg["digest"]["max_items"] == 10


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(str(tmp_path / "nope.yaml"))


def test_missing_required_keys(tmp_path):
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, "models: {profile: p, rank: r}\n"))  # 无 sources/output_dir

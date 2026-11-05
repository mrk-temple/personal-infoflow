import threading

import pytest

from infoflow import web

# ---- parse_digest：简报 markdown → 结构化条目 ----

SAMPLE = """# 信息简报 2026-06-16

## [Cool AI paper](https://example.com/a)
**80** · Hacker News

> 一句理由

反馈:: 好

## [Boring listicle](https://example.com/b)
**40** · 拓展 · r/programming

> 另一句

反馈:: 差

## [No verdict yet](https://example.com/c)
**60** · arXiv cs.AI

> 还没标

反馈::
"""


def test_parse_digest_items():
    items = web.parse_digest(SAMPLE)
    assert len(items) == 3
    a, b, c = items
    assert (a["link"], a["verdict"], a["bucket"], a["source"]) == \
        ("https://example.com/a", "pos", "rel", "Hacker News")
    assert (b["verdict"], b["bucket"], b["source"]) == ("neg", "explore", "r/programming")
    assert c["verdict"] is None and c["score"] == "60"
    assert all(it["reason"] for it in items)


def test_parse_digest_dup_count_and_empty():
    text = SAMPLE.replace("**80** · Hacker News",
                          "**80** · Hacker News · 也被 3 个其他源报道")
    a = web.parse_digest(text)[0]
    assert a["dup_count"] == 4          # 自身 + 3 个其他源
    assert web.parse_digest("") == []


def test_parse_digest_enriched_flag():
    text = SAMPLE.replace("**40** · 拓展 · r/programming",
                          "**40** · 拓展 · r/programming · 📄")
    assert web.parse_digest(text)[1]["enriched"] is True
    assert web.parse_digest(SAMPLE)[0]["enriched"] is False


# ---- set_verdict：写回 markdown（Web 与 Obsidian 同一份事实源）----

@pytest.fixture
def digest_env(tmp_path, monkeypatch):
    """隔离环境：输出目录指向 tmp，state 路径无所谓（set_verdict 不读它）。"""
    out = tmp_path / "vault" / "简报"
    out.mkdir(parents=True)
    p = out / "2026-06-16.md"
    p.write_text(SAMPLE, encoding="utf-8")
    cfg = {"digest": {"output_dir": str(out)}}
    yield cfg, p


def test_set_verdict_marks_and_unmarks(digest_env):
    cfg, p = digest_env
    assert web.set_verdict(cfg, "2026-06-16", "https://example.com/a", "pos")
    assert "反馈:: 好\n" in p.read_text(encoding="utf-8")
    # 再标差 → 覆盖
    assert web.set_verdict(cfg, "2026-06-16", "https://example.com/a", "neg")
    text = p.read_text(encoding="utf-8")
    assert "反馈:: 差\n" in text and "反馈:: 好" not in text
    # 清除
    assert web.set_verdict(cfg, "2026-06-16", "https://example.com/a", None)
    assert "反馈::\n" in p.read_text(encoding="utf-8")


def test_set_verdict_only_touches_target_item(digest_env):
    cfg, p = digest_env
    before = p.read_text(encoding="utf-8")
    assert web.set_verdict(cfg, "2026-06-16", "https://example.com/c", "pos")
    after = p.read_text(encoding="utf-8")
    # 只有第三条的 反馈:: 变了
    assert after.splitlines()[-1].strip() == "反馈:: 好"
    for l1, l2 in zip(before.splitlines()[:-1], after.splitlines()[:-1]):
        assert l1 == l2


def test_set_verdict_unknown_link_or_date(digest_env, tmp_path):
    cfg, _ = digest_env
    assert not web.set_verdict(cfg, "2026-06-16", "https://nope", "pos")
    assert not web.set_verdict(cfg, "1999-01-01", "https://example.com/a", "pos")


# ---- RunState：进度快照与并发保护 ----

def test_runstate_lifecycle():
    rs = web.RunState()
    assert rs.try_start()
    rs.log("· 抓取 ...")
    snap = rs.snapshot()
    assert snap["running"] and snap["lines"] == ["· 抓取 ..."] and not snap["done"]
    rs.finish(result={"picked": 3})
    snap = rs.snapshot()
    assert not snap["running"] and snap["done"] and snap["result"]["picked"] == 3
    # 结束后可再开新一轮
    assert rs.try_start()
    rs.finish(error="boom")
    assert rs.snapshot()["error"] == "boom"


def test_feedback_only_works_without_model_credentials(monkeypatch, tmp_path):
    import json
    import time
    out = tmp_path / "digests"
    out.mkdir()
    (out / "2026-06-16.md").write_text(SAMPLE, encoding="utf-8")
    state = tmp_path / "feedback-state.json"
    cfg = {"digest": {"output_dir": str(out)}, "state": {
        "feedback_log": str(tmp_path / "feedback-log.json"),
        "feedback_state": str(state)}, "feedback": {}}
    rs = web.RunState()
    monkeypatch.setattr(web, "RUN", rs)

    def unavailable_client():
        raise AssertionError("本地反馈不应创建模型客户端")

    monkeypatch.setattr("infoflow.client.get_client", unavailable_client)
    web.run_async(cfg, feedback_only=True)
    deadline = time.monotonic() + 5
    while not rs.snapshot()["done"] and time.monotonic() < deadline:
        threading.Event().wait(.01)
    snap = rs.snapshot()
    assert snap["done"] and snap["error"] is None
    assert snap["result"]["feedback"]["new"] == 2
    assert json.loads(state.read_text(encoding="utf-8"))["quality"]["counts"] == {"pos": 1, "neg": 1}


def test_run_async_rejects_concurrent_runs(monkeypatch, tmp_path):
    cfg = {"digest": {"output_dir": str(tmp_path)}}
    started = threading.Event()
    release = threading.Event()

    def fake_run(*a, **k):
        started.set()
        release.wait(5)
        return {"picked": 0}

    monkeypatch.setattr("infoflow.pipeline.run", fake_run)
    monkeypatch.setattr("infoflow.client.get_client", lambda: None)
    web.run_async(cfg)
    assert started.wait(5)
    with pytest.raises(RuntimeError):
        web.run_async(cfg)
    release.set()

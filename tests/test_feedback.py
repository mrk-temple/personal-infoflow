from infoflow.feedback import _aggregate, _parse_digest, _verdict, title_keywords

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
**60** · arXiv

> 还没标

反馈::
"""


def test_verdict_mapping():
    assert _verdict("好") == 1
    assert _verdict("差") == -1
    assert _verdict("") is None
    assert _verdict("maybe") is None


def test_title_keywords_filters_stopwords_and_short():
    kws = title_keywords("Using the new Transformer model")
    assert "transformer" in kws
    assert "model" in kws
    assert "the" not in kws  # stopword
    assert "new" not in kws  # stopword


def test_parse_digest_extracts_only_marked():
    items = _parse_digest(SAMPLE)
    links = {it["link"]: it for it in items}
    assert set(links) == {"https://example.com/a", "https://example.com/b"}
    assert links["https://example.com/a"]["verdict"] == 1
    assert links["https://example.com/a"]["source"] == "Hacker News"
    assert links["https://example.com/a"]["bucket"] == "rel"
    assert links["https://example.com/b"]["verdict"] == -1
    assert links["https://example.com/b"]["bucket"] == "explore"
    assert links["https://example.com/b"]["source"] == "r/programming"


def test_aggregate_source_bias_and_quality():
    log = [
        {"verdict": 1, "source": "Hacker News", "bucket": "rel", "title": "Transformer scaling"},
        {"verdict": 1, "source": "Hacker News", "bucket": "rel", "title": "Diffusion models"},
        {"verdict": -1, "source": "r/programming", "bucket": "explore", "title": "CSS tricks"},
    ]
    state = _aggregate({}, log)
    assert state["source_bias"]["Hacker News"] > 0
    assert state["source_bias"]["r/programming"] < 0
    assert state["quality"]["counts"] == {"pos": 2, "neg": 1}
    assert state["quality"]["overall"] == round(2 / 3, 2)

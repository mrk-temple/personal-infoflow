from infoflow.cluster import cluster_items


def test_near_duplicate_titles_collapse():
    items = [
        {"title": "OpenAI releases new model", "summary": "short", "source": "A"},
        {"title": "OpenAI Releases New Model!", "summary": "a much longer summary here", "source": "B"},
        {"title": "Completely unrelated topic about cats", "summary": "x", "source": "C"},
    ]
    reps = cluster_items(items, threshold=0.82)
    assert len(reps) == 2
    # 每簇留摘要最长的代表
    merged = next(r for r in reps if r["dup_count"] == 2)
    assert merged["summary"] == "a much longer summary here"
    assert merged["dup_count"] == 2
    assert set(merged["dup_sources"]) == {"A", "B"}


def test_distinct_titles_not_merged():
    items = [
        {"title": "alpha", "summary": "", "source": "A"},
        {"title": "beta", "summary": "", "source": "B"},
    ]
    assert len(cluster_items(items)) == 2

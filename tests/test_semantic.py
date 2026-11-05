from infoflow.semantic import _cos, cluster_semantic


def test_cosine_basic():
    assert _cos([1, 0], [1, 0]) == 1.0
    assert _cos([1, 0], [0, 1]) == 0.0
    assert _cos([], [1, 0]) == 0.0


def test_cluster_semantic_merges_close_vectors():
    items = [
        {"title": "a", "summary": "longer one", "source": "A", "_vec": [1.0, 0.0]},
        {"title": "b", "summary": "x", "source": "B", "_vec": [0.99, 0.01]},
        {"title": "c", "summary": "y", "source": "C", "_vec": [0.0, 1.0]},
    ]
    reps = cluster_semantic(items, threshold=0.9)
    assert len(reps) == 2
    merged = next(r for r in reps if r["dup_count"] == 2)
    assert merged["summary"] == "longer one"

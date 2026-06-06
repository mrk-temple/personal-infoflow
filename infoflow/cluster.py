import re
from difflib import SequenceMatcher

_WS = re.compile(r"[\W_]+", re.UNICODE)


def _norm(title):
    return _WS.sub(" ", (title or "").lower()).strip()


def _sim(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def cluster_items(items, threshold=0.82):
    """把标题高度相似的条目聚成一簇，每簇只留一个代表（正文/摘要最长的那个）。"""
    clusters = []
    for it in items:
        norm = _norm(it.get("title", ""))
        for c in clusters:
            if _sim(norm, c["norm"]) >= threshold:
                c["members"].append(it)
                break
        else:
            clusters.append({"norm": norm, "members": [it]})

    reps = []
    for c in clusters:
        rep = dict(max(c["members"], key=lambda m: len(m.get("summary", ""))))
        rep["dup_count"] = len(c["members"])
        rep["dup_sources"] = sorted({m.get("source", "") for m in c["members"]})
        reps.append(rep)
    return reps

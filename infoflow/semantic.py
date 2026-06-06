import json
import math
import pathlib

from .client import resolve
from .embed import embed_texts
from .signals import collect_captures
from .feedback import _state


def _cos(a, b):
    if not a or not b:
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb) if na and nb else 0.0


def embed_items(cfg, items):
    """给每条候选算向量并挂在 it['_vec'] 上。"""
    texts = [((it.get("title", "") + " " + it.get("summary", "")))[:600] for it in items]
    vecs = embed_texts(cfg, texts)
    for it, v in zip(items, vecs):
        it["_vec"] = v
    return items


def cluster_semantic(items, threshold=0.86):
    """按向量余弦相似度聚类去重（比标题字面更准），每簇留摘要最全的代表。"""
    clusters = []
    for it in items:
        v = it.get("_vec")
        placed = False
        if v:
            for c in clusters:
                if c["vec"] and _cos(v, c["vec"]) >= threshold:
                    c["members"].append(it)
                    placed = True
                    break
        if not placed:
            clusters.append({"vec": v, "members": [it]})
    reps = []
    for c in clusters:
        rep = dict(max(c["members"], key=lambda m: len(m.get("summary", ""))))
        rep["dup_count"] = len(c["members"])
        rep["dup_sources"] = sorted({m.get("source", "") for m in c["members"]})
        reps.append(rep)
    return reps


def _anchor_path(cfg):
    return pathlib.Path(resolve(cfg.get("embedding", {}).get("anchor_path", "data/anchors.json")))


def _save_anchors(cfg, vecs):
    p = _anchor_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(vecs), encoding="utf-8")


def _load_anchors(cfg):
    p = _anchor_path(cfg)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def build_anchors(cfg):
    """锚点 = 你点过"好"的条目标题 + 主动保存的捕获内容。它们代表"你真正喜欢的"。"""
    liked = _state(cfg).get("liked", [])
    texts = list(liked)
    cap = collect_captures(cfg).strip()
    if cap:
        texts += [c.strip() for c in cap.splitlines() if len(c.strip()) >= 6][:50]
    texts = [t for t in texts if t][:80]
    if not texts:
        _save_anchors(cfg, [])
        return 0
    _save_anchors(cfg, embed_texts(cfg, texts))
    return len(texts)


def liked_similarity(cfg, items):
    """给每条候选算"与你喜欢过的内容的最高语义相似度"，写到 it['_sim_liked']。"""
    anchors = _load_anchors(cfg)
    if not anchors:
        return
    for it in items:
        v = it.get("_vec")
        it["_sim_liked"] = max((_cos(v, a) for a in anchors), default=0.0) if v else 0.0

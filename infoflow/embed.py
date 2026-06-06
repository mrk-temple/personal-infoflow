import json
import hashlib
import pathlib

from .client import resolve

_MODEL = None  # fastembed 模型懒加载（加载较慢，复用）


def _cfg(cfg):
    return cfg.get("embedding", {})


def _cache_path(cfg):
    return pathlib.Path(resolve(_cfg(cfg).get("cache_path", "data/emb_cache.json")))


def _load_cache(cfg):
    p = _cache_path(cfg)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cfg, cache):
    p = _cache_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache), encoding="utf-8")


def _key(model, text):
    return hashlib.sha1((model + "||" + text).encode("utf-8")).hexdigest()


def available(cfg):
    e = _cfg(cfg)
    if not e.get("enabled", False):
        return False
    if e.get("provider", "fastembed") == "fastembed":
        try:
            import fastembed  # noqa: F401
            return True
        except ImportError:
            return False
    return True  # ollama：假设可达，调用失败时再降级


def _fastembed(cfg, texts):
    global _MODEL
    from fastembed import TextEmbedding
    name = _cfg(cfg).get("model", "BAAI/bge-small-en-v1.5")
    if _MODEL is None or getattr(_MODEL, "_iname", None) != name:
        _MODEL = TextEmbedding(model_name=name)
        _MODEL._iname = name
    return [list(map(float, v)) for v in _MODEL.embed(texts)]


def _ollama(cfg, texts):
    import urllib.request
    e = _cfg(cfg)
    base = e.get("ollama_url", "http://localhost:11434").rstrip("/")
    model = e.get("model", "bge-m3")
    out = []
    for t in texts:
        req = urllib.request.Request(
            f"{base}/api/embeddings",
            data=json.dumps({"model": model, "prompt": t}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            out.append(json.loads(r.read())["embedding"])
    return out


def embed_texts(cfg, texts):
    """返回每条文本的向量；命中缓存的不重算。"""
    if not texts:
        return []
    e = _cfg(cfg)
    provider = e.get("provider", "fastembed")
    model = e.get("model", "BAAI/bge-small-en-v1.5")
    cache = _load_cache(cfg)

    out = [None] * len(texts)
    todo, todo_idx = [], []
    for i, t in enumerate(texts):
        k = _key(model, t)
        if k in cache:
            out[i] = cache[k]
        else:
            todo.append(t)
            todo_idx.append(i)

    if todo:
        vecs = _ollama(cfg, todo) if provider == "ollama" else _fastembed(cfg, todo)
        for j, v in zip(todo_idx, vecs):
            out[j] = v
            cache[_key(model, texts[j])] = v
        _save_cache(cfg, cache)
    return out

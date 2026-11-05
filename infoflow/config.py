"""配置加载与路径解析。

把"读哪份 config、缺省值怎么填、相对路径锚到哪"集中到一处，避免散落在各模块里
用 ``cfg["a"]["b"]`` 直接索引（缺键时报的 KeyError 对用户毫无意义）。
"""
import copy
import os
import pathlib

import yaml

# 包目录：内部相对路径（data/*.json 等）都锚定到这里，不受运行时 cwd 影响。
BASE = pathlib.Path(__file__).resolve().parent


def resolve(p: str) -> str:
    """用户路径展开 ``~``；内部相对路径锚定到包目录，避免受 cwd 影响。"""
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else str(BASE / p)


# 缺省配置：用户 config.yaml 里没写的键回退到这里。只列“有合理默认”的项；
# vault_path / sources / models 这类必须由用户提供的不给默认，缺了就在校验时报错。
DEFAULTS = {
    "profile": {
        "cache_path": "data/profile.md",
        "max_chars": 200000,
        "exclude": [".trash", ".obsidian", "templates"],
    },
    "signals": {
        "chat_dir": "",
        "chat_max_chars": 60000,
        "capture_path": "",
        "capture_max_chars": 20000,
    },
    "fetch": {
        "days": 10,
        "per_feed": 30,
        "full_text": False,
        "full_text_limit": 40,
        "full_text_max_chars": 4000,
        "full_text_timeout": 20,
    },
    "cluster": {"enabled": True, "title_threshold": 0.82},
    "embedding": {
        "enabled": False,
        "provider": "fastembed",
        "model": "BAAI/bge-small-en-v1.5",
        "cluster_threshold": 0.86,
        "liked_boost_max": 12,
        "cache_path": "data/emb_cache.json",
        "anchor_path": "data/anchors.json",
    },
    "rank": {"batch_size": 12, "breadth_weight": 0.4},
    "feedback": {
        "bias_step": 6,
        "bias_cap": 24,
        "remember": 12,
        "keyword_bias_step": 3,
        "keyword_bias_cap": 12,
        "min_source_samples": 4,
        "source_drop_precision": 0.34,
        "adaptive_exploration": True,
    },
    "digest": {
        "min_score": 0,
        "max_items": 10,
        "max_per_source": 3,
        "exploration_ratio": 0.7,
    },
    "portrait": {"enabled": False},
    "state": {
        "seen_path": "data/seen.json",
        "feedback_log": "data/feedback_log.json",
        "feedback_state": "data/feedback_state.json",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """把 override 深合并到 base 的拷贝上（dict 递归合并，其余直接覆盖）。"""
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class ConfigError(SystemExit):
    """配置缺失/不合法时抛出，消息直接给用户看。"""


def validate(cfg: dict) -> dict:
    """对必填项做最小校验，缺了就用一句人话报错（而不是深处某行 KeyError）。"""
    if not cfg.get("models", {}).get("rank"):
        raise ConfigError("config.yaml 缺少 models.rank（打分用的模型名）。")
    if not cfg.get("models", {}).get("profile"):
        raise ConfigError("config.yaml 缺少 models.profile（建画像用的模型名）。")
    if not cfg.get("digest", {}).get("output_dir"):
        raise ConfigError("config.yaml 缺少 digest.output_dir（简报要写到哪个目录）。")
    if not cfg.get("sources") and not cfg.get("feeds"):
        raise ConfigError("config.yaml 里 sources 为空——至少配一个内容源。")
    return cfg


def load_config(path: str) -> dict:
    """读 config.yaml，合并缺省值并校验。找不到文件时给出清晰指引。"""
    p = pathlib.Path(path)
    if not p.exists():
        raise ConfigError(
            f"没找到配置文件 {p}。\n"
            f"先复制模板：cp config.example.yaml config.yaml，再编辑里面的路径和源。"
        )
    user_cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return validate(_deep_merge(DEFAULTS, user_cfg))

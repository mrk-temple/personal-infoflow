"""配置加载与路径解析。

把"读哪份 config、缺省值怎么填、相对路径锚到哪"集中到一处，避免散落在各模块里
用 ``cfg["a"]["b"]`` 直接索引（缺键时报的 KeyError 对用户毫无意义）。
"""
import copy
import math
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
    "language": "zh-CN",
    "models": {"provider": "auto", "profile": "", "rank": "", "base_url": "", "codex_command": "codex", "codex_model": "",
               "cli_workdir": "data/codex-jobs", "timeout": 240},
    "profile": {
        "cache_path": "data/profile.md",
        "max_chars": 200000,
        "exclude": [".trash", ".obsidian", "templates"],
        "refresh_days": 7,
        "recent_days": 30,
    },
    "signals": {
        "chat_dir": "",
        "chat_max_chars": 60000,
        "capture_path": "",
        "capture_max_chars": 20000,
        "half_life_days": 30,
    },
    "telegram": {"enabled": False, "token_env": "TELEGRAM_BOT_TOKEN",
                 "allowed_chat_ids": [], "max_entries": 1000},
    "reading": {"implicit_feedback": False, "half_life_days": 30, "max_entries": 5000},
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
        "model_cache_path": "data/models",
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
        "half_life_days": 90,
    },
    "digest": {
        "min_score": 0,
        "max_items": 10,
        "max_per_source": 3,
        "exploration_ratio": 0.7,
    },
    "portrait": {"enabled": False, "provider": "none", "model": "gpt-image-2",
                 "codex_command": "codex", "timeout": 300, "base_url": "", "width": 1024, "height": 1024,
                 "output_path": "data/portraits/portrait.png", "note_path": "data/portraits/profile.md", "steps": 20},
    "state": {
        "seen_path": "data/seen.json",
        "feedback_log": "data/feedback_log.json",
        "feedback_state": "data/feedback_state.json",
        "activity_path": "data/activity.json",
        "captures_path": "data/captures.json",
        "settings_path": "data/settings.json",
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
    if cfg.get("models", {}).get("provider") != "codex" and not cfg.get("models", {}).get("rank"):
        raise ConfigError("config.yaml 缺少 models.rank（打分用的模型名）。")
    if cfg.get("models", {}).get("provider") != "codex" and not cfg.get("models", {}).get("profile"):
        raise ConfigError("config.yaml 缺少 models.profile（建画像用的模型名）。")
    if not cfg.get("digest", {}).get("output_dir"):
        raise ConfigError("config.yaml 缺少 digest.output_dir（简报要写到哪个目录）。")
    if not cfg.get("sources") and not cfg.get("feeds"):
        raise ConfigError("config.yaml 里 sources 为空——至少配一个内容源。")
    if cfg.get("language") not in {"zh-CN", "en"}:
        raise ConfigError("language must be zh-CN or en.")
    if cfg["models"].get("provider") not in {"auto", "codex", "deepseek", "kimi", "mimo", "qwen", "openai", "anthropic", "custom"}:
        raise ConfigError("Unknown models.provider.")
    if cfg["portrait"].get("provider") not in {"none", "codex", "api", "local"}:
        raise ConfigError("portrait.provider must be none, codex, api or local.")
    for key in ("provider", "profile", "rank", "base_url", "codex_command", "codex_model"):
        if not isinstance(cfg["models"].get(key, ""), str):
            raise ConfigError(f"models.{key} must be text.")
    for section, key, low, high in (
        ("rank", "batch_size", 1, 100), ("rank", "breadth_weight", 0, 1),
        ("digest", "max_items", 1, 100), ("digest", "max_per_source", 0, 100),
        ("digest", "exploration_ratio", 0, 1), ("profile", "max_chars", 1, 1000000),
        ("profile", "refresh_days", 0, 3650), ("profile", "recent_days", 1, 3650),
        ("signals", "half_life_days", 1, 3650), ("feedback", "half_life_days", 0, 3650),
        ("reading", "half_life_days", 1, 3650), ("reading", "max_entries", 1, 100000),
        ("telegram", "max_entries", 1, 100000), ("fetch", "days", 1, 3650),
        ("portrait", "width", 256, 4096), ("portrait", "height", 256, 4096),
        ("portrait", "timeout", 10, 1800), ("portrait", "steps", 1, 150),
        ("models", "timeout", 10, 1800),
    ):
        value = cfg[section][key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ConfigError(f"{section}.{key} must be a number between {low} and {high}.")
        if key in {"batch_size", "max_items", "max_per_source", "max_entries", "max_chars"} and not isinstance(value, int):
            raise ConfigError(f"{section}.{key} must be an integer.")
    if not isinstance(cfg["telegram"]["allowed_chat_ids"], list):
        raise ConfigError("telegram.allowed_chat_ids must be a list.")
    if cfg["telegram"]["enabled"] and not cfg["telegram"]["allowed_chat_ids"]:
        raise ConfigError("Set telegram.allowed_chat_ids before enabling Telegram capture.")
    if not isinstance(cfg.get("sources", []), list) or len(cfg.get("sources", [])) > 100 or any(not isinstance(s, dict) or not s.get("type")
                                                          for s in cfg.get("sources", [])):
        raise ConfigError("sources must be a list of objects with a type.")
    for spec in cfg.get("sources", []):
        limit = spec.get("limit", 30)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ConfigError("Each source limit must be an integer between 1 and 200.")
    for section, key in (("reading", "implicit_feedback"), ("portrait", "enabled"), ("feedback", "adaptive_exploration")):
        if not isinstance(cfg[section][key], bool):
            raise ConfigError(f"{section}.{key} must be true or false.")
    if cfg["portrait"]["enabled"] and not all(cfg["portrait"].get(k) for k in ("output_path", "note_path")):
        raise ConfigError("Enabled portraits need portrait.output_path and portrait.note_path.")
    return cfg


def load_config(path: str) -> dict:
    """读 config.yaml，合并缺省值并校验。找不到文件时给出清晰指引。"""
    p = pathlib.Path(path)
    if not p.exists():
        raise ConfigError(
            f"没找到配置文件 {p}。\n"
            f"先复制模板：cp config.example.yaml config.yaml，再编辑里面的路径和源。"
        )
    try:
        user_cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError("Invalid YAML in config file; check indentation and quoting.") from exc
    if not isinstance(user_cfg, dict):
        raise ConfigError("The configuration root must be a YAML mapping.")
    for key, default in DEFAULTS.items():
        if isinstance(default, dict) and key in user_cfg and not isinstance(user_cfg[key], dict):
            raise ConfigError(f"{key} must be a YAML mapping.")
    if "models" in user_cfg and not isinstance(user_cfg["models"], dict):
        raise ConfigError("models must be a YAML mapping.")
    cfg = validate(_deep_merge(DEFAULTS, user_cfg))
    # Installed wheels need writable state. Paths belong to the config, not site-packages/cwd.
    def anchor(value):
        expanded = pathlib.Path(os.path.expanduser(value))
        return str(expanded if expanded.is_absolute() else p.resolve().parent / expanded)
    for key in ("vault_path",):
        if cfg.get(key):
            cfg[key] = anchor(cfg[key])
    for section, keys in {"profile": ("cache_path",), "signals": ("chat_dir", "capture_path"),
                          "digest": ("output_dir",), "portrait": ("output_path", "note_path"),
                          "embedding": ("cache_path", "anchor_path", "model_cache_path"),
                          "models": ("cli_workdir",),
                          "state": tuple(DEFAULTS["state"])}.items():
        for key in keys:
            if cfg[section].get(key):
                cfg[section][key] = anchor(cfg[section][key])
    cfg["_config_path"] = str(p.resolve())
    from dotenv import load_dotenv
    load_dotenv(p.resolve().parent / ".env", override=False)
    load_dotenv(p.resolve().parent / ".env.local", override=True)
    from .settings import load_saved_settings
    return load_saved_settings(cfg)

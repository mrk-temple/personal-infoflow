"""Persist user choices locally without changing the daily archive or exposing keys."""
import copy
import os
import re
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

from .config import ConfigError, _deep_merge, resolve, validate
from .providers import PROVIDERS, provider_catalog
from .storage import LOCK, read_json, write_json, write_text

FIELDS = {
    "models": {"provider", "profile", "rank", "base_url", "codex_command", "codex_model", "timeout"},
    "digest": {"max_items", "max_per_source", "exploration_ratio", "min_score"},
    "portrait": {"enabled", "provider", "model", "base_url", "codex_command", "width", "height", "timeout", "steps"},
    "reading": {"implicit_feedback"},
    "feedback": {"adaptive_exploration"},
}


def settings_path(cfg):
    return Path(resolve(cfg.get("state", {}).get("settings_path", "data/settings.json")))


def _allowed(data):
    result = {}
    for section, fields in FIELDS.items():
        if section in data:
            if not isinstance(data[section], dict):
                raise ValueError(f"{section} must be an object")
            result[section] = {key: value for key, value in data[section].items() if key in fields}
    if "sources" in data:
        result["sources"] = data["sources"]
    return result


def load_saved_settings(cfg):
    saved = read_json(settings_path(cfg), {})
    return validate(_deep_merge(cfg, _allowed(saved)))


def public_settings(cfg):
    data = _allowed(cfg)
    data["providers"] = provider_catalog()
    data["image_key_configured"] = bool(os.environ.get("IMAGE_API_KEY"))
    return data


def _write_key(cfg, name, value):
    if not isinstance(value, str) or not value or len(value) > 2000 or "\n" in value or "\r" in value:
        raise ValueError("Invalid API key value")
    root = Path(cfg.get("_config_path", str(Path(resolve("data"))) + "/config.yaml")).parent
    path = root / ".env.local"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    line = f"{name}='{value.replace(chr(39), chr(92) + chr(39))}'"
    found = False
    for i, existing in enumerate(lines):
        if re.match(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=", existing):
            lines[i], found = line, True
    if not found:
        lines.append(line)
    write_text(path, "\n".join(lines) + "\n")
    load_dotenv(path, override=True)


def save_settings(cfg, data):
    with LOCK:
        patch = _allowed(data)
        try:
            candidate = validate(_deep_merge(cfg, patch))
        except ConfigError as exc:
            raise ValueError(str(exc)) from None
        # Endpoint URLs must be explicit HTTP(S) endpoints without embedded credentials.
        for section in ("models", "portrait"):
            url = candidate[section].get("base_url", "")
            if url:
                parsed = urllib.parse.urlsplit(url)
                if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError("Invalid endpoint URL")
        if data.get("api_key"):
            provider = candidate["models"].get("provider", "auto")
            if provider not in PROVIDERS or not PROVIDERS[provider]["key_env"]:
                raise ValueError("Choose an API provider before saving a key")
            _write_key(cfg, PROVIDERS[provider]["key_env"], data["api_key"])
        if data.get("image_api_key"):
            _write_key(cfg, "IMAGE_API_KEY", data["image_api_key"])
        persisted = _deep_merge(read_json(settings_path(cfg), {}), patch)
        write_json(settings_path(cfg), persisted)
        cfg.clear()
        cfg.update(copy.deepcopy(candidate))
        return public_settings(cfg)

"""Capture saved text locally, or receive allowlisted Telegram messages by polling."""
import hashlib
import os
import re
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from . import http
from .config import resolve
from .storage import LOCK, decay_weight, read_json, utc_now, write_json

URL_RE = re.compile(r"https?://[^\s<>]+")


class CaptureError(RuntimeError):
    pass


def capture_path(cfg):
    return Path(resolve(cfg.get("state", {}).get("captures_path", "data/captures.json")))


def load_captures(cfg):
    return read_json(capture_path(cfg), {"offset": 0, "items": []})


def _links(text, entities=()):
    links = [m.rstrip(".,;!?)）。，") for m in URL_RE.findall(text)]
    links += [e["url"] for e in entities if e.get("type") == "text_link"
              and str(e.get("url", "")).startswith(("https://", "http://"))]
    return list(dict.fromkeys(links))


def add_capture(cfg, text, source="manual"):
    text = text.strip()
    if not text or len(text) > 12000:
        raise ValueError("Capture text must contain 1–12000 characters")
    key = "manual:" + hashlib.sha256(text.encode()).hexdigest()[:24]
    with LOCK:
        state = load_captures(cfg)
        if any(e["id"] == key for e in state["items"]):
            return False
        state["items"].append({"id": key, "text": text, "links": _links(text),
                               "source": source, "captured_at": utc_now()})
        _save(cfg, state)
    return True


def _save(cfg, state):
    limit = cfg.get("telegram", {}).get("max_entries", 1000)
    state["items"] = sorted(state["items"], key=lambda e: e.get("captured_at", ""))[-limit:]
    write_json(capture_path(cfg), state)


def sync_telegram(cfg):
    settings = cfg.get("telegram", {})
    allowed = {str(v) for v in settings.get("allowed_chat_ids", [])}
    token = os.environ.get(settings.get("token_env", "TELEGRAM_BOT_TOKEN"), "").strip()
    if not allowed:
        raise CaptureError("Set telegram.allowed_chat_ids before receiving Telegram messages.")
    if not token:
        raise CaptureError("Telegram bot token is missing; set the configured token environment variable.")
    with LOCK:
        state = load_captures(cfg)
        offset = state.get("offset", 0)
    # Network I/O is outside the state lock, allowing reading and feedback during polling.
    try:
        response = http.post_json(f"https://api.telegram.org/bot{token}/getUpdates", {
            "offset": offset, "limit": 100, "timeout": 0,
            "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post"],
        }, timeout=30)
    except urllib.error.HTTPError as exc:
        raise CaptureError(f"Telegram HTTP {exc.code}. Check the bot token, webhook and polling ownership.") from None
    except Exception:
        # Telegram tokens are part of the URL; never forward urllib/http exceptions to logs/UI.
        raise CaptureError("Cannot reach Telegram. Check the network and retry.") from None
    if not isinstance(response, dict) or not response.get("ok"):
        raise CaptureError("Telegram rejected getUpdates. Check the bot token and remove any active webhook.")
    updates = response.get("result", [])
    if not isinstance(updates, list):
        raise CaptureError("Invalid Telegram update response; no capture state changed.")
    received = 0
    with LOCK:
        state = load_captures(cfg)
        entries = {e["id"]: e for e in state["items"]}
        for update in sorted(updates, key=lambda u: u.get("update_id", -1)):
            update_id = update.get("update_id")
            if not isinstance(update_id, int) or update_id < state.get("offset", 0):
                continue
            msg = next((update[k] for k in ("message", "edited_message", "channel_post", "edited_channel_post")
                        if isinstance(update.get(k), dict)), {})
            if str(msg.get("chat", {}).get("id")) in allowed:
                text = str(msg.get("text") or msg.get("caption") or "").strip()[:12000]
                if text and isinstance(msg.get("message_id"), int):
                    key = f"telegram:{msg['chat']['id']}:{msg['message_id']}"
                    stamp = datetime.fromtimestamp(msg.get("date", 0), timezone.utc).isoformat()
                    item = {"id": key, "text": text, "source": "Telegram", "captured_at": stamp,
                            "links": _links(text, msg.get("entities") or msg.get("caption_entities") or [])}
                    if entries.get(key) != item:
                        entries[key] = item
                        received += 1
            # Disallowed/unsupported updates are acknowledged as well, avoiding an endless replay.
            state["offset"] = max(state.get("offset", 0), update_id + 1)
        state["items"] = list(entries.values())
        _save(cfg, state)  # Captures and cursor commit together; retries are idempotent.
    return {"received": received, "offset": state["offset"], "total": len(state["items"])}


def capture_context(cfg):
    settings = cfg.get("signals", {})
    half_life = settings.get("half_life_days", 30)
    budget = settings.get("capture_max_chars", 20000)
    chunks = []
    for entry in reversed(load_captures(cfg)["items"]):
        weight = decay_weight(entry.get("captured_at"), half_life)
        if weight < .1:
            continue
        chunks.append(f"[{entry['captured_at'][:10]} · weight {weight:.2f}] {entry['text']}")
    return "\n\n".join(chunks)[:budget]

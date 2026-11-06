"""Opt-in, local reading signals. A click is never a dislike or a full read."""
import math
from pathlib import Path

from .config import resolve
from .storage import LOCK, decay_weight, read_json, utc_now, write_json


def activity_path(cfg):
    return Path(resolve(cfg.get("state", {}).get("activity_path", "data/activity.json")))


def load_activity(cfg):
    return read_json(activity_path(cfg), {})


def record_activity(cfg, day, item, event, value=None):
    if event not in {"open", "read", "save", "dwell"}:
        raise ValueError("Unknown reading event")
    if event in {"read", "save"} and not isinstance(value, bool):
        raise ValueError("read/save requires a boolean")
    if event == "dwell" and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or value < 0):
        raise ValueError("dwell requires finite, non-negative seconds")
    with LOCK:
        state = load_activity(cfg)
        key = f"{day}\t{item['link']}"
        entry = state.get(key, {"date": day, "link": item["link"], "read": False, "saved": False})
        entry.update({k: item.get(k, "") for k in ("title", "source", "bucket")})
        if event == "open":
            entry["opened_at"] = utc_now()
        elif event == "dwell":
            # Browser submits total visible seconds, so retries cannot multiply the signal.
            entry["dwell_seconds"] = max(entry.get("dwell_seconds", 0), min(value, 600))
        else:
            entry["read" if event == "read" else "saved"] = value
        entry["updated_at"] = utc_now()
        state[key] = entry
        limit = cfg.get("reading", {}).get("max_entries", 5000)
        state = dict(sorted(state.items(), key=lambda pair: pair[1].get("updated_at", ""))[-limit:])
        write_json(activity_path(cfg), state)
        return entry


def implicit_signals(cfg, explicit=()):
    if not cfg.get("reading", {}).get("implicit_feedback", False):
        return []
    blocked = {(e["date"], e["link"]) for e in explicit}
    half_life = cfg.get("reading", {}).get("half_life_days", 30)
    signals = []
    for e in load_activity(cfg).values():
        if (e["date"], e["link"]) in blocked:
            continue  # Explicit good/bad always takes precedence, including explicit dislikes.
        strength = .5 if e.get("saved") else .15 if e.get("dwell_seconds", 0) >= 30 else 0
        weight = strength * decay_weight(e.get("updated_at"), half_life)
        if weight > .01:
            signals.append({**e, "weight": weight})
    return signals

"""Small, atomic local stores shared by the CLI and the threaded web server."""
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOCK = threading.RLock()


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Invalid JSON state: {Path(path).name}. Restore a backup before retrying.") from exc


def write_text(path, text):
    """Replace on the same filesystem; interrupted writes leave the old file intact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def decay_weight(stamp, half_life_days, now=None):
    if not half_life_days:
        return 1.0
    try:
        when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        when = when.replace(tzinfo=when.tzinfo or timezone.utc)
        age = max(0, ((now or datetime.now(timezone.utc)) - when).total_seconds() / 86400)
        return 2 ** (-age / half_life_days)
    except (ValueError, TypeError):
        return 0.0

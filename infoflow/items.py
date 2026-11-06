"""One Markdown format parser for feedback synchronization and both UI languages."""
import re
from datetime import date

POS = {"好", "赞", "+", "👍", "有用", "有价值", "good"}
NEG = {"差", "噪音", "-", "👎", "无用", "没用", "bad"}
LINK_RE = re.compile(r"^##\s+\[(.*?)\]\((.+)\)\s*$")
META_RE = re.compile(r"^\*\*(\d+)\*\*(.*)$")
FB_RE = re.compile(r"^(?:反馈|Feedback)::\s*(.*)$", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DUP_RE = re.compile(r"(?:也被\s*(\d+)\s*个其他源报道|also in (\d+) other sources)", re.I)


def valid_date(value):
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def verdict(token):
    token = token.strip().lower()
    return 1 if token in POS else -1 if token in NEG else None


def parse_digest(text):
    items, cur = [], None
    for line in text.splitlines():
        m = LINK_RE.match(line)
        if m:
            cur = {"title": m[1], "link": m[2], "score": "", "source": "",
                   "bucket": "rel", "dup_count": 1, "enriched": False,
                   "reason": "", "verdict": None}
            items.append(cur)
        elif cur is not None:
            meta = META_RE.match(line)
            fb = FB_RE.match(line)
            if meta:
                cur["score"] = meta[1]
                cur["enriched"] = "📄" in meta[2]
                segs = [s.replace("📄", "").strip() for s in meta[2].split("·")]
                cur["bucket"] = "explore" if any(s.lower() in {"拓展", "explore"} for s in segs) else "rel"
                for s in segs:
                    duplicate = DUP_RE.search(s)
                    if duplicate:
                        cur["dup_count"] = int(duplicate[1] or duplicate[2]) + 1
                cur["source"] = next((s for s in segs if s and s.lower() not in {"拓展", "explore"}
                                      and not DUP_RE.search(s)), "")
            elif fb:
                v = verdict(fb[1])
                cur["verdict"] = "pos" if v == 1 else "neg" if v == -1 else None
                cur = None
            elif line.startswith("> "):
                cur["reason"] += ("\n" if cur["reason"] else "") + line[2:].strip()
    return items

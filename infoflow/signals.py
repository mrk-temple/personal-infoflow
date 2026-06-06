import json
import pathlib

from .client import resolve

CHAT_EXTS = {".json", ".md", ".txt"}
CAP_EXTS = {".md", ".txt"}


def _strings_from_json(obj, acc, limit=4000):
    """通用兜底：从任意 JSON 里捞出像"对话内容"的字符串叶子。"""
    if len(acc) >= limit:
        return
    if isinstance(obj, str):
        s = obj.strip()
        if 8 <= len(s) <= 2000 and not s.startswith(("http://", "https://", "data:")):
            acc.append(s)
    elif isinstance(obj, list):
        for v in obj:
            _strings_from_json(v, acc, limit)
    elif isinstance(obj, dict):
        for v in obj.values():
            _strings_from_json(v, acc, limit)


def _chatgpt_user_msgs(data):
    """专门解析 ChatGPT 导出的 conversations.json，只取你（user）说的话。"""
    out = []
    convs = data if isinstance(data, list) else [data]
    for conv in convs:
        if not isinstance(conv, dict):
            continue
        mapping = conv.get("mapping")
        if not isinstance(mapping, dict):
            continue
        for node in mapping.values():
            msg = (node or {}).get("message") or {}
            if (msg.get("author") or {}).get("role") != "user":
                continue
            for part in (msg.get("content") or {}).get("parts") or []:
                if isinstance(part, str) and part.strip():
                    out.append(part.strip())
    return out


def _claude_user_msgs(data):
    """解析 Claude 导出的 conversations.json，只取 human（你）的消息。"""
    out = []
    convs = data if isinstance(data, list) else [data]
    for conv in convs:
        if not isinstance(conv, dict):
            continue
        msgs = conv.get("chat_messages")
        if not isinstance(msgs, list):
            continue
        for m in msgs:
            if not isinstance(m, dict) or m.get("sender") != "human":
                continue
            texts = [
                blk["text"].strip()
                for blk in (m.get("content") or [])
                if isinstance(blk, dict) and blk.get("type") == "text" and blk.get("text")
            ]
            if not texts and m.get("text"):           # 老版导出把全文放在顶层 text
                texts = [str(m["text"]).strip()]
            out.extend(t for t in texts if t)
    return out


def _extract_chat_file(f):
    try:
        raw = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    if f.suffix.lower() != ".json":
        return raw  # md / txt 直接用
    try:
        data = json.loads(raw)
    except Exception:
        return raw[:5000]
    for parser in (_claude_user_msgs, _chatgpt_user_msgs):  # 先 Claude，再 ChatGPT
        msgs = parser(data)
        if msgs:
            return "\n".join(msgs)
    acc = []                                  # 都不匹配就通用兜底
    _strings_from_json(data, acc)
    return "\n".join(acc)


def _read_capped(files, cap, extractor):
    files = [f for f in files if f.is_file()]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)  # 最近的优先
    chunks, total = [], 0
    for f in files:
        text = (extractor(f) or "").strip()
        if not text:
            continue
        if total + len(text) > cap:
            text = text[: max(0, cap - total)]
        chunks.append(text)
        total += len(text)
        if total >= cap:
            break
    return "\n\n".join(chunks)


def collect_chat(cfg):
    s = cfg.get("signals", {})
    path = s.get("chat_dir", "")
    if not path:
        return ""
    p = pathlib.Path(resolve(path))
    if not p.exists():
        return ""
    files = [f for f in p.rglob("*") if f.suffix.lower() in CHAT_EXTS]
    return _read_capped(files, s.get("chat_max_chars", 60000), _extract_chat_file)


def collect_captures(cfg):
    s = cfg.get("signals", {})
    path = s.get("capture_path", "")
    if not path:
        return ""
    p = pathlib.Path(resolve(path))
    if not p.exists():
        return ""
    cap = s.get("capture_max_chars", 20000)
    if p.is_file():
        try:
            return p.read_text(encoding="utf-8", errors="ignore")[:cap]
        except Exception:
            return ""
    files = [f for f in p.rglob("*") if f.suffix.lower() in CAP_EXTS]
    return _read_capped(files, cap, lambda f: f.read_text(encoding="utf-8", errors="ignore"))


def extra_profile_context(cfg):
    """返回 (拼给画像的文本块, 是否有对话, 是否有捕获)。"""
    chat = collect_chat(cfg).strip()
    cap = collect_captures(cfg).strip()
    block = ""
    if chat:
        block += ("\n\n【你最近与 AI 的对话——代表你当前在好奇、在攻克什么，"
                  "时效性强，权重应高于旧笔记】：\n" + chat)
    if cap:
        block += ("\n\n【你最近主动保存/刷到、觉得值得看的内容——"
                  "代表你真实的兴趣取向与品味】：\n" + cap)
    return block, bool(chat), bool(cap)

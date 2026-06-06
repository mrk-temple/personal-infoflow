import os
import pathlib

from .client import chat, resolve
from .feedback import feedback_for_profile
from .signals import extra_profile_context

PROFILE_SYS = """你在为一个人建立"兴趣画像"。材料可能来自多个来源：
- 个人笔记：代表他的知识结构与长期兴趣（注意：笔记里写得很透的基础内容，恰恰是他已熟知、不必再推荐的）
- 与 AI 的对话：代表他当前在好奇、在攻克的问题，时效性强，权重更高
- 主动保存/刷到的内容：代表他真实的兴趣取向与品味
请综合这些，输出一份简洁的画像档案，用第二人称（"你"）书写，涵盖：
- 你长期关注的领域，以及每个领域大致的深度（入门 / 熟练 / 专家）
- 你最近在做什么、在好奇什么（优先依据对话与保存的内容，而非旧笔记）
- 你大概率已经熟知、因此不需要再被推荐基础内容的主题
- 你能看出的目标或动机
控制在 500 字左右，分点清晰，避免空话套话。"""


def collect_notes(vault, max_chars, exclude):
    vault = resolve(vault)
    files = []
    for p in pathlib.Path(vault).rglob("*.md"):
        if any(x in str(p) for x in exclude):
            continue
        files.append(p)
    # 最近修改的排前面——更代表你当前的兴趣
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    chunks, total = [], 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        snippet = f"### {p.name}\n{text}\n"
        if total + len(snippet) > max_chars:
            break
        chunks.append(snippet)
        total += len(snippet)
    return "\n".join(chunks), len(chunks)


def build_profile(client, cfg):
    notes, n = collect_notes(
        cfg["vault_path"],
        cfg["profile"]["max_chars"],
        cfg["profile"]["exclude"],
    )
    if not notes.strip():
        raise SystemExit("没读到任何笔记，检查 config.yaml 里的 vault_path")

    extra, has_chat, has_cap = extra_profile_context(cfg)
    if has_chat:
        print("  纳入信号：AI 对话记录")
    if has_cap:
        print("  纳入信号：推送 / 保存捕获")

    profile = chat(
        client,
        cfg["models"]["profile"],
        PROFILE_SYS,
        f"以下是按最近修改排序的 {n} 篇笔记：\n\n{notes}" + extra + feedback_for_profile(cfg),
        temperature=0.4,
    )
    out = pathlib.Path(resolve(cfg["profile"]["cache_path"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(profile, encoding="utf-8")
    print(f"  已读入 {n} 篇笔记，画像写入 {out}")
    return profile


def load_profile(client, cfg, refresh=False):
    path = pathlib.Path(resolve(cfg["profile"]["cache_path"]))
    if refresh or not path.exists():
        return build_profile(client, cfg)
    return path.read_text(encoding="utf-8")

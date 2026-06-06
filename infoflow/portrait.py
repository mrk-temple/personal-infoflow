import pathlib
import urllib.parse
import urllib.request

from .client import chat, resolve

PROMPT_SYS = """把下面这份"兴趣画像"提炼成一句用于 AI 绘画的英文提示词。
要求：
- 抓住这个人"与信息、知识的关系"是什么气质——是收集者、编织者、园丁、探索者，还是别的？用一个统领全局的核心隐喻来表达。
- 用氛围、光线、空间、象征性物件来传达，而不是罗列他具体在学的学科或工具名（不要出现 textbook / ResNet / calculus / operating systems 这类具体科目或模型名）。
- 画面要克制、有留白、有想象空间，避免把桌面堆得满满当当。
- 不画真人肖像。
- 带上风格词（如 illustration, soft light, minimal, atmospheric）。
只输出这一句英文提示词本身，不要引号、不要解释、不要换行。"""


def build_image_prompt(client, cfg, profile):
    p = cfg.get("portrait", {})
    override = p.get("prompt_override", "").strip()
    if override:                       # 直接锁定提示词，跳过模型生成
        return override
    hint = p.get("style_hint", "").strip()
    user = profile
    if hint:
        user += f"\n\n【额外的画面basis/意象要求，请优先体现】：{hint}"
    return chat(client, cfg["models"]["rank"], PROMPT_SYS, user, temperature=0.7).strip()


def generate_portrait(client, cfg, profile):
    # 本地 MVP 只用 Pollinations（免费、无需 key），够验证效果。
    # 真正的出图（Codex OAuth + gpt-image-2）留到 Hermes skill 阶段做。
    p = cfg["portrait"]
    prompt = build_image_prompt(client, cfg, profile)

    params = urllib.parse.urlencode({
        "width": p.get("width", 1024),
        "height": p.get("height", 1024),
        "model": p.get("model", "flux"),
    })
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "infoflow/0.1"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()

    base = pathlib.Path(resolve(p["output_path"]))
    base.parent.mkdir(parents=True, exist_ok=True)
    # 带时间戳存档，保留每一张，看得到蜕变
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out = base.with_name(f"{base.stem}-{stamp}{base.suffix}")
    out.write_bytes(data)
    return out, prompt


def write_profile_note(cfg, profile, img_path, prompt):
    note = pathlib.Path(resolve(cfg["portrait"]["note_path"]))
    note.parent.mkdir(parents=True, exist_ok=True)
    img_name = pathlib.Path(img_path).name
    from datetime import datetime
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new = not note.exists()

    block = []
    if new:
        block += ["# 兴趣画像 · 成长档案", "",
                  "_每次重建画像都会在下面追加一张，记录你一点点的蜕变。_", ""]
    block += [
        f"## 🕐 {stamp}",
        "",
        f"![[{img_name}]]",
        "",
        f"> 绘画提示词：{prompt}",
        "",
        "> [!note]- 当时的画像文字",
        *["> " + ln for ln in profile.splitlines()],
        "",
    ]
    with open(note, "w" if new else "a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")
    return note

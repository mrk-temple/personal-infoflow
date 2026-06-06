import os
import json
import pathlib

from openai import OpenAI

# 自动加载 .env（从当前目录向上找）。没装 python-dotenv 也不报错，
# 这时就退回到读真实环境变量。
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

BASE = pathlib.Path(__file__).resolve().parent


def resolve(p: str) -> str:
    """用户路径展开 ~，内部相对路径锚定到包目录，避免受 cwd 影响。"""
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else str(BASE / p)


def get_client() -> OpenAI:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit(
            "没读到 DEEPSEEK_API_KEY。检查：\n"
            "  1) .env 是否在你运行命令的那个目录（或其上级）\n"
            "  2) .env 里写的是  DEEPSEEK_API_KEY=sk-xxx  （等号两边不要空格、不要引号）\n"
            "  3) 是否已 pip install python-dotenv"
        )
    # DeepSeek 的 API 与 OpenAI 兼容，只换 base_url
    return OpenAI(api_key=key, base_url="https://api.deepseek.com")


def chat(client, model, system, user, temperature=0.3):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content


def extract_json(raw: str):
    """从模型输出里稳妥地抠出 JSON，兼容带 ``` 代码块或前后废话的情况。"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if "\n" in raw:
            first, rest = raw.split("\n", 1)
            if first.strip().lower() in ("json", ""):
                raw = rest
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1]
    return json.loads(raw)

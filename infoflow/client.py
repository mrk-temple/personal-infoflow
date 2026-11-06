"""大模型客户端封装：建 client、发对话、稳妥地从输出里抠 JSON。

路径解析（``resolve``）已挪到 :mod:`infoflow.config`，这里只管"和模型说话"。
"""
import json
import os

from openai import OpenAI

from .providers import PROVIDERS, AnthropicClient, CodexClient, configured_key

# 自动加载 .env（从当前目录向上找）。没装 python-dotenv 也不报错，
# 这时就退回到读真实环境变量。
try:
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

DEFAULT_BASE_URL = "https://api.deepseek.com"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.6-pro"


def _env(*names):
    """依次取第一个非空的环境变量。"""
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return None


def model_settings(cfg=None):
    """按供应商成组解析配置，防止 MiMo key 配上旧网关地址或模型。"""
    models = (cfg or {}).get("models", {})
    selected = models.get("provider", "auto")
    if selected != "auto":
        if selected not in PROVIDERS:
            raise ValueError("Unknown model provider")
        spec = PROVIDERS[selected]
        prefix = selected.upper()
        return {"provider": spec["label"], "id": selected, "key": configured_key(selected),
                "base_url": models.get("base_url") or _env(prefix + "_BASE_URL") or spec["base_url"],
                "model": None}
    mimo_key = _env("MIMO_API_KEY")
    if mimo_key:
        return {
            "provider": "MiMo", "key": mimo_key,
            "base_url": _env("MIMO_BASE_URL") or MIMO_BASE_URL,
            "model": _env("MIMO_MODEL") or MIMO_MODEL,
        }
    deepseek_key = _env("DEEPSEEK_API_KEY")
    if deepseek_key:
        return {"provider": "DeepSeek", "key": deepseek_key,
                "base_url": _env("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL,
                "model": _env("DEEPSEEK_MODEL")}
    for provider in ("kimi", "qwen", "anthropic", "custom"):
        if configured_key(provider):
            settings = model_settings({"models": {"provider": provider}})
            settings["model"] = _env(provider.upper() + "_MODEL") or PROVIDERS[provider]["model"]
            return settings
    key = _env("OPENAI_API_KEY")
    return {
        "provider": "OpenAI 兼容网关",
        "key": key,
        "base_url": _env("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "model": _env("OPENAI_MODEL"),
    }


def model_status(cfg):
    """只供界面读取非敏感状态；密钥与地址不返回给浏览器。"""
    settings = model_settings(cfg)
    return {
        "provider": settings["provider"], "configured": bool(settings["key"]) or settings.get("id") == "codex",
        "model": settings["model"] or cfg.get("models", {}).get("rank", ""),
    }


def get_client(cfg=None):
    settings = model_settings(cfg)
    if settings.get("id") == "codex":
        return CodexClient(cfg or {})
    key = settings["key"]
    if not key:
        if settings.get("id") in PROVIDERS:
            raise RuntimeError(f"Missing {PROVIDERS[settings['id']]['key_env']}. Configure this provider in Settings.")
        raise SystemExit(
            "没读到 API key。检查：\n"
            "  1) .env 是否在你运行命令的那个目录（或其上级）\n"
            "  2) .env 里写了 MIMO_API_KEY=你的密钥（也支持 DEEPSEEK_API_KEY / OPENAI_API_KEY）\n"
            "     （等号两边不要空格、不要引号）\n"
            "  3) 是否已 pip install python-dotenv"
        )
    # DeepSeek/OpenAI 兼容端点只换 base_url；环境变量可覆盖（接代理/自建网关）。
    if settings.get("id") == "anthropic":
        return AnthropicClient(settings)
    instance = OpenAI(api_key=key, base_url=settings["base_url"], timeout=120, max_retries=1)
    instance._infoflow_settings = settings
    return instance


def resolve_model(cfg_model):
    """MiMo 配置优先；否则 OPENAI_MODEL / DEEPSEEK_MODEL 覆盖配置模型名。

    用同一个网关跑全部任务（画像 + 打分 + 配图提示词）时，改 .env 即可，
    不用动 config.yaml。没设就原样用 config 的。
    """
    return model_settings()["model"] or cfg_model


def chat(client, model, system, user, temperature=0.3):
    if isinstance(client, (CodexClient, AnthropicClient)):
        return client.complete(model, system, user, temperature)
    settings = getattr(client, "_infoflow_settings", None)
    actual_model = (settings.get("model") or model) if settings is not None else resolve_model(model)
    # Keep provider/model defaults: reasoning models may reject arbitrary temperature values.
    resp = client.chat.completions.create(
        model=actual_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content


def extract_json(raw: str):
    """从模型输出里稳妥地抠出 JSON，兼容带 ``` 代码块或前后废话的情况。"""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if "\n" in raw:
            first, rest = raw.split("\n", 1)
            if first.strip().lower() in ("json", ""):
                raw = rest
    decoder = json.JSONDecoder()
    for start, char in enumerate(raw):
        if char in "[{":
            try:
                value, _ = decoder.raw_decode(raw[start:])
                return value
            except ValueError:
                continue
    return json.loads(raw)

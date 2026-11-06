import base64
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infoflow.client import get_client, model_settings
from infoflow.config import DEFAULTS, load_config
from infoflow.portrait import generate_portrait
from infoflow.providers import PROVIDERS, AnthropicClient, CodexClient
from infoflow.settings import public_settings, save_settings


@pytest.mark.parametrize("provider", ["deepseek", "kimi", "mimo", "qwen", "openai", "anthropic"])
def test_explicit_provider_never_reuses_another_providers_credentials(provider, monkeypatch):
    monkeypatch.setenv("MIMO_API_KEY", "mimo-other-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://old.invalid/v1")
    monkeypatch.setenv(PROVIDERS[provider]["key_env"], f"test-{provider}")
    cfg = {"models": {"provider": provider, "base_url": "https://chosen.invalid/v1"}}
    settings = model_settings(cfg)
    assert settings["key"] == f"test-{provider}"
    assert settings["base_url"] == "https://chosen.invalid/v1"


def test_missing_selected_provider_key_does_not_fall_back_to_mimo(monkeypatch):
    monkeypatch.setenv("MIMO_API_KEY", "test-mimo")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_client({"models": {"provider": "anthropic"}})


def test_anthropic_uses_native_messages_protocol(monkeypatch):
    calls = []
    def post(url, payload, **kwargs):
        calls.append((url, payload, kwargs))
        return {"content": [{"type": "thinking", "thinking": "hidden"}, {"type": "text", "text": "Answer"}]}
    monkeypatch.setattr("infoflow.providers.http.post_json", post)
    client = AnthropicClient({"key": "test-anthropic", "base_url": "https://api.anthropic.com"})
    assert client.complete("chosen-model", "System", "User", .2) == "Answer"
    assert calls[0][0] == "https://api.anthropic.com/v1/messages"
    assert calls[0][1]["system"] == "System"
    assert calls[0][2]["headers"]["x-api-key"] == "test-anthropic"


def test_cli_text_runtime_needs_no_api_key_and_keeps_output_in_its_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-forwarded")
    monkeypatch.setattr("infoflow.providers.shutil.which", lambda name: "codex")
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        output = Path(args[args.index("--output-last-message") + 1])
        output.write_text('{"items":[]}', encoding="utf-8")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr("infoflow.providers.subprocess.run", run)
    client = CodexClient({"models": {"cli_workdir": str(tmp_path), "codex_command": "codex"}})
    assert client.complete("ignored", "System", "User", .2) == '{"items":[]}'
    assert "OPENAI_API_KEY" not in calls[0][1]["env"]
    assert "--ephemeral" in calls[0][0] and "--worktree" not in calls[0][0]
    assert calls[0][0][calls[0][0].index("--sandbox") + 1] == "read-only"


def config(tmp_path):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["models"].update(provider="codex", profile="", rank="")
    cfg["digest"]["output_dir"] = str(tmp_path / "Daily")
    cfg["sources"] = [{"type": "hackernews", "limit": 10}]
    cfg["state"] = {k: str(tmp_path / f"{k}.json") for k in cfg["state"]}
    cfg["_config_path"] = str(tmp_path / "config.yaml")
    return cfg


def test_persisted_settings_survive_restart_without_touching_daily_archive(tmp_path):
    cfg = config(tmp_path)
    archive = tmp_path / "Daily"
    archive.mkdir()
    day = archive / "2026-11-05.md"
    day.write_text("My previous edition", encoding="utf-8")
    import yaml
    Path(cfg["_config_path"]).write_text(yaml.safe_dump(cfg), encoding="utf-8")
    save_settings(cfg, {"digest": {"max_items": 8, "exploration_ratio": .4},
                        "sources": [{"type": "hackernews", "limit": 20}]})
    loaded = load_config(cfg["_config_path"])
    assert loaded["digest"]["max_items"] == 8 and loaded["digest"]["exploration_ratio"] == .4
    assert loaded["sources"][0]["limit"] == 20
    assert day.read_text(encoding="utf-8") == "My previous edition"


def test_api_keys_are_saved_locally_and_never_returned_or_in_settings_json(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cfg = config(tmp_path)
    result = save_settings(cfg, {"models": {"provider": "anthropic", "profile": "test-model", "rank": "test-model"},
                                 "api_key": "secret-for-local-test"})
    assert "secret-for-local-test" in (tmp_path / ".env.local").read_text(encoding="utf-8")
    assert "secret-for-local-test" not in json.dumps(result)
    assert "secret-for-local-test" not in Path(cfg["state"]["settings_path"]).read_text(encoding="utf-8")
    assert "secret-for-local-test" not in json.dumps(public_settings(cfg))


def test_invalid_settings_dont_replace_previous_values(tmp_path):
    cfg = config(tmp_path)
    with pytest.raises(ValueError):
        save_settings(cfg, {"digest": {"exploration_ratio": 2}})
    assert cfg["digest"]["exploration_ratio"] == .7
    assert not Path(cfg["state"]["settings_path"]).exists()


@pytest.mark.parametrize("provider", ["api", "local"])
def test_image_api_and_local_server_are_optional_adapters(tmp_path, monkeypatch, provider):
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1cAAAAASUVORK5CYII=")
    encoded = base64.b64encode(png).decode()
    monkeypatch.setenv("IMAGE_API_KEY", "test-image-key")
    calls = []
    def post(url, payload, **kwargs):
        calls.append((url, payload, kwargs))
        return {"data": [{"b64_json": encoded}]} if provider == "api" else {"images": [encoded]}
    monkeypatch.setattr("infoflow.portrait.http.post_json", post)
    cfg = {"portrait": {"provider": provider, "base_url": "http://localhost:7860", "model": "chosen-model",
                         "output_path": str(tmp_path / "portrait.png"), "prompt_override": "A garden"}}
    path, _ = generate_portrait(None, cfg, "")
    assert path.read_bytes() == png
    assert calls[0][0].endswith("/images/generations" if provider == "api" else "/sdapi/v1/txt2img")

import pytest

from infoflow import client
from infoflow.client import extract_json


@pytest.fixture
def clean_provider_env(monkeypatch):
    for prefix in ("MIMO", "OPENAI", "DEEPSEEK"):
        for suffix in ("API_KEY", "BASE_URL", "MODEL"):
            monkeypatch.delenv(f"{prefix}_{suffix}", raising=False)


def test_mimo_credentials_do_not_use_legacy_gateway(monkeypatch, clean_provider_env):
    monkeypatch.setenv("MIMO_API_KEY", "test-mimo-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-old-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://old.invalid/v1")
    monkeypatch.setenv("OPENAI_MODEL", "old-model")
    settings = client.model_settings()
    assert settings["key"] == "test-mimo-key"
    assert settings["base_url"] == client.MIMO_BASE_URL
    assert client.resolve_model("deepseek-model") == client.MIMO_MODEL


def test_mimo_token_plan_overrides(monkeypatch, clean_provider_env):
    monkeypatch.setenv("MIMO_API_KEY", "test-key")
    monkeypatch.setenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
    monkeypatch.setenv("MIMO_MODEL", "mimo-custom")
    instance = client.get_client()
    assert str(instance.base_url) == "https://token-plan-cn.xiaomimimo.com/v1/"
    assert client.resolve_model("legacy") == "mimo-custom"
    instance.close()


def test_legacy_gateway_remains_usable(monkeypatch, clean_provider_env):
    monkeypatch.setenv("OPENAI_API_KEY", "test-old-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://old.invalid/v1")
    monkeypatch.setenv("OPENAI_MODEL", "old-model")
    assert client.model_settings()["base_url"] == "https://old.invalid/v1"
    assert client.resolve_model("from-config") == "old-model"


def test_browser_status_never_contains_credentials(monkeypatch, clean_provider_env):
    monkeypatch.setenv("MIMO_API_KEY", "private-test-key")
    status = client.model_status({})
    assert status == {"provider": "MiMo", "configured": True, "model": client.MIMO_MODEL}
    assert "private-test-key" not in str(status)


def test_missing_credentials_have_clear_error(clean_provider_env):
    with pytest.raises(SystemExit, match="MIMO_API_KEY"):
        client.get_client()


def test_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_fenced_json_block():
    raw = "```json\n{\"items\": [1, 2]}\n```"
    assert extract_json(raw) == {"items": [1, 2]}


def test_json_with_surrounding_prose():
    raw = '好的，结果如下：{"score": 80} 以上。'
    assert extract_json(raw) == {"score": 80}


def test_bare_fence_without_lang():
    raw = "```\n{\"x\": true}\n```"
    assert extract_json(raw) == {"x": True}


def test_legacy_deepseek_key_does_not_fall_through_to_openai_endpoint(monkeypatch, clean_provider_env):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://other-provider.invalid/v1")
    assert client.model_settings()["base_url"] == client.DEFAULT_BASE_URL


def test_openai_key_without_override_uses_official_openai_endpoint(monkeypatch, clean_provider_env):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    assert client.model_settings()["base_url"] == "https://api.openai.com/v1"

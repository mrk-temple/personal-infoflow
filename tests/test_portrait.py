import base64
from types import SimpleNamespace

import pytest

from infoflow.portrait import generate_portrait, import_portrait, prepare_portrait

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1cAAAAASUVORK5CYII=")


def config(tmp_path):
    return {"portrait": {"output_path": str(tmp_path / "portrait.png"), "prompt_override": "A quiet garden of ideas",
                         "provider": "codex", "model": "gpt-image-2"}}


def test_app_handoff_writes_a_reviewable_imagegen_prompt(tmp_path):
    job, prompt = prepare_portrait(None, config(tmp_path), "")
    text = (job / "prompt.md").read_text(encoding="utf-8")
    assert "$imagegen" in text and "gpt-image-2" in text
    assert prompt in text and str(job / "portrait.png") in text


def test_cli_bridge_is_ephemeral_and_uses_a_scoped_workspace(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("infoflow.portrait.shutil.which", lambda executable: "codex")
    def run(args, **kwargs):
        calls.append((args, kwargs))
        (kwargs["cwd"] / "portrait.png").write_bytes(PNG)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr("infoflow.portrait.subprocess.run", run)
    out, _ = generate_portrait(None, config(tmp_path), "")
    assert out.read_bytes() == PNG
    assert "--ephemeral" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--sandbox") + 1] == "workspace-write"
    assert "shell" not in calls[0][1]


def test_import_validates_png_and_keeps_previous_portraits(tmp_path):
    src = tmp_path / "source.png"
    src.write_bytes(PNG)
    first = import_portrait(config(tmp_path), src)
    second = import_portrait(config(tmp_path), src)
    assert first != second and first.exists() and second.exists()
    src.write_text("not an image", encoding="utf-8")
    with pytest.raises(ValueError, match="not a PNG"):
        import_portrait(config(tmp_path), src)


def test_missing_codex_reports_app_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr("infoflow.portrait.shutil.which", lambda command: None)
    with pytest.raises(RuntimeError, match="portrait-prepare"):
        generate_portrait(None, config(tmp_path), "")

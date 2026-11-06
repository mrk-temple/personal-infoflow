# Optional profile illustrations

Use the backend the user selected in `portrait.provider`; keep it optional:

- `none`: no generation.
- `api`: the user's image API endpoint/model and `IMAGE_API_KEY`.
- `codex`: the signed-in Codex CLI, using its built-in `gpt-image-2` tool when available.
- `local`: an existing Automatic1111 / Forge service exposing `/sdapi/v1/txt2img`.

`--portrait` requests one illustration without fetching another digest. Ordinary
profile refresh generates an image only when `portrait.enabled` is true. A prompt
override skips the text-model prompt step; otherwise the configured text provider
turns the interest profile into a restrained visual metaphor.

Archive each PNG with a unique timestamp under `portrait.output_path`'s directory,
append the profile note and keep prior images. Do not replace a missing local model,
CLI tool or quota with a paid service unless the user chooses it.

If CLI automation lacks image generation, run `--portrait-prepare`, open its generated
prompt in the Codex App, then import the completed PNG with `--portrait-import FILE`.
This uses ordinary app/CLI authentication; do not read/copy OAuth tokens or create
API keys to imitate subscription access.

Verify that a real PNG was produced and archived. Report an unavailable tool or
failed request honestly. Protocol/unit tests alone do not establish live account access.

# Configuration reference

The maintained full reference is the repository's `docs/CONFIGURATION.md`; defaults
live in `infoflow/config.py` and examples in `config.example.yaml`.

Important decisions for an agent:

- Resolve all relative user paths from the config file's directory. Legacy state
  may still be explicitly located under `infoflow/data/`; preserve it during upgrades.
- Web choices persist in `state.settings_path` and override the corresponding YAML
  preferences. Do not overwrite them to impose a default 3:7 recipe or provider.
- API text providers require per-task model IDs. The supported provider choices are
  DeepSeek, Kimi, MiMo, Qwen, OpenAI, native Anthropic and a compatible service.
  Explicit selection isolates each provider's key and endpoint. API access depends
  on the user's own account; subscriptions are not interchangeable API credentials.
- `models.provider: codex` uses the existing CLI login and optional `codex_model`;
  it does not need a new API key. Set an executable path when the CLI is not on PATH.
- Source type/fields, enabled flags and per-source limits are configurable. Source
  outages are reported/skipped; do not remove a subscription without user intent.
- `feedback.adaptive_exploration` can be disabled to keep the user's ratio fixed.
- Telegram receiving requires an explicit chat allowlist and the configured token
  environment variable. No sending endpoint is part of this workflow.
- Implicit preferences are opt-in and weaker than explicit good/bad feedback.
- Embeddings and illustrations are optional; preserve fallbacks instead of requiring
  model downloads for ordinary digest use.

Never print credentials. The Web UI stores entered keys in ignored `.env.local`
beside config; non-secret preferences and daily archives remain separate.

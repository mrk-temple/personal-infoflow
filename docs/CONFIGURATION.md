# Configuration / 配置

Start from `config.example.yaml`. The Web settings page edits a local preference file; it does not rewrite your YAML or change the daily archive directory. Precedence is: defaults → YAML → saved Web preferences. API credentials come from process environment / `.env` / `.env.local`; the local override file wins when it is present.

## Text providers

Choose `models.provider` explicitly when you have several providers. API modes require `models.profile` and `models.rank`; they can be different model IDs. Codex uses `models.codex_model`, or its own default when blank.

| Provider | Key variable | Endpoint override |
| --- | --- | --- |
| `deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL` |
| `kimi` | `KIMI_API_KEY` or `MOONSHOT_API_KEY` | `KIMI_BASE_URL` |
| `mimo` | `MIMO_API_KEY` | `MIMO_BASE_URL` |
| `qwen` | `QWEN_API_KEY` or `DASHSCOPE_API_KEY` | `QWEN_BASE_URL` |
| `openai` | `OPENAI_API_KEY` | `OPENAI_BASE_URL` |
| `anthropic` | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL` |
| `custom` | `CUSTOM_API_KEY` | `CUSTOM_BASE_URL` |
| `codex` | Existing CLI login | `models.codex_command` / `models.codex_model` |

`models.base_url` overrides the selected provider's endpoint variable. No other provider's key or URL is used as a fallback after an explicit selection. `auto` retains legacy detection order: MiMo, DeepSeek, Kimi, Qwen, Anthropic, custom, OpenAI. In this legacy mode, provider-specific `*_MODEL` can override YAML model IDs; explicit mode uses the per-task IDs in config.

For Qwen, endpoints depend on region/workspace; use the URL from your console, including `/compatible-mode/v1`. MiMo Token Plan may need a plan-specific endpoint. Model IDs and access depend on your own account. Examples are editable starting points, not a promise of access.

Codex CLI must be installed and signed in. `models.cli_workdir` contains ephemeral jobs' final responses, so place it on a private local disk. No API key variables are forwarded by the CLI adapter. Existing CLI account limits apply; this does not turn API billing into subscription billing.

## Reading mix and sources

- `digest.exploration_ratio`: 0–1. The Web slider uses percentages. The ratio governs slot selection; the number is not a per-story probability.
- `digest.max_items`: 1–100 per run. Same-day runs append, so a day can contain more than this number.
- `digest.max_per_source`: cap within a run; `0` means no cap. Too few qualifying candidates/sources can produce fewer stories.
- `feedback.adaptive_exploration`: optionally adjusts the ratio after sufficient explicit ratings. Uncheck it to keep your chosen ratio fixed.
- `sources[].limit`: 1–200 per source. Up to 100 configured sources. Disabled sources stay in configuration but are not fetched.

The source editor's target field means:

| Type | Target |
| --- | --- |
| `rss` | RSS/Atom URL |
| `hackernews` | None; set a fetch limit |
| `arxiv` | Category, e.g. `cs.AI` |
| `reddit` | Subreddit name |
| `googlenews` | Comma-separated queries |
| `github` | Optional topic; advanced language/since-days filters remain configurable in YAML |
| `youtube` | Comma-separated channel IDs or `@handles`; playlists are an advanced YAML option |
| `twitter` | Your RSSHub base URL, then `|`, then comma-separated handles |

Some services rate-limit unauthenticated requests. Run details show `ok`, empty or unavailable source outcomes without logging credential-bearing source URLs. Only published clusters' links become seen; candidates not selected remain eligible.

## Image backends

`portrait.provider`: `none`, `api`, `codex`, or `local`. `portrait.enabled` controls automatic generation when refreshing a profile; the manual portrait action is separate.

- **API**: set `portrait.base_url`, `portrait.model` and `IMAGE_API_KEY`. The adapter accepts PNG base64 or a returned image URL from an OpenAI-compatible generations endpoint. Endpoint-specific restrictions still apply.
- **Codex**: set `portrait.codex_command` if needed. Requires a CLI that exposes built-in image generation for the signed-in account. The prepared job requests `gpt-image-2`; import/app handoff is available when automation is unavailable.
- **Local**: Automatic1111 / Forge `POST /sdapi/v1/txt2img`; set the base URL and optionally a local checkpoint in `portrait.model`. Start the local service with its API enabled yourself. This is not a generic ComfyUI workflow executor.

Advanced image fields: `width`, `height`, `steps` (local), `timeout`, `style_hint`, and `prompt_override`. An override skips the text-model prompt step. Images are validated as PNG and archived with unique timestamps, alongside generation metadata. The latest one is viewable from the profile dialog.

## Signal layers and decay

- `profile.refresh_days`: stable profile TTL, default 7; `0` is manual-only.
- `profile.recent_days`: separates recent notes/projects from older background knowledge.
- `signals.chat_dir`: optional exported chat folder. Supported exports prefer user/human messages; generic JSON has a fallback parser.
- `signals.capture_path`: optional Markdown/text file or folder, merged with manual/Telegram captures.
- `signals.half_life_days`: recency annotation/filtering for chat and captures, default 30. Very old signals below 10% weight are omitted. Capture text is passed to the profile as dated, weighted context; these weights guide the model rather than multiplying text.
- `feedback.half_life_days`: numeric decay of explicit source/keyword bias, default 90; `0` disables decay. New/changed ratings use their rating time, including ratings on an old edition. Unchanged scans preserve that timestamp; legacy entries fall back to edition date. Precision statistics retain actual counts.
- `reading.implicit_feedback`: off by default. Saves contribute a weaker positive weight; visible, focused reading time starts contributing after 30 seconds. Opening a link, manually marking read and skipping a story do not imply approval/dislike.
- `reading.half_life_days`: implicit signal half-life, default 30. Explicit good/bad on the same date/link takes precedence.

The profile cache contains stable note-derived knowledge. Captures and current explicit likes/dislikes are appended afresh on every run, so clearing feedback does not remain baked into the new cache format.

## Telegram receiver

```yaml
telegram:
  enabled: true
  token_env: TELEGRAM_BOT_TOKEN
  allowed_chat_ids: [123456789]
  max_entries: 1000
```

Put the real token in an ignored env file. An empty allowlist is rejected before any request. The receiver handles message/edited-message text, captions and text-link entities, including allowed channels. Other chats are ignored but their update IDs are acknowledged. Captures and offset share one atomic JSON write; edits replace the same Telegram message and retries do not duplicate it.

Each invocation polls one batch of up to 100 updates without long-polling. Run it again to drain a backlog, or schedule normal CLI runs with your own task scheduler. No sending endpoint is used, and file attachments are not downloaded. Telegram retains updates only for its own retention window; this is not a backup service.

## Daily history, privacy and upgrades

`digest.output_dir/YYYY-MM-DD.md` is the daily archive. The date list is built from these actual files on every server start; the newest existing edition opens by default. Same-day runs append. Read-later state references the date and link, so saved stories from different editions can appear together.

Changing providers, source limits or the reading recipe does not move/delete the archive. If you deliberately change `digest.output_dir`, the reader will show the new directory; move/copy your earlier files yourself if you want them included there.

Notes, model prompts, captures, feedback, CLI outputs, images and API keys are private local data. Selected note/context text and candidate content are sent to the text provider you choose; image prompts go to the selected image service. Browser language and color preferences use localStorage for that origin, so another port/browser has its own display preferences.

Legacy versions anchored relative state paths inside the package. Keep explicit old paths or copy state into the config-adjacent `data/` directory before upgrading. Refresh the profile once after migration, retain original files until checked, and use one writer per configuration.

Optional fastembed model weights use `embedding.model_cache_path` (default `data/models` beside config), rather than an unspecified system cache. Embeddings are off in the example configuration until deliberately enabled.

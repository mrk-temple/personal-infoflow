# Design references / 改进依据

The project keeps its own warm-paper newspaper style and a local Markdown archive. These references informed concrete behavior; no upstream application code or screenshots were copied.

| Evidence | Applied here |
| --- | --- |
| [User report: issue #1](https://github.com/mrk-temple/personal-infoflow/issues/1) describes edited/cleared ratings being ignored. | Reconcile by `(date, link)` on every scan, remove marks no longer present, rebuild aggregate bias and add regression tests. Use one parser for Chinese and English editions. |
| [Miniflux features](https://miniflux.app/features.html) documents bookmarks, search, keyboard navigation, responsive reading and privacy-minded external links. | Cross-edition read later, title/reason/source search, unread state, keyboard controls, source/date filters, HTTP(S)-only links with `noopener noreferrer` and no referrer. |
| [FreshRSS](https://github.com/FreshRSS/FreshRSS) demonstrates user-controlled subscriptions in a self-hosted reader. | Enable/disable/add/remove sources, per-source limits, source failure isolation, and an archive that remains independent of model choice. |
| [Telegram Bot API](https://core.telegram.org/bots/api#getupdates) defines update offsets, message forms and polling constraints. | Allowlist before requesting, commit captures with offset, deduplicate retries/edits, acknowledge ignored updates, receive without sending. |
| [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) documents scoped execution, ephemeral sessions and final-message output. | A text-engine adapter that uses the signed-in CLI, a read-only job directory and no forwarded API key variables. It performs an application task, not repository modification. |
| [Codex image generation](https://learn.chatgpt.com/docs/image-generation) documents built-in `gpt-image-2`, account usage and API separation. | Optional CLI image jobs plus a reviewable App prompt/import path; API and local image services are separately selectable. CLI image availability is checked through actual output rather than assumed. |

Provider protocol references:

- [DeepSeek first API call](https://api-docs.deepseek.com/): compatible endpoint and editable model examples.
- [Kimi quickstart](https://platform.kimi.ai/docs/get-your-api-key): native service URL and OpenAI-compatible requests.
- [MiMo first API call](https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call): compatible API formats; plan-specific addresses remain configurable.
- [Qwen OpenAI compatibility](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope): region/workspace endpoint differences.
- [OpenAI image API](https://developers.openai.com/api/reference/resources/images/methods/generate): explicit model and image output fields.
- [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create): separate system content, message blocks and native authentication/version headers.

Additional code review findings addressed in this release:

1. Previously every fetched item became seen, even if ranking omitted it or it was not selected. Now only selected clusters do; invalid or incomplete model output fails without consuming candidates.
2. A long/missing feedback line could be ignored, and source metadata could drift between two parsers. These paths now share the same format rules and scan full item sections.
3. State was written directly, and config paths depended on package installation location. Writes now replace atomically, corrupt JSON is not silently overwritten, and config-relative paths work with installed packages.
4. RSS and article fetching could bypass the declared timeout; feed timestamps used host-local conversion. Requests now use shared bounds and UTC conversion.
5. Runtime details occupied reading space. Controls are compact, provider identity lives in Settings, and successful progress details collapse automatically.

The implementation is evaluated with protocol/unit tests and a separate real browser run. Those are distinct from per-provider account access, Telegram bot deployment, local GPU setup and audience acceptance; the exact evidence is in [RELEASE_CHECK.md](../RELEASE_CHECK.md).

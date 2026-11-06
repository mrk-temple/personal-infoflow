# Verification record · 0.3.0

Date: **2026-11-06**, Asia/Shanghai. Local automated checks, real service/browser
observations and user-configured integrations are recorded separately.

## Automated checks

- **94 tests**: edited/cleared/removed feedback, long/missing feedback fields, legacy duplicates, idempotence, independent state directories and archive retention. New ratings on old editions decay from rating time, without resetting on every scan.
- Real loopback HTTP tests: feedback, read later, dates, settings across a restarted server, origin/method guards, invalid input and scoped portrait paths.
- Provider credential/endpoint isolation, native Anthropic protocol, CLI text/image handoff, and image API/local SD adapters with bounded substitutes rather than paid account calls.
- Telegram allowlist/offset/edit/retry behavior, redacted failures, manual captures, signal decay, optional dwell and explicit-feedback precedence.
- Profile exclusions/live layers, model-output validation, English Markdown, published-only seen state and workspace-scoped embedding model cache.
- Ruff, both frontend JavaScript syntax checks, skill validation, wheel build/isolated installation, and packaged assets loaded outside the source directory.
- Public-source scan, staged diff review and exact comparison against known local credential values before upload; secret values are not printed.

CI is configured for Python 3.10/3.12 tests/lint, Node syntax, wheel build and public-source checks. Current results are in [GitHub Actions](https://github.com/mrk-temple/personal-infoflow/actions).

## Real data and CLI runs

Only public, generic sample interest notes were used, not the owner's private vault.
`examples/demo-config.yaml` reproduces this kind of run. Live feeds change; exact
headlines and counts below are dated observations.

| Run | Observed result |
| --- | --- |
| Retrieval | Hacker News 10, Quanta Magazine 5, Ars Technica 6: 21 unique candidates from three working sources. |
| Chinese ranking | Signed-in Codex CLI completed both batches and wrote six real stories spanning three selected sources to daily Markdown. |
| English profile/ranking | Signed-in CLI built the profile and ranked live candidates; six real stories spanning two selected sources were written with English reasons. |
| CLI image | One real 1024×1024 PNG, 2,117,057 bytes, generated from a public visual prompt, timestamped, decoded for visual inspection and displayed in the profile dialog. |
| CLI environment | `codex-cli 0.166.0-alpha.6`; login status reported ChatGPT authentication. No new OpenAI API key was created. |

An earlier MiMo run built the public sample Chinese profile and fetched the feeds,
but its ranking output did not parse as valid JSON. No fake digest or consumed seen
state resulted. After the user chose CLI instead of paid API setup, the successful
runs above used CLI; MiMo ranking was not re-tested or claimed fixed.

## Browser observations

- Removed model identity from the masthead; compact controls and exactly two persistent paper colors.
- English/Chinese controls, navigation, placeholders, errors and settings; new reasons follow the selected language, while existing articles retain theirs.
- Actual good→bad→clear sequence, including withdrawal of learned state. Read stories disappear from unread and remain available in read later.
- Settings changed to 50% exploration, eight stories, adaptive ratio off and HN limit 12. Restart restored all four choices, the existing six-story archive and saved/read states.
- Search `AI` returned two stories; Quanta filtering returned three. The page used real feed output, not fixture replacements.
- Actual widths: 1265px three-column, 805px two-column and 375px single-column client areas. Narrow/wide DOM checks found no horizontal overflow.
- The generated PNG loaded through the scoped route; profile Markdown displayed with safe formatting.

| Screenshot | Content |
| --- | --- |
| [Chinese warm paper](docs/screenshots/daily-zh-warm.jpg) | Actual archive, compact controls, saved/read state and editable recipe. |
| [English monochrome](docs/screenshots/daily-en-mono.jpg) | Real English output filtered to Quanta Magazine. |
| [Settings](docs/screenshots/settings-zh.jpg) | Persisted user-chosen limits, ratio and CLI options. |
| [Search](docs/screenshots/search-zh.jpg) | Real `AI` query with two matches. |
| [Profile](docs/screenshots/profile-zh.jpg) | Public sample profile and actual CLI-generated image. |
| [Narrow view](docs/screenshots/mobile-en.jpg) | English single-column layout. |
| [First open](docs/screenshots/first-open-zh.jpg) | Genuine empty state with the shipped demo config. |

## Verification limits

No live Telegram bot token or local SD/Forge server was used. Their protocol,
persistence and error paths passed local tests; live access needs each user's setup.
OpenAI, Anthropic, Qwen, Kimi and custom paid accounts were not called live in this
pass. Optional embedding weights were not downloaded.

CLI image availability/quotas depend on the installed version/account; App prompt/import
handoff is available when that tool is missing. This is a local single-user reader,
not a public authenticated service. Keep backups and use one writer per configuration.

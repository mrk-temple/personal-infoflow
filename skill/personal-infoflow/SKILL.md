---
name: personal-infoflow
description: >-
  Run the user's local Personal InfoFlow newspaper: build an interest profile from
  configured notes, gather and rank stories, write daily Markdown, and reconcile
  good/bad feedback. Use for today's personal digest, updating an interest profile,
  saving a reading signal, or syncing ratings (今天的信息流、日报、画像、反馈).
  Use ordinary search tools for unrelated one-off web searches.
---

# Personal InfoFlow

Use the installed repository and its shared CLI; preserve the user's chosen provider,
sources, language, image backend and output directory. Do not replace their settings
with a preferred model or create a new API key to run an already configured workflow.

## Entry points

`scripts/run.py` and `scripts/run.sh` locate the repository/interpreter and forward
arguments to `python -m infoflow`. Repository resolution uses `INFOFLOW_HOME`, the
script's repository-relative location, then the installer-written `scripts/home_path`.
Interpreter resolution uses `INFOFLOW_PYTHON`, the repository environment, then system Python.

| User intent | CLI arguments |
| --- | --- |
| Today's personal newspaper | No extra arguments |
| Rebuild profile and make an edition | `--refresh-profile` |
| Sync good/bad/cleared ratings only | `--feedback` |
| Generate English reasons | `--language en` |
| Save text or a link as an interest signal | `--capture "user-provided text"` |
| Receive configured Telegram messages | `--telegram-sync` |
| Open the local reader | `--web` |
| Generate a requested illustration | `--portrait`; read the image reference first |

Use `--config PATH` for the user's chosen config. Paths are config-relative, and
saved Web settings can override non-secret YAML preferences. Read
[configuration](references/configuration.md) when setup, provider or path decisions matter.

## Run and report

Run the requested action using the existing environment. If dependencies or CLI
authentication are missing, report the concrete failure and consult
[troubleshooting](references/troubleshooting.md); do not silently switch to a paid API
or install an image model to work around it.

For a successful edition, read the new daily section from `digest.output_dir` and
summarize a few worthwhile stories with their links/reasons. Same-day runs append;
never rewrite earlier editions to simplify the response. A successful run with no
new stories does not imply a new daily file was created.

Feedback is editable and reversible. Web good/bad/clear writes Markdown and updates
learned state immediately; hand edits synchronize on the next feedback/digest run.
Do not reinterpret a read/save state as an explicit rating.

The browser supports English/Chinese and warm/monochrome modes. Settings include
the recommendation mix, story/source limits, providers and optional illustrations.
The server is long-running; if starting it in the background, report its local URL
and retain the process only for the user's requested use.

## Optional illustrations and privacy

Generate only when requested or enabled in the user's configuration. Image API,
signed-in Codex CLI and local SD/Forge are separate choices; details and App handoff
are in [portrait](references/portrait.md). Keep earlier timestamped images.

Notes, captures, feedback, profiles, credentials and CLI outputs are local user data.
Use only the configured provider and scope. Do not copy them into an agent memory,
public repository, screenshots or another service unless the user asks for that use.

# 修改日志

本项目的所有显著改动记录于此。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)，
版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-11-06

### Fixed

- Reconcile changed, cleared and deleted feedback by date/link; repair legacy duplicate records and recalculate all learned state. Fixes #1.
- Update feedback beyond short item sections, create independent state directories, and share a Chinese/English Markdown parser with the reader.
- Mark only selected duplicate clusters seen; malformed/incomplete model output no longer silently consumes candidates.
- Use bounded RSS/full-text requests and UTC feed dates; persist local state atomically and report corrupt JSON without replacing it.
- Keep mutation APIs POST-only and reject cross-origin requests with bounded JSON bodies.

### Added

- Full English/Chinese UI and READMEs; persistent warm-paper/monochrome themes and compact reading controls.
- User-selectable DeepSeek, Kimi, MiMo, Qwen, OpenAI, native Anthropic, compatible service or signed-in Codex CLI. Explicit providers never borrow another provider's credentials.
- Persisted local settings for the reading ratio, optional adaptation, story/source limits, sources, models and image backends. Daily archives are preserved.
- Search, source filters, history selection, read/unread, cross-edition read later and keyboard controls.
- Allowlisted, retry-safe Telegram capture plus manual capture; local implicit preferences remain opt-in and weaker than explicit ratings.
- Long-term/recent profile layers, configurable signal decay and exclusions for generated notes.
- Optional image API, Codex CLI or local SD/Forge; timestamped PNG archives, profile preview and App handoff/import.
- Real bilingual feed/CLI screenshots and a reproducible public-note demo configuration.

### Migration

- Relative state paths now follow the config file. Retain explicit old `infoflow/data/` paths or copy state to config-adjacent `data/`.
- Refresh the profile once to rebuild the older feedback-containing cache. Back up the vault and state before upgrading.

## Earlier Web preview / 既有 Web 功能

### 新增：Web 界面

- **`python -m infoflow --web`**（装包后 `infoflow --web`）→ 浏览器打开 `http://127.0.0.1:7781`。
  极简实现：后端是标准库 `http.server`（`infoflow/web.py`），前端是一张无框架、无构建的
  单页（`infoflow/webapp/`），**零新增依赖**。
- **跑一轮**：网页上点「跑一轮 / 重建画像并跑一轮 / 只收集反馈」，后台线程调同一份
  `pipeline.run`，进度行实时推送到页面；同一时刻只允许一轮在跑。
- **读简报**：解析当日 markdown 成结构化条目渲染（贴合/拓展标签、来源、"也被 N 个源报道"）。
- **标反馈**：点「好/差」直接写回简报的 `反馈::` 行（新增 `feedback.set_verdict()`）——
  与用户在 Obsidian 里手写完全等效，vault 里的 markdown 仍是唯一事实源，反馈引擎零改动复用。
  再点一次可取消。
- 默认只监听 `127.0.0.1`，可用 `--web-host/--web-port` 改。
- 新增 `tests/test_web.py`（解析、set_verdict 写回、RunState 并发保护）。

## [0.2.0] - 2026-06-16

把原型整理成一个像样的工程，并把 skill 改造成**与 agent 无关、可移植**的形态。
功能行为保持不变（同一套管线、同样的产出），改的是结构、健壮性与可维护性。

### 新增（项目工程化）

- **打包**：新增 `pyproject.toml`，可 `pip install -e .` 安装；提供 `infoflow` 控制台命令
  （`[project.scripts]`）；`[embed]` / `[dev]` 两个可选依赖组。
- **可执行模块**：新增 `infoflow/__main__.py`，支持 `python -m infoflow`（不再需要 `.main`）。
- **测试**：新增 `tests/`，18 个纯逻辑单测覆盖 JSON 抽取、标题/语义去重、反馈解析与聚合、
  简报 3:7 选条、配置加载与校验（无需网络/API）。
- **CI**：新增 `.github/workflows/ci.yml`，在 3.10/3.12 上跑 ruff + pytest。
- **文档**：新增 `docs/ARCHITECTURE.md`（数据流 + 模块职责表）、本 `CHANGELOG.md`、`.editorconfig`。

### 变更（代码结构与健壮性）

- **配置集中化**：新增 `infoflow/config.py`，`load_config()` 合并缺省值（`DEFAULTS`）并做最小
  校验——缺关键项时报一句人话，而不是在深处抛 `KeyError`。路径解析 `resolve()` 从 `client.py`
  迁到这里。
- **`client.py` 收敛职责**：只保留"和模型说话"（建 client / `chat` / `extract_json`），不再混入
  路径工具。`extract_json` 对 `None`/空输入更健壮。base_url 可用 `DEEPSEEK_BASE_URL` 覆盖。
- **HTTP 集中化**：新增 `infoflow/http.py`，统一 User-Agent / 超时 / 读取上限 / GET·POST JSON。
  `sources.py`、`enrich.py`、`embed.py`、`portrait.py` 原本各写一份 urllib，现统一调用。
- **去掉跨模块私有引用**：`semantic.py` 不再 `import feedback._state`，改用新公开函数
  `feedback.load_state()`。
- **日志**：引入标准 `logging`，`sources.py` / `profile.py` 的零散 `print` 改为模块级 logger；
  `main.py` 统一配置（走 stdout、纯消息格式，与原观感一致），并把 openai/httpx 的 INFO 噪音
  （"HTTP Request: POST ..."）压到 WARNING。新增 `-v/--verbose` 开关。

### Skill：改造成与 agent 无关、可移植

- **统一两份分叉副本**：仓库内 `skill/` 与已安装的 `~/.claude/skills/` 此前实现不一致
  （一个用 `INFOFLOW_HOME`/`INFOFLOW_PYTHON`，一个硬编码绝对路径）。现统一为同一套可移植入口。
- **可移植入口**：`scripts/run.sh` 与 `scripts/run.py` 自动解析仓库根
  （`INFOFLOW_HOME` → 脚本相对位置 → `install.sh` 写的 `home_path`）与解释器
  （`INFOFLOW_PYTHON` → `<repo>/.venv/bin/python` → `python3`），去掉所有硬编码路径与
  对特定 agent 的依赖。
- **安装脚本**：新增 `skill/personal-infoflow/install.sh`，一条命令装到任意 agent 的 skills
  目录（默认 Claude Code 的 `~/.claude/skills`），并写下 `home_path` 让仓库外副本也能找回仓库。
- **SKILL.md 去 Hermes 化**：描述/触发词保留，正文改为 agent 无关、祈使句式；细节按渐进披露
  拆到 `references/configuration.md`、`references/troubleshooting.md`、`references/portrait.md`，
  让 SKILL.md 更精简。

### 验证

- `pytest`：18 passed。
- 端到端实跑（`python -m infoflow`、`run.sh`、`run.py`、装到 `~/.claude/skills` 的副本）均
  退出 0、产出符合预期；所用为隔离的临时 config（不写用户 vault、不动用户状态）。
- 确认 `config.yaml` 里的 `deepseek-v4-pro` / `deepseek-v4-flash` 是该端点 `models.list()` 实有
  的模型名（**非笔误**），故未改动。

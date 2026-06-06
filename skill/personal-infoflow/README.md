# Hermes skill：personal-infoflow

把这套信息流接到 Hermes Agent，用一句话触发。

## 安装

1. 确保本机已克隆 personal-infoflow 仓库、配好 `config.yaml` 和 `.env`，并能在它的虚拟环境里跑通 `python -m infoflow.main`。
2. 设两个环境变量（写进 `~/.hermes/.env`）：
   - `DEEPSEEK_API_KEY=...`
   - `INFOFLOW_HOME=/绝对路径/personal-infoflow`
3. 把本目录（`infoflow/`）放到 Hermes 的 skills 目录下：
   ```
   cp -r skill/personal-infoflow ~/.hermes/skills/productivity/personal-infoflow
   ```
   （或用 `hermes skills install` 指向托管的 SKILL.md。）
4. 验证：
   ```
   hermes chat --toolsets skills -q "用 infoflow 给我今天的信息流"
   ```

## 说明

- skill 通过 `scripts/run.py` 调用仓库里的核心管线（`infoflow.pipeline.run`）——逻辑与本地 CLI 完全同一份。
- 画像存储、出图（Codex OAuth + gpt-image-2）、Telegram 推送等更深的 Hermes 原生集成是后续迭代。

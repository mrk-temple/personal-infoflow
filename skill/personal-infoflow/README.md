# Skill：personal-infoflow

把 personal-infoflow 这套本地管线封成一个**与 agent 无关**的 skill：任何能执行 shell 或
Python 的 agent（Claude Code / Hermes / 其它）都能用同一套入口脚本一句话触发。

## 前置

先在仓库根把环境配好、能跑通：

```bash
cd <仓库根>
python -m venv .venv && .venv/bin/pip install -e .   # 或 pip install -r requirements.txt
cp .env.example .env && $EDITOR .env                  # 填 DEEPSEEK_API_KEY
cp config.example.yaml config.yaml && $EDITOR config.yaml
.venv/bin/python -m infoflow --feedback               # 自测
```

## 安装到 agent

```bash
# 默认装到 Claude Code 的 ~/.claude/skills
skill/personal-infoflow/install.sh

# 或指定其它 agent 的 skills 目录（如 Hermes）
skill/personal-infoflow/install.sh /path/to/hermes/skills
```

`install.sh` 会把 `SKILL.md / scripts / references` 复制到 `<目标>/personal-infoflow/`，并写下
`scripts/home_path` 记录本仓库根——这样即便 skill 被装到仓库外，入口脚本也能找回仓库。

## 入口

- `scripts/run.sh` —— shell 入口
- `scripts/run.py` —— Python 入口（等价）

两者自动解析仓库根（`INFOFLOW_HOME` → 脚本位置 → `home_path`）与解释器
（`INFOFLOW_PYTHON` → `<仓库>/.venv/bin/python` → `python3`），再透传参数给 `python -m infoflow`。

```bash
scripts/run.sh                    # 今天的简报
scripts/run.sh --refresh-profile  # 重建画像 + 简报
scripts/run.sh --feedback         # 只收反馈、看命中率
```

逻辑与本地 CLI 完全同一份（`infoflow.pipeline.run`）。详见 `SKILL.md` 与 `references/`。

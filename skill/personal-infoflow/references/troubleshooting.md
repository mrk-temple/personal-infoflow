# 常见坑（Troubleshooting）

## 首次运行慢

开了 `fetch.full_text` 会逐篇抓正文；开了 embedding 首次会下载约 130MB 模型。属正常，
耐心等。想快可让用户在 `config.yaml` 临时设 `fetch.full_text: false`、`embedding.enabled: false`。

## 语义去重没生效

仓库 `.venv` 若未装 `fastembed`，`embedding` 层会**自动回退到标题去重**（不报错）。想要真正
的语义去重 + "更多类似"，在仓库 `.venv` 里 `pip install fastembed`（它要 numpy<2，别和其它
项目共用环境）。也可装 `pip install -e ".[embed]"`。

## 找不到 python / ModuleNotFoundError

入口脚本按 `INFOFLOW_PYTHON` → `<仓库>/.venv/bin/python` → `python3` 解析解释器。报这个错
通常是 `.venv` 未建好或依赖没装。**不要**自己新建环境或装依赖，照实告诉用户按仓库 README
配好环境（`python -m venv .venv && .venv/bin/pip install -e .`）。

## 找不到仓库根

入口脚本按 `INFOFLOW_HOME` → 脚本相对位置 → `scripts/home_path` 解析仓库根。若 skill 被装到
仓库外（如 `~/.claude/skills`）且没跑过 `install.sh`，就会找不到。解决：设 `INFOFLOW_HOME`
环境变量，或在仓库里跑 `skill/personal-infoflow/install.sh` 重新安装（它会写下 `home_path`）。

## 来源抓取失败

Reddit 未登录常被限流、RSSHub 公共实例不稳、偶发网络 reset——单个源失败会被捕获并跳过，
不影响其它源和整轮成功。日志里会有 `[type] xxx 抓取失败（跳过）：...`。

## 同一天多次跑

简报是**追加**到当天文件、不覆盖；已读内容（记录在 `data/seen.json`）不会重复出现，所以追加段
可能很短甚至为空（没有新内容）——这是正常的。

## 配图失败 / 402

管线内置的 Pollinations 出图已收费，故 `portrait.enabled` 默认 false。配图改由 agent 的图像
工具完成（见 `references/portrait.md`），没有就跳过，不影响简报。

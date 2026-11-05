---
name: personal-infoflow
description: >-
  生成个性化信息流日报。读用户的 Obsidian 笔记与 AI 对话建立兴趣画像，从多源
  （HN/arXiv/GitHub/Reddit/RSS/Google News/YouTube）抓取、语义去重、按"3 贴合 : 7 开眼界"
  排序，写一篇简报到用户的 Obsidian vault，并按用户在简报里标的"好/差"反馈持续进化。
  当用户说"今天的信息流 / 跑一下简报 / 我今天该看什么 / 更新我的画像 / 收一下反馈 / 看看命中率"
  等时使用。
---

# personal-infoflow

用一句话触发本地 personal-infoflow 管线，跑完把精选结果口头讲给用户，并按反馈进化。
本 skill 与 agent 无关：任何能执行 shell 或 Python 的 agent 都可用同一套入口脚本驱动。

## 何时使用（When to Use）

- 用户想要"今天的信息流 / 日报 / 简报"、"我今天该看点什么"
- 用户说"更新 / 重建我的画像"（笔记或兴趣有较大变化时）
- 用户说"收一下我的反馈 / 看看命中率"
- **不要**用于：与个性化内容推荐无关的一次性网页搜索（那直接用 agent 自带的 web 工具）

## 入口脚本（与 agent 无关）

所有动作都通过仓库里同一份核心管线完成，由可移植入口脚本驱动：

- `scripts/run.sh` —— 偏好 shell 的 agent（Claude Code 等）
- `scripts/run.py` —— 偏好直接调 Python 的 agent（Hermes 等）

两者等价：会自动解析**仓库根**与**解释器**，再把 CLI 参数透传给 `python -m infoflow`。

解析顺序（无需手配，装好即用）：
- 仓库根：环境变量 `INFOFLOW_HOME` → 脚本在仓库内的相对位置 → `install.sh` 写下的 `scripts/home_path`
- 解释器：环境变量 `INFOFLOW_PYTHON` → `<仓库>/.venv/bin/python` → 系统 `python3`

| 用户意图 | 命令 |
| --- | --- |
| 出今天的简报 | `scripts/run.sh` |
| 重建画像 + 简报 | `scripts/run.sh --refresh-profile` |
| 只收集反馈、看命中率 | `scripts/run.sh --feedback` |

用户若想在浏览器里操作（跑一轮、读简报、点「好/差」），可启动 Web 界面：
`scripts/run.sh --web`，然后告诉用户打开 `http://127.0.0.1:7781`（该命令会一直前台运行，
Ctrl+C 停止；agent 应把它放到后台并如实告知）。

**不要**自己新建虚拟环境或 `pip install`——用入口脚本即可。若报 `ModuleNotFoundError`
或找不到 python，说明仓库 `.venv` 未配好或 `INFOFLOW_HOME` 没指对：照实告诉用户，
让其按仓库 README 配环境，而不要自行装依赖。详见 `references/troubleshooting.md`。

## 步骤（Procedure）

1. 跑对应命令（见上表）。管线内部依次：收集上轮反馈 → 加载/重建画像 → 抓取多源 →
   语义去重 → 打分 → 把简报**追加**写入用户 Obsidian vault。
2. 命令成功（退出码 0）后，找到当天的简报文件：`config.yaml` 里 `digest.output_dir`
   下的 `YYYY-MM-DD.md`。读取**本轮新追加的那一段**（以本次时间戳 `🕐 HH:MM` 开头）。
3. 给用户一个**简短口头摘要**：今天精选几条、贴合/拓展各几条、命中率，并点出 2–3 条
   最值得看的（标题 + 一句为什么）。**不要**复述整篇简报——它已写进 vault。
4. 若反馈汇总里出现"建议下线"的来源，转告用户、问是否要从 `config.yaml` 的 `sources` 去掉。
5. 主动提醒用户：在简报里每条的 `反馈::` 后写 `好` 或 `差`，下次运行会自动学习。

## 画像配图（可选，需图像生成工具）

管线只更新画像**文字**（`<仓库>/infoflow/data/profile.md`），不出图
（`config.yaml` 里 `portrait.enabled` 保持 false）。若当前 agent 有可用的图像生成工具，
在跑完 `--refresh-profile` 后，可据画像文字配一张隐喻气质的图存进 vault。
完整出图规范见 `references/portrait.md`。没有图像工具就跳过本节，只更新文字。

## 与记忆配合（Memory）

- 工具的"兴趣画像"是它自己的状态，存在 `infoflow/data/profile.md`。
- 当用户透露**稳定的**长期兴趣、目标或明确好恶时，除了让工具下次重建画像，也把这类事实
  写进当前 agent 的长期记忆，让画像与核心记忆互相印证。skill 负责"怎么跑"，记忆负责
  "关于用户已确定了什么"。

## 如何判断成功（Verification）

- 命令退出码为 0，且 `digest.output_dir` 下当天的 `.md` 文件存在并含本轮时间戳段（`🕐 HH:MM`）。
- 失败时命令会在末尾打印是哪一步出的错；把该信息**如实**转达用户，不要假装成功。

## 进一步参考（References）

- `references/configuration.md` —— config.yaml 各项、内容源类型、模型与 embedding 设置
- `references/troubleshooting.md` —— 常见坑：首次慢、来源限流、环境/依赖、同日追加
- `references/portrait.md` —— 画像配图的完整提示词与归档规范
- 安装到其它 agent：在仓库里运行 `skill/personal-infoflow/install.sh [目标skills目录]`

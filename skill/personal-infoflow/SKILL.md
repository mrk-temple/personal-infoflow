---
name: personal-infoflow
description: >-
  生成个性化信息流日报。读用户的笔记与 AI 对话建立兴趣画像，从多源（HN/arXiv/GitHub/RSS/Google News/YouTube）
  抓取、语义去重、按"3 贴合 : 7 开眼界"排序，写一篇简报到用户的 Obsidian，并按用户在简报里标的"好/差"反馈进化。
  当用户说"今天的信息流 / 跑一下简报 / 我该看什么 / 更新我的画像 / 收一下反馈"等时使用。
required_environment_variables:
  - DEEPSEEK_API_KEY
  - INFOFLOW_HOME
---

# personal-infoflow

把 personal-infoflow 这套本地管线接到 Hermes 里：用一句话触发，跑完把精选结果讲给用户，并按用户反馈持续进化。

## 何时使用（When to Use）

- 用户想要"今天的信息流 / 日报 / 简报"、"我今天该看点什么"
- 用户说"更新 / 重建我的画像"（笔记或兴趣有较大变化时）
- 用户说"收一下我的反馈 / 看看命中率"
- 不要用于：与个性化内容推荐无关的一次性网页搜索（那直接用 web 工具）

## 快速参考（Quick Reference）

所有动作都通过仓库里的核心管线完成。前置：`INFOFLOW_HOME` 指向 personal-infoflow 仓库根目录，`INFOFLOW_PYTHON` 指向**已装好依赖的虚拟环境的 python**（例如 `~/infoflow-venv/bin/python`）。

**重要：必须用 `$INFOFLOW_PYTHON` 来跑，不要用系统 `python`/`python3`，也不要自己新建虚拟环境或装依赖——环境已经由用户配好。** run.py 会自动使用 `$INFOFLOW_PYTHON`。

| 用户意图 | 命令 |
| --- | --- |
| 出今天的简报 | `"$INFOFLOW_PYTHON" "$INFOFLOW_HOME/skill/personal-infoflow/scripts/run.py"` |
| 重建画像 + 出图 + 简报 | `"$INFOFLOW_PYTHON" "$INFOFLOW_HOME/skill/personal-infoflow/scripts/run.py" --refresh-profile` |
| 只收集反馈、看命中率 | `"$INFOFLOW_PYTHON" "$INFOFLOW_HOME/skill/personal-infoflow/scripts/run.py" --feedback` |

如果某个命令报 `ModuleNotFoundError` 或找不到 python，**不要尝试创建环境或安装依赖**，而是直接告诉用户：`INFOFLOW_PYTHON` 没设对，请指向已装依赖的虚拟环境。

## 步骤（Procedure）

1. 确认 `INFOFLOW_HOME` 已设置，且该目录下存在 `config.yaml`（没有就提示用户先按仓库 README 配置）。
2. 运行对应命令（见上表）。命令内部会依次：收集上轮反馈 → 加载/重建画像 → 抓取多源 → 语义去重 → 打分 → 把简报追加写入用户的 Obsidian。
3. 命令成功后，找到当天的简报文件（`config.yaml` 里 `digest.output_dir` 下的 `YYYY-MM-DD.md`），读取**本轮新追加的那一段**。
4. 给用户一个**简短口头摘要**：今天精选几条、贴合/拓展各几条、命中率，并点出 2-3 条最值得看的（标题 + 一句为什么）。不要把整篇简报复述出来——它已经写进 vault 了。
5. 如果上一步反馈汇总里出现"建议下线"的来源，转告用户、并询问是否要从 `config.yaml` 的 `sources` 里去掉。
6. 主动提醒用户：在简报里每条的 `反馈::` 后写 `好` 或 `差`，下次运行会自动学习。

## 画像配图（用 Hermes 自己的生图工具，不靠管线）

管线只负责更新画像**文字**（`<INFOFLOW_HOME>/infoflow/data/profile.md`）。配图由你（Hermes）用 `image_generate` 工具出，原因：本地管线接的 Pollinations 已收费（402）。

当用户要"新画像 / 重建画像 / 给我画像配图"时，在管线跑完 `--refresh-profile` 之后：

1. 读取 `<INFOFLOW_HOME>/infoflow/data/profile.md`，理解这个人**与信息、知识的关系是什么气质**（构建者 / 编织者 / 探索者……）。
2. 写一句**英文**绘画提示词：用场景、光线、象征物来隐喻这种气质，**不要罗列他在学的具体学科或模型名**（不要出现 textbook / ResNet / calculus 这类词），画面克制、有留白、不画真人肖像，带风格词（如 minimal illustration, soft light, atmospheric）。
3. 用 `image_generate` 工具按该提示词出图。
4. 把图保存到用户 vault 的简报目录，文件名带时间戳：`<vault>/信息简报/portrait-YYYYMMDD-HHMM.png`（vault 简报目录见 config.yaml 的 `digest.output_dir`；当前是 `D:\Learn_note\Obsidian Vault\信息简报`）。
5. 把这次配图追加进成长档案 `<vault>/信息简报/兴趣画像.md`：一段 `## 🕐 时间戳` + `![[portrait-时间戳.png]]` + 提示词，**追加不覆盖**，让用户能看到一张张的蜕变。
6. 简短告诉用户出了新图、存在哪，并一句话说这次画像相比上次的变化。

不要再依赖管线里的 Pollinations 出图（`config.yaml` 里 `portrait.enabled` 应保持 false）。

## 与记忆配合（Memory）

- 这套工具的"兴趣画像"存在仓库的 `data/profile.md`。当用户在对话里透露新的长期兴趣、目标或明确的好恶时，除了让工具下次重建画像，也应把这类**稳定事实**写进 Hermes 的 USER.md（例如"用户在做信息流 + 多智能体方向"），让画像与核心记忆互相印证。
- skill 负责"怎么跑"，USER.md 负责"关于用户已确定了什么"，两者叠加。

## 常见坑（Pitfalls）

- **首次运行慢**：会下载嵌入模型（约 130MB）并逐篇抓正文。属正常，耐心等；想快可让用户在 `config.yaml` 临时设 `fetch.full_text: false`、`embedding.enabled: false`。
- **配图 402 / 失败**：Pollinations 免费额度政策多变，配图失败会自动跳过，不影响简报。可让用户设 `portrait.enabled: false`。
- **同一天多次跑**：简报是**追加**到当天文件、不覆盖；已读内容不会重复出现，所以追加段可能很短甚至为空（没有新内容）。这是正常的。
- **依赖与环境**：必须在仓库的虚拟环境里跑（fastembed 需要 numpy<2，别和用户的其它项目共用环境）。

## 如何判断成功（Verification）

- 命令退出码为 0，且 `digest.output_dir` 下当天的 `.md` 文件存在并包含本轮时间戳段（`🕐 HH:MM`）。
- 失败时命令会在末尾打印是哪一步出的错；把该信息转达用户，不要假装成功。

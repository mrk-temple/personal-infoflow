# personal-infoflow

## 源码版使用说明 · 2026-11-05

Python 3.10+：`python -m pip install -e ".[dev]"`，复制 `.env.example` 和 `config.example.yaml` 为本地配置；`python -m infoflow --web` 打开界面。

画像会读取你配置的笔记，远程模型会接收任务需要的内容。公开仓库不包含个人 vault 路径、兴趣画像、反馈或密钥；自动采集需要网络。

本次检查：32 项测试和内嵌浏览器脚本语法检查通过。 详细范围见 [验证与后续工作](RELEASE_CHECK.md)。敏感信息规则见 [SECURITY.md](SECURITY.md)。

一个长在你 Obsidian 里的个性化信息流。它读你的笔记建立"兴趣画像"，从多个来源抓内容，用大模型按 **3 贴合 : 7 开眼界** 的配方筛选，每天写一篇简报回你的 vault——你在简报里随手标个"好/差"，它下次就更懂你。

没有新 App，没有又一个要登录的网站。**Obsidian 就是界面**，一篇 markdown 就是交付，编辑那篇 markdown 就是反馈。

> 示例产出见 [`examples/sample-digest.md`](examples/sample-digest.md)。

## 它解决什么

主流推荐要么把你关进回音壁，要么是无差别的热榜。这个项目的赌注是：**真正的个性化是一个"你"的模型 + 一道狠筛**——难的不是抓内容，是有底气地扔掉 95%。所以它刻意保留拓展位，每天强行塞几条你舒适区之外、但邻近的内容，避免越看越窄。

## 工作原理

1. **画像**：读 Obsidian 笔记（+ AI 对话记录 + 你的历史反馈）→ 一份会进化的兴趣档案
2. **获取**：多类型源——RSS / Hacker News / Reddit / arXiv / Google News / GitHub 新热 / YouTube 频道
3. **去重**：本地 embedding 把同一事件的不同标题语义聚合，只留一条代表
4. **排序**：模型给每条打"相关性"和"拓展性"两个分；可选抓取正文让打分更准
5. **配方**：简报按 3:7 选条（贴合按相关性、拓展按开眼界分），命中率低时自动微调比例
6. **交付**：写一篇当日简报进 vault（同一天多次跑则追加不覆盖）；也可在 Web 界面里直接看
7. **反馈**：你标"好/差"（Obsidian 里写，或网页上点）→ 自动调整来源权重、关键词偏置和画像，越用越准

## 两种用法

**A. Web 界面（最省事）**

```bash
python -m infoflow --web        # 打开 http://127.0.0.1:7781（装包后也可用 `infoflow --web`）
```

浏览器里跑一轮、读当日简报、点「好/差」标反馈，进度实时可见。极简实现：标准库
`http.server` + 一张无框架单页（零新增依赖），默认只监听本机。

**B. 本地 CLI**

```bash
git clone <your-repo-url> && cd personal-infoflow
python -m venv .venv && source .venv/bin/activate
pip install -e .                     # 或 pip install -e ".[embed]" 装上本地语义层

cp .env.example .env                 # 填入 MIMO_API_KEY
cp config.example.yaml config.yaml   # 改 vault 路径、内容源

python -m infoflow --refresh-profile   # 首次：建画像 + 出简报
python -m infoflow                      # 之后每天跑（装包后也可直接用 `infoflow`）
python -m infoflow --feedback           # 只汇总反馈，不抓取
python -m infoflow -v                   # 加 -v 看更详细日志
```

挂到 cron / 计划任务里每天自动跑即可。

**C. 作为 agent skill（与 agent 无关）**

核心逻辑与 CLI 共用一份。skill 入口脚本会自动定位仓库与解释器，任何能跑 shell 或 Python 的
agent（Claude Code / Hermes / 其它）都能用。一条命令装好：

```bash
skill/personal-infoflow/install.sh                 # 默认装到 ~/.claude/skills（Claude Code）
skill/personal-infoflow/install.sh /path/to/skills # 或装到其它 agent 的 skills 目录
```

装好后对 agent 说"给我今天的信息流"即可。详见 [`skill/personal-infoflow/README.md`](skill/personal-infoflow/README.md)。

## 配置要点（全在 `config.yaml`）

Web 版采用暖纸色、宋体报头和分栏阅读布局，可按「贴合兴趣 / 开眼界」切换栏目。

MiMo 接入：在本地 `.env` 设置 `MIMO_API_KEY`、`MIMO_BASE_URL`、`MIMO_MODEL`。
默认使用 `https://api.xiaomimimo.com/v1` 和 `mimo-v2.6-pro`；Token Plan 使用控制台
提供的专属地址和密钥。配置后重启服务，页顶会显示供应商与模型。
密钥由 Python 服务端读取，浏览器只收到是否已配置的状态。
`MIMO_API_KEY` 非空时，所有模型任务优先使用这组配置，避免沿用旧网关地址与模型；
未设置时仍兼容原有 `DEEPSEEK_*` / `OPENAI_*`。
接口说明见 [MiMo 官方文档](https://mimo.mi.com/docs/en-US/quick-start/summary/first-api-call)。

- `sources`：内容源列表，面越宽越好。`googlenews` 那条专门用来主动拉"邻近但你没接触过"的主题；`youtube` 可填频道 ID 或 `@handle`（自动解析）。
- `digest.exploration_ratio`：开眼界占比，默认 0.7（即 3:7）。
- `embedding`：本地向量层（语义去重 +"更多类似"），需 `pip install fastembed`；不装会自动回退标题去重。
- `fetch.full_text`：是否抓正文再打分（更准但更慢）。
- `feedback.*`：反馈对来源/关键词权重的影响力度、自适应比例开关。
- 中文平台（知乎 / 公众号 / 豆瓣 / X）没有公开 API，用 [RSSHub](https://docs.rsshub.app) 转成 RSS 后当普通 `rss` 源接入；公共实例常限流，建议自建。

## 注意事项

- **隐私**：建画像会把你的笔记内容发给大模型 API。介意就先精简 `profile.exclude` 或换本地模型。
- **来源是尽力而为**：Reddit 未登录常被限流、RSSHub 公共实例不保证可用，失败会自动跳过。
- **配图**：当前留给上层（如 Hermes 的生图工具）处理，本地管线默认 `portrait.enabled: false`。
- 这是个人项目，不是生产级服务。

## 已做 / Roadmap

已完成：多源获取（含 YouTube）、全文抓取、本地 embedding 语义去重、"更多类似"、命中率评估与自适应 3:7、关键词级反馈偏置、同日追加、Web 界面（跑一轮/读简报/标反馈）、Hermes skill 封装。

待做：

- [ ] Telegram 捕获"日常刷到的东西"作为额外信号
- [ ] 隐式反馈（从行为推断喜好）
- [ ] 画像分层 + 时间衰减
- [ ] 出图走 Codex OAuth + gpt-image-2

## 开发

```bash
pip install -e ".[dev]"   # 装 pytest + ruff
pytest                     # 跑单测
ruff check .               # 静态检查
```

- 架构与数据流见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。
- 改动记录见 [`CHANGELOG.md`](CHANGELOG.md)。
- CLI 与 skill 共用同一份编排 `infoflow.pipeline.run`，逻辑只此一处。

## License

MIT

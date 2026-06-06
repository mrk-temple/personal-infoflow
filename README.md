# personal-infoflow

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
6. **交付**：写一篇当日简报进 vault（同一天多次跑则追加不覆盖）
7. **反馈**：你标"好/差"→ 自动调整来源权重、关键词偏置和画像，越用越准

## 两种用法

**A. 本地 CLI**

```bash
git clone <your-repo-url> && cd personal-infoflow
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                 # 填入 DEEPSEEK_API_KEY
cp config.example.yaml config.yaml   # 改 vault 路径、内容源

python -m infoflow.main --refresh-profile   # 首次：建画像 + 出简报
python -m infoflow.main                      # 之后每天跑
python -m infoflow.main --feedback           # 只汇总反馈，不抓取
```

挂到 cron / 计划任务里每天自动跑即可。

**B. 作为 [Hermes](https://github.com/NousResearch/hermes-agent) skill**

核心逻辑与 CLI 共用一份。把 `skill/personal-infoflow/` 放进 Hermes 的 skills 目录、配好 `INFOFLOW_HOME` 与 `INFOFLOW_PYTHON`，就能对 Hermes 说"给我今天的信息流"自动跑。详见 [`skill/personal-infoflow/README.md`](skill/personal-infoflow/README.md)。

## 配置要点（全在 `config.yaml`）

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

已完成：多源获取（含 YouTube）、全文抓取、本地 embedding 语义去重、"更多类似"、命中率评估与自适应 3:7、关键词级反馈偏置、同日追加、Hermes skill 封装。

待做：

- [ ] Telegram 捕获"日常刷到的东西"作为额外信号
- [ ] 隐式反馈（从行为推断喜好）
- [ ] 画像分层 + 时间衰减
- [ ] 出图走 Codex OAuth + gpt-image-2

## License

MIT

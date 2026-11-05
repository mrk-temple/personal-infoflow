# 架构

一句话：**建画像 → 抓取 → 去重 → 打分 → 选条成简报 → 收反馈进化**。CLI、Web 与 skill
共用同一份编排（`infoflow.pipeline.run`），逻辑只此一处。

## 数据流

```
笔记 + AI对话 + 历史反馈
        │  profile.build_profile / load_profile
        ▼
   兴趣画像(profile.md)
        │
多源抓取 sources.gather ──► 候选 items[{title,link,summary,source}]
        │  (seen.json 去掉已见)
        ▼
去重  embedding 开 → semantic.cluster_semantic（向量余弦）
      否则        → cluster.cluster_items（标题相似）
        │  (可选 enrich 抓正文)
        ▼
打分  rank.rank_items（模型给 relevance/exploration + 来源/关键词偏置 + 语义加分）
        ▼
选条  digest.write_digest（3 贴合 : 7 拓展，自适应比例，每源上限）
        ▼
   当日简报(YYYY-MM-DD.md，同日追加) ◄── Web 界面也读这一篇
        │                                    （点「好/差」写回 反馈:: 行）
        ▼  用户在 `反馈::` 标 好/差
反馈  feedback.collect_feedback（解析简报 → 聚合来源/关键词偏置、命中率、自适应比例）
        └──► 回流到下一轮的画像与打分
```

## 模块职责

| 模块 | 职责 |
| --- | --- |
| `config.py` | 读 config.yaml、合并缺省值、最小校验；路径解析 `resolve()` |
| `client.py` | OpenAI 兼容客户端、`chat()`、从模型输出抠 `extract_json()` |
| `http.py` | 统一的 HTTP 工具（UA / 超时 / 读取上限 / GET·POST JSON） |
| `profile.py` | 读笔记 + 信号，调模型生成兴趣画像 |
| `signals.py` | 额外信号：AI 对话导出、主动保存的捕获内容 |
| `sources.py` | 各源适配器（rss/hn/reddit/arxiv/googlenews/github/youtube/twitter）+ `gather` |
| `fetch.py` | 获取层薄门面（转调 `sources.gather`） |
| `cluster.py` | 标题相似度聚类去重（无 embedding 时的回退） |
| `embed.py` | 本地向量层（fastembed / ollama），带缓存 |
| `semantic.py` | 向量去重、与"喜欢过的"内容的相似度（"更多类似"） |
| `enrich.py` | 跟链接抓正文，替换截断的 RSS 摘要 |
| `rank.py` | 调模型按画像打 relevance/exploration，叠加反馈偏置 |
| `digest.py` | 按 3:7 选条、每源上限，写/追加当日简报 |
| `feedback.py` | 解析简报里的 好/差，聚合来源·关键词偏置、命中率、自适应比例 |
| `portrait.py` | 画像配图（本地 Pollinations，默认关；正式出图交给上层 agent） |
| `pipeline.py` | 把以上串成一轮的编排；CLI、Web 与 skill 都调它 |
| `web.py` | Web 界面后端（标准库 http.server）：API + 后台跑一轮 + 进度快照 |
| `webapp/` | Web 前端：单文件无框架页面，点「好/差」写回简报的 `反馈::` 行 |
| `main.py` | CLI 入口、参数解析、日志配置 |

## 入口

- 本地 CLI：`python -m infoflow [--refresh-profile|--portrait|--feedback|-v]`
- Web 界面：`python -m infoflow --web [--web-host H --web-port P]` → `http://127.0.0.1:7781`
- 装包后：`infoflow ...`（见 `pyproject.toml` 的 `[project.scripts]`）
- Skill：`skill/personal-infoflow/scripts/run.{sh,py}`，自动定位仓库与解释器后转调 `python -m infoflow`

## 状态文件（`infoflow/data/`，gitignore，属用户数据）

- `profile.md` —— 当前兴趣画像
- `seen.json` —— 已出现过的链接（避免重复推荐）
- `feedback_log.json` / `feedback_state.json` —— 反馈原始记录 / 聚合状态
- `emb_cache.json` / `anchors.json` —— 向量缓存 / "喜欢过"的锚点向量

# 配置参考（config.yaml）

完整模板见仓库根的 `config.example.yaml`。下面只讲要点。缺省值见 `infoflow/config.py`
的 `DEFAULTS`——用户没写的键会自动回退，不会报 KeyError。

## 必填项

- `vault_path` —— Obsidian vault 根目录（建画像时读这里的 `.md`）。
- `models.profile` / `models.rank` —— 建画像 / 打分用的模型名（DeepSeek 兼容 OpenAI 接口）。
- `digest.output_dir` —— 简报写到哪个目录（通常是 vault 里的"信息简报"文件夹）。
- `sources` —— 内容源列表，至少一个。

## 内容源类型（sources[].type）

| type | 关键字段 | 说明 |
| --- | --- | --- |
| `rss` | `url` | 通用 RSS/Atom。中文平台用 RSSHub 转成 RSS 后也走这里 |
| `hackernews` | `limit` | HN 首页 |
| `reddit` | `subreddit`, `window`, `limit` | 未登录常被限流，失败自动跳过 |
| `arxiv` | `category`, `limit` | 如 `cs.AI` |
| `googlenews` | `queries`, `limit` | 按关键词主动拉"邻近但用户没接触过"的主题，加宽面 |
| `github` | `since_days`, `language?`, `topic?`, `limit` | 最近新建、按 star 排序的又新又火仓库 |
| `youtube` | `channels` / `playlists` / `handles`, `limit` | 原生 RSS，免费无需 key；`@handle` 自动解析成 channel_id |
| `twitter` | `base`, `handles`, `limit` | X 无免费公共 RSS，`base` 须指向自建 RSSHub |

每条源可加 `enabled: false` 临时关掉，`name:` 自定义显示名。

## 抓取与打分

- `fetch.full_text` —— 是否跟链接抓正文再打分（更准但更慢）。`full_text_limit` 控每次抓几篇。
- `rank.batch_size` —— 每批送模型打分的条数。`rank.breadth_weight` 影响展示用综合分。
- `digest.exploration_ratio` —— 开眼界占比，默认 0.7（3 贴合 : 7 拓展）；反馈充分时会自适应微调。
- `digest.min_score` —— 只给"贴合位"设门槛。`digest.max_per_source` —— 每源最多几条，0 = 不限。

## embedding（本地向量层，可选）

- `embedding.enabled: true` 需先 `pip install fastembed`（注意它要 numpy<2）。**没装会自动
  回退到标题去重，不报错。**
- `provider: fastembed`（默认，轻量）或 `ollama`（填 `ollama_url`）。
- 作用：语义去重（比标题字面更准）+ "更多类似"（与点过"好"的内容越像，越加分）。

## 模型与密钥

- `DEEPSEEK_API_KEY` 放仓库 `.env`。base_url 默认 `https://api.deepseek.com`，可用环境变量
  `DEEPSEEK_BASE_URL` 覆盖（接代理/自建网关）。
- 模型名以 `models.list()` 能查到的为准；本仓库当前用 `deepseek-v4-pro` / `deepseek-v4-flash`。

# 画像配图规范（可选）

管线只负责更新画像**文字**（`<仓库>/infoflow/data/profile.md`）。出图由当前 agent 自带的
图像生成工具完成（本地管线接的 Pollinations 已收费，`portrait.enabled` 保持 false）。

当用户要"新画像 / 重建画像 / 给画像配图"，且 agent 有可用图像工具时，在跑完
`--refresh-profile` 之后：

1. 读 `infoflow/data/profile.md`，理解这个人**与信息、知识的关系是什么气质**
   （构建者 / 编织者 / 探索者……）。
2. 写一句**英文**绘画提示词：用场景、光线、象征物隐喻这种气质，**不要**罗列他在学的具体学科
   或模型名（不要出现 textbook / ResNet / calculus 这类词），画面克制、有留白、不画真人肖像，
   带风格词（minimal illustration, soft light, atmospheric）。
3. 用图像工具按该提示词出图。
4. 保存到 vault 的简报目录，文件名带时间戳：`<简报目录>/portrait-YYYYMMDD-HHMM.png`
   （简报目录见 config.yaml 的 `digest.output_dir`）。
5. 追加进成长档案 `<简报目录>/兴趣画像.md`：一段 `## 🕐 时间戳` + `![[portrait-时间戳.png]]`
   + 提示词，**追加不覆盖**，让用户看到一张张的蜕变。
6. 简短告诉用户出了新图、存在哪，并一句话说这次相比上次的变化。

没有可用图像工具就跳过——别尝试装/调本地出图。

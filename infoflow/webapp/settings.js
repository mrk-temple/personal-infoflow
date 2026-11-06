"use strict";
Object.assign(STRINGS["zh-CN"], {
  adaptiveLabel:"根据明确反馈自动微调推荐比例",
  monoTheme:"黑白报", warmTheme:"暖纸报", settings:"设置", editionNote:"给阅读留一点时间。", makePortrait:"生成画像配图",
  settingsTitle:"把报纸调成你的样子", settingsIntro:"选择自己的模型、阅读配方和消息来源。设置保存在本机，往期日报一直保留。",
  readingRecipe:"阅读配方", explorationLabel:"开眼界占比", itemCount:"每期条数", sourceCap:"每来源最多条数（0 不限）", implicitLabel:"使用收藏与前台停留作为较弱的偏好信号",
  textEngine:"文字与排序", providerLabel:"模型供应商 / 运行方式", rankModel:"排序模型 ID", profileModel:"画像模型 ID", endpointLabel:"API 地址（可覆盖默认地址）", keepKey:"留空保留已有密钥",
  cliPath:"Codex CLI 可执行文件名或路径", cliModel:"CLI 模型（留空使用 CLI 默认值）", cliNote:"使用本机已登录的 Codex；不需要新的 API key，会占用账号已有用量。",
  imageEngine:"可选配图", imageProvider:"选择生图方式", noImage:"不配图", imageApi:"自己的生图 API（OpenAI 兼容）", imageLocal:"本地 Stable Diffusion / Forge", imageEndpoint:"生图服务地址", imageModel:"生图模型 ID / 本地 checkpoint（可留空）", autoImage:"更新画像时自动配图（也可在画像里手动生成）",
  sourceSettings:"消息来源", sourceNote:"可添加、关闭或移除来源，并设置每个来源的采集条数。不会删除已有日报。", addSource:"＋ 添加来源", sourceType:"类型", sourceName:"来源名称", sourceTarget:"地址 / 分类 / 关键词 / 频道", sourceLimit:"采集条数", sourceEnabled:"启用", removeSource:"移除",
  keyPrivacy:"密钥仅保存到本机 .env.local，保存后不会返回浏览器。不要将它提交到 GitHub。", saveSettings:"保存设置", settingsSaved:"设置已保存，下次生成时生效；往期日报已保留。", autoProvider:"自动检测已有环境配置", configured:"已配置", missingKey:"尚未配置", invalid_settings:"设置无效：请检查模型 ID、API 地址、条数和来源。", noImageSelected:"先在设置中选择生图方式。",
});
Object.assign(STRINGS.en, {
  adaptiveLabel:"Adapt the reading ratio using explicit feedback",
  monoTheme:"B&W", warmTheme:"Warm paper", settings:"Settings", editionNote:"A little time, well read.", makePortrait:"Generate profile illustration",
  settingsTitle:"Your paper. Your rules.", settingsIntro:"Choose your models, reading recipe and sources. Settings stay local; earlier editions stay in your archive.",
  readingRecipe:"Reading recipe", explorationLabel:"Exploration share", itemCount:"Stories per edition", sourceCap:"Maximum per source (0 = unlimited)", implicitLabel:"Use saves and visible reading time as weaker preference signals",
  textEngine:"Writing & ranking", providerLabel:"Provider / runtime", rankModel:"Ranking model ID", profileModel:"Profile model ID", endpointLabel:"API base URL (override if needed)", keepKey:"Leave blank to keep the existing key",
  cliPath:"Codex CLI executable name or path", cliModel:"CLI model (blank uses the CLI default)", cliNote:"Uses your signed-in local Codex CLI. No new API key required; your account's usage limits still apply.",
  imageEngine:"Optional illustrations", imageProvider:"Image generation method", noImage:"No illustrations", imageApi:"Your image API (OpenAI-compatible)", imageLocal:"Local Stable Diffusion / Forge", imageEndpoint:"Image service base URL", imageModel:"Image model ID / local checkpoint (optional locally)", autoImage:"Generate an illustration when refreshing the profile (or generate manually from Your profile)",
  sourceSettings:"Your sources", sourceNote:"Add, disable or remove sources and set how many stories to fetch from each. Existing editions are preserved.", addSource:"＋ Add a source", sourceType:"Type", sourceName:"Source name", sourceTarget:"URL / category / keywords / channels", sourceLimit:"Fetch limit", sourceEnabled:"Enabled", removeSource:"Remove",
  keyPrivacy:"Keys are saved only in this computer's .env.local and are never sent back to the browser. Keep this file out of GitHub.", saveSettings:"Save settings", settingsSaved:"Settings saved for the next run. Earlier editions are preserved.", autoProvider:"Detect existing environment configuration", configured:"configured", missingKey:"not configured", invalid_settings:"Invalid settings. Check model IDs, endpoint URLs, counts and source fields.", noImageSelected:"Choose an image generation method in Settings first.",
});
let settingsData = null, sourceDraft = [];
let paperTheme = "warm";
try { paperTheme = localStorage.getItem("infoflow.theme") || "warm"; } catch {}
if (!["warm","mono"].includes(paperTheme)) paperTheme = "warm";
function setPaperTheme(value) {
  paperTheme = value;
  document.documentElement.dataset.theme = value;
  $$('button[data-theme]').forEach(b => b.setAttribute("aria-pressed", String(b.dataset.theme === value)));
  try { localStorage.setItem("infoflow.theme", value); } catch {}
}
$$('button[data-theme]').forEach(b => { b.onclick = () => setPaperTheme(b.dataset.theme); });
setPaperTheme(paperTheme);
function renderSettingsLanguage() {
  $(".theme-options").setAttribute("aria-label", language === "en" ? "Newspaper colors" : "报纸颜色");
  if (settingsData) {
    const value = $("#pref-provider").value;
    renderProviderOptions(value);
    updateProviderVisibility();
    updateRatioLabel();
  }
}
function renderProviderOptions(value) {
  $("#pref-provider").innerHTML = `<option value="auto">${esc(t("autoProvider"))}</option>` + settingsData.providers.map(p => `<option value="${esc(p.id)}">${esc(p.label)}${p.id !== "codex" ? ` · ${esc(t(p.configured ? "configured" : "missingKey"))}` : ""}</option>`).join("");
  $("#pref-provider").value = value || "auto";
}
function updateRatioLabel() { $("#ratio-label").textContent = ` ${$("#pref-ratio").value}%`; }
function updateProviderVisibility() {
  const id = $("#pref-provider").value, cli = id === "codex";
  $("#cli-options").hidden = !cli; $("#api-options").hidden = cli;
  $("#pref-rank").required = !cli; $("#pref-profile").required = !cli;
  const provider = settingsData?.providers.find(p => p.id === id);
  $("#key-label").textContent = provider?.key_env || t("autoProvider");
  $("#pref-key").disabled = !provider?.key_env;
}
function updateImageVisibility() {
  const id = $("#pref-image-provider").value;
  $("#image-endpoint-options").hidden = !["api","local"].includes(id);
  $("#image-key-options").hidden = id !== "api";
  $("#image-cli-options").hidden = id !== "codex";
  $("#pref-image-auto").disabled = id === "none";
  if (id === "none") $("#pref-image-auto").checked = false;
  $("#pref-image-endpoint").required = id === "api";
  $("#pref-image-model").required = id === "api";
}
const sourceTypes = ["rss","hackernews","arxiv","reddit","googlenews","github","youtube","twitter"];
function sourceTarget(spec) {
  return spec.type === "rss" ? spec.url || "" : spec.type === "arxiv" ? spec.category || "" : spec.type === "reddit" ? spec.subreddit || "" : spec.type === "googlenews" ? (spec.queries || []).join(", ") : spec.type === "youtube" ? [...(spec.channels || []), ...(spec.handles || [])].join(", ") : spec.type === "github" ? spec.topic || "" : spec.type === "twitter" ? `${spec.base || ""} | ${(spec.handles || []).join(", ")}` : "";
}
function readSourceRows() {
  return $$(".source-row").map((row, i) => {
    const type = row.querySelector(".src-type").value;
    const original = sourceDraft[i]?.type === type ? sourceDraft[i] : {};
    const spec = {...original, type, name:row.querySelector(".src-name").value.trim(), enabled:row.querySelector(".src-enabled").checked, limit:Number(row.querySelector(".src-limit").value)};
    const target = row.querySelector(".src-target").value.trim(), list = target.split(",").map(x => x.trim()).filter(Boolean);
    if (type === "rss") spec.url = target;
    if (type === "arxiv") spec.category = target;
    if (type === "reddit") spec.subreddit = target;
    if (type === "googlenews") spec.queries = list;
    if (type === "github") spec.topic = target;
    if (type === "youtube") { spec.channels = list.filter(x => !x.startsWith("@")); spec.handles = list.filter(x => x.startsWith("@")); }
    if (type === "twitter") { const parts = target.split("|"); spec.base = parts[0].trim(); spec.handles = (parts[1] || "").split(",").map(x => x.trim()).filter(Boolean); }
    return spec;
  });
}
function renderSourceRows() {
  $("#source-editor").innerHTML = sourceDraft.map((spec, i) => `<div class="source-row" data-index="${i}"><div class="source-row-head"><label class="check-label"><input class="src-enabled" type="checkbox" ${spec.enabled !== false ? "checked" : ""}><span>${esc(t("sourceEnabled"))}</span></label><button class="remove-source" type="button">${esc(t("removeSource"))}</button></div><div class="source-row-grid"><label>${esc(t("sourceType"))}<select class="src-type">${sourceTypes.map(type => `<option value="${type}" ${type === spec.type ? "selected" : ""}>${type}</option>`).join("")}</select></label><label>${esc(t("sourceName"))}<input class="src-name" value="${esc(spec.name || "")}"></label><label>${esc(t("sourceLimit"))}<input class="src-limit" type="number" min="1" max="200" required value="${spec.limit || 15}"></label></div><label>${esc(t("sourceTarget"))}<input class="src-target" value="${esc(sourceTarget(spec))}" ${["rss","arxiv","reddit","googlenews","youtube"].includes(spec.type) ? "required" : ""} ${spec.type === "hackernews" ? "disabled" : ""}></label></div>`).join("");
}
function fillSettings(data) {
  settingsData = data;
  renderProviderOptions(data.models.provider);
  $("#pref-ratio").value = Math.round(data.digest.exploration_ratio * 100);
  $("#pref-items").value = data.digest.max_items;
  $("#pref-source-cap").value = data.digest.max_per_source;
  $("#pref-implicit").checked = !!data.reading.implicit_feedback;
  $("#pref-adaptive").checked = !!data.feedback?.adaptive_exploration;
  $("#pref-rank").value = data.models.rank || ""; $("#pref-profile").value = data.models.profile || "";
  $("#pref-endpoint").value = data.models.base_url || ""; $("#pref-key").value = "";
  $("#pref-cli").value = data.models.codex_command || "codex"; $("#pref-cli-model").value = data.models.codex_model || "";
  $("#pref-image-provider").value = data.portrait.provider || "none";
  $("#pref-image-endpoint").value = data.portrait.base_url || "";
  $("#pref-image-model").value = data.portrait.model || "";
  $("#pref-image-key").value = "";
  $("#pref-image-cli").value = data.portrait.codex_command || "codex";
  $("#pref-image-auto").checked = !!data.portrait.enabled;
  sourceDraft = structuredClone(data.sources || []);
  updateRatioLabel(); updateProviderVisibility(); updateImageVisibility(); renderSourceRows();
}
$("#settings").onclick = async () => {
  $("#settings-error").textContent = "";
  try { fillSettings(await api("/api/settings")); $("#settings-dialog").showModal(); }
  catch (error) { toast(error.message); }
};
$("#close-settings").onclick = () => $("#settings-dialog").close();
$("#pref-ratio").oninput = updateRatioLabel;
$("#pref-provider").onchange = () => {
  const p = settingsData.providers.find(p => p.id === $("#pref-provider").value);
  if (p) { $("#pref-endpoint").value = p.base_url; $("#pref-rank").value = p.model; $("#pref-profile").value = p.model; }
  $("#pref-key").value = ""; updateProviderVisibility();
};
$("#pref-image-provider").onchange = () => {
  const p = $("#pref-image-provider").value;
  $("#pref-image-endpoint").value = p === "local" ? "http://127.0.0.1:7860" : p === "api" ? "https://api.openai.com/v1" : "";
  $("#pref-image-model").value = ["codex","api"].includes(p) ? "gpt-image-2" : "";
  $("#pref-image-key").value = ""; updateImageVisibility();
};
$("#source-editor").addEventListener("click", event => {
  const button = event.target.closest(".remove-source");
  if (button) { sourceDraft = readSourceRows(); sourceDraft.splice(Number(button.closest(".source-row").dataset.index), 1); renderSourceRows(); }
});
$("#source-editor").addEventListener("change", event => { if (event.target.classList.contains("src-type")) { sourceDraft = readSourceRows(); renderSourceRows(); } });
$("#add-source").onclick = () => { sourceDraft = readSourceRows(); sourceDraft.push({type:"rss", url:"", name:"", limit:15, enabled:true}); renderSourceRows(); };
$("#settings-form").onsubmit = async event => {
  event.preventDefault(); $("#settings-error").textContent = ""; $("#save-settings").disabled = true;
  const body = {
    models:{provider:$("#pref-provider").value, rank:$("#pref-rank").value.trim(), profile:$("#pref-profile").value.trim(), base_url:$("#pref-endpoint").value.trim(), codex_command:$("#pref-cli").value.trim() || "codex", codex_model:$("#pref-cli-model").value.trim()},
    digest:{exploration_ratio:Number($("#pref-ratio").value) / 100, max_items:Number($("#pref-items").value), max_per_source:Number($("#pref-source-cap").value)},
    reading:{implicit_feedback:$("#pref-implicit").checked},
    feedback:{adaptive_exploration:$("#pref-adaptive").checked},
    portrait:{provider:$("#pref-image-provider").value, enabled:$("#pref-image-auto").checked, base_url:$("#pref-image-endpoint").value.trim(), model:$("#pref-image-model").value.trim(), codex_command:$("#pref-image-cli").value.trim() || "codex"},
    sources:readSourceRows(), api_key:$("#pref-key").value, image_api_key:$("#pref-image-key").value,
  };
  try { const result = await api("/api/settings", body); fillSettings(result.settings); $("#settings-dialog").close(); toast(t("settingsSaved")); await poll(); }
  catch (error) { $("#settings-error").textContent = error.message; }
  finally { $("#save-settings").disabled = false; }
};
$("#make-portrait").onclick = async () => {
  try { const data = await api("/api/settings"); if (data.portrait.provider === "none") return toast(t("noImageSelected")); $("#profile-dialog").close(); await start({portrait:true}); }
  catch (error) { toast(error.message); }
};
applyLanguage();

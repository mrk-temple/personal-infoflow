"use strict";
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const STRINGS = {
  "zh-CN": {
    skip:"跳到简报", localEdition:"你的私人编辑部", connecting:"连接中", connected:"本机已连接", offline:"连接中断，正在重试",
    title:"个人信息日报", intro:"从你的兴趣出发，往更大的世界去。", editionStamp:"每日精选 · 持续生长",
    recipeLabel:"我的阅读配方", recipeCopy:"贴合兴趣 / 开眼界", editorDesk:"阅读操作",
    commandCopy:"读你的笔记，为你选稿。每一次反馈，都让下一期更懂你。", profile:"兴趣画像", collect:"同步反馈", refresh:"更新画像", generate:"生成今日简报 ↗",
    details:"查看运行详情", summaryHint:"少一点噪音，多一点值得。", readingTitle:"今天，读这些", all:"全部", relevant:"贴合兴趣", explore:"开眼界",
    edition:"本期", unread:"未读", saved:"稍后读", searchLabel:"搜索简报", searchPlaceholder:"搜索标题、推荐理由…", sourceLabel:"按来源筛选", allSources:"全部来源", dateLabel:"选择日期",
    retry:"重试", footerBrand:"私人编辑部 · 持续生长", feedbackHint:"好／差可随时修改或清除，保存后立即同步。", shortcuts:"快捷键：/ 搜索 · J/K 浏览 · S 稍后读 · M 已读",
    close:"关闭 ×", profileIntro:"长期知识作为底色，最近的捕获与反馈持续调整方向。",
    privacy:"阅读状态仅保存在本机；隐式偏好默认关闭。笔记与信号会在生成时发送给你配置的模型。",
    good:"好", bad:"差", yourVerdict:"这一条，对你有用吗？", save:"＋ 稍后读", unsave:"✓ 已保存", markRead:"标为已读", markUnread:"✓ 已读", readOriginal:"读原文 ↗",
    lead:"本期头条 / THE LEAD", story:"阅读", score:"精选分", fullText:"已参考正文", otherSources:"个其他源也在报道", noKey:"模型未配置",
    stories:"条精选", sources:"个来源", marked:"条反馈", shown:"条匹配", libraryTitle:"留给下一次阅读", pastTitle:"往期，仍然值得",
    emptyTitle:"等待开版", emptyCopy:"点击「生成今日简报」，让值得读的消息汇入这一页。", noMatchTitle:"这一页，暂时安静", noMatchCopy:"没有匹配的条目，试试清空搜索或切换栏目。",
    noSavedTitle:"为好内容留个位置", noSavedCopy:"点文章上的「稍后读」，在这里收集各期值得回看的内容。", loadFailed:"简报加载失败", loadFailedCopy:"请检查本地服务是否还在运行，然后重试。",
    savedGood:"记下了：好", savedBad:"记下了：差", cleared:"已清除标注", savedItem:"已保存到稍后读", removedItem:"已从稍后读移除", readDone:"已标为已读", readUndone:"已恢复未读",
    writeFailed:"保存失败，请重试", busy:"正在编辑这一期…", done:"本轮已完成", runFailed:"本轮未完成，请查看详情后重试", starting:"正在启动…", profileEmpty:"还没有画像，点击「更新画像」开始。",
    captures:"条主动捕获", decay:"反馈半衰期", days:"天", implicitOn:"隐式偏好已启用", implicitOff:"隐式偏好已关闭", profileUpdated:"最近更新",
    error:"请求失败，请重试", item_not_found:"条目已被修改，请刷新后重试", already_running:"已有任务在运行，请稍候", origin_rejected:"请求来源不匹配，请从本机地址打开页面", server_error:"本地状态读取失败，请检查配置与状态文件", implicit_disabled:"隐式偏好未启用", invalid_date:"日期无效",
  },
  en: {
    skip:"Skip to stories", localEdition:"YOUR PRIVATE EDITION", connecting:"Connecting", connected:"Connected locally", offline:"Reconnecting…",
    title:"The Daily Flow", intro:"Start with your interests. Go a little further.", editionStamp:"Selected daily. Always evolving.",
    recipeLabel:"YOUR READING RECIPE", recipeCopy:"Relevant / Beyond the familiar", editorDesk:"THE EDITOR'S DESK",
    commandCopy:"Your notes set the direction. Your feedback shapes the next edition.", profile:"Your profile", collect:"Sync feedback", refresh:"Refresh profile", generate:"Make today's digest ↗",
    details:"View run details", summaryHint:"Less noise. More worth reading.", readingTitle:"Worth your attention", all:"All stories", relevant:"For you", explore:"Explore",
    edition:"This edition", unread:"Unread", saved:"Read later", searchLabel:"Search stories", searchPlaceholder:"Search titles, reasons…", sourceLabel:"Filter by source", allSources:"All sources", dateLabel:"Choose edition",
    retry:"Retry", footerBrand:"YOUR PRIVATE EDITION · ALWAYS EVOLVING", feedbackHint:"Change or clear good/bad anytime. Every edit is synced immediately.", shortcuts:"Keys: / search · J/K navigate · S save · M read",
    close:"Close ×", profileIntro:"Long-term knowledge sets the foundation. Recent captures and feedback keep it current.",
    privacy:"Reading state stays on this computer. Implicit preferences are off by default. Notes and signals are sent to your configured model when generating.",
    good:"Good", bad:"Bad", yourVerdict:"Was this worth your time?", save:"＋ Save for later", unsave:"✓ Saved", markRead:"Mark as read", markUnread:"✓ Read", readOriginal:"Read original ↗",
    lead:"THE LEAD", story:"READING", score:"Score", fullText:"Full text considered", otherSources:"other sources covering this", noKey:"Model not configured",
    stories:"stories", sources:"sources", marked:"rated", shown:"matching", libraryTitle:"For your next quiet moment", pastTitle:"From an earlier edition",
    emptyTitle:"Your next edition awaits", emptyCopy:"Choose “Make today's digest” to bring worthwhile stories onto this page.", noMatchTitle:"A quiet corner", noMatchCopy:"No stories match. Clear your search or try another section.",
    noSavedTitle:"Keep something worth returning to", noSavedCopy:"Choose “Save for later” on any story to build a reading list across editions.", loadFailed:"Couldn't load your digest", loadFailedCopy:"Check that the local service is running, then retry.",
    savedGood:"Saved: good", savedBad:"Saved: bad", cleared:"Rating cleared", savedItem:"Saved for later", removedItem:"Removed from read later", readDone:"Marked as read", readUndone:"Marked as unread",
    writeFailed:"Couldn't save. Please retry.", busy:"Preparing your edition…", done:"This run is complete", runFailed:"This run couldn't finish. Check the details and retry.", starting:"Starting…", profileEmpty:"No profile yet. Choose “Refresh profile” to get started.",
    captures:"captures", decay:"Feedback half-life", days:"days", implicitOn:"Implicit preferences on", implicitOff:"Implicit preferences off", profileUpdated:"Last updated",
    error:"Request failed. Please retry.", item_not_found:"This story changed. Reload and retry.", already_running:"A run is already in progress.", origin_rejected:"Open this reader from its local address.", server_error:"Couldn't read local state. Check your configuration and state files.", implicit_disabled:"Implicit preferences are disabled.", invalid_date:"Invalid edition date.",
  },
};
let language;
try { language = localStorage.getItem("infoflow.language"); } catch { /* storage may be blocked */ }
if (!STRINGS[language]) language = navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
const t = key => STRINGS[language][key] || STRINGS.en[key] || key;
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const href = value => { try { const u = new URL(value); return /^https?:$/.test(u.protocol) ? esc(u.href) : "#"; } catch { return "#"; } };
let items = [], edition = "", today = "", bucket = "all", view = "all", source = "", running = false, starting = false;
let status = null, loadId = 0, loadError = false, pollBusy = false, wasRunning = false, profileData = null;
const pending = new Set();
let toastTimer;
function toast(message) { $("#toast").textContent = message; $("#toast").classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 3200); }
async function api(path, body) {
  let response;
  try {
    response = await fetch(path, {method:body === undefined ? "GET" : "POST", headers:body === undefined ? {} : {"Content-Type":"application/json"}, body:body === undefined ? undefined : JSON.stringify(body), signal:AbortSignal.timeout(15000)});
  } catch { throw new Error(t("error")); }
  let result;
  try { result = await response.json(); } catch { throw new Error(t("error")); }
  if (!response.ok || result.ok === false) throw new Error(t(result.error || "error"));
  return result;
}
function applyLanguage() {
  document.documentElement.lang = language;
  document.title = `${t("title")} · Personal InfoFlow`;
  $$('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  $$('[data-placeholder]').forEach(el => { el.placeholder = t(el.dataset.placeholder); });
  $("#language").textContent = language === "en" ? "简体中文 ↗" : "English ↗";
  $("#language").setAttribute("aria-label", language === "en" ? "切换到简体中文" : "Switch to English");
  $("#source").setAttribute("aria-label", t("sourceLabel"));
  $("#edition-date").setAttribute("aria-label", t("dateLabel"));
  $("#stories").setAttribute("aria-label", t("readingTitle"));
  $("#profile-image").alt = language === "en" ? "Interest profile illustration" : "兴趣画像配图";
  $(".filters").setAttribute("aria-label", t("relevant") + " / " + t("explore"));
  $(".reader-toolbar").setAttribute("aria-label", t("searchLabel"));
  $(".command-panel").setAttribute("aria-label", t("editorDesk"));
  renderSources(); renderItems(); renderStatus(); renderProfile();
  if (typeof renderSettingsLanguage === "function") renderSettingsLanguage();
}
function renderSources() {
  const sources = [...new Set(items.map(it => it.source))].filter(Boolean).sort();
  if (!sources.includes(source)) source = "";
  $("#source").innerHTML = `<option value="">${esc(t("allSources"))}</option>` + sources.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join("");
  $("#source").value = source;
}
function filtered() {
  const query = $("#search").value.trim().toLocaleLowerCase();
  return items.filter(it => (bucket === "all" || it.bucket === bucket) && (!source || it.source === source) &&
    (view !== "unread" || !it.read) && (!query || `${it.title} ${it.reason} ${it.source}`.toLocaleLowerCase().includes(query)));
}
function renderItems() {
  const visible = filtered();
  $("#stories").innerHTML = visible.map((it, i) => {
    const key = `${it.date}\t${it.link}`;
    const good = it.verdict === "pos", bad = it.verdict === "neg", busy = pending.has(key);
    return `<article tabindex="0" data-key="${esc(key)}" data-kicker="${esc(i ? `${String(i + 1).padStart(2,"0")} / ${t("story")}` : t("lead"))}" aria-busy="${busy}">
      <div class="meta"><span class="tag-${it.bucket}">${esc(t(it.bucket === "explore" ? "explore" : "relevant"))}</span><span>${esc(it.source)}</span>${it.score !== "" ? `<span title="${esc(t("score"))}">${esc(it.score)} / 100</span>` : ""}${view === "saved" ? `<time>${esc(it.date)}</time>` : ""}</div>
      <h2><a href="${href(it.link)}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">${esc(it.title)}</a></h2>
      <p class="reason">${esc(it.reason)}</p>
      ${it.enriched || it.dup_count > 1 ? `<p class="story-context">${it.enriched ? esc(t("fullText")) : ""}${it.dup_count > 1 ? ` · ${it.dup_count - 1} ${esc(t("otherSources"))}` : ""}</p>` : ""}
      <div class="story-tools"><button data-action="save" aria-pressed="${!!it.saved}" ${busy ? "disabled" : ""}>${esc(t(it.saved ? "unsave" : "save"))}</button><button data-action="read" aria-pressed="${!!it.read}" ${busy ? "disabled" : ""}>${esc(t(it.read ? "markUnread" : "markRead"))}</button></div>
      <div class="fb"><span class="lbl">${esc(t("yourVerdict"))}</span><button data-action="feedback" data-value="pos" class="${good ? "on-good" : ""}" aria-pressed="${good}" ${busy ? "disabled" : ""}>${esc(t("good"))}</button><button data-action="feedback" data-value="neg" class="${bad ? "on-bad" : ""}" aria-pressed="${bad}" ${busy ? "disabled" : ""}>${esc(t("bad"))}</button></div></article>`;
  }).join("");
  $("#empty").hidden = visible.length > 0;
  const emptyType = loadError ? "loadFailed" : view === "saved" && !items.length ? "noSaved" : items.length ? "noMatch" : "empty";
  $("#empty-title").textContent = t(emptyType === "loadFailed" ? emptyType : emptyType + "Title");
  $("#empty-copy").textContent = t(emptyType + "Copy");
  $("#retry").hidden = !loadError;
  $("#reading-title").textContent = t(view === "saved" ? "libraryTitle" : edition && today && edition !== today ? "pastTitle" : "readingTitle");
  const count = items.filter(it => it.verdict).length;
  $("#summary-count").innerHTML = `<strong>${items.length}</strong> ${esc(t("stories"))} · <strong>${new Set(items.map(it => it.source)).size}</strong> ${esc(t("sources"))} · <strong>${count}</strong> ${esc(t("marked"))}${visible.length !== items.length ? ` · ${visible.length} ${esc(t("shown"))}` : ""}`;
}
async function loadDates() {
  const data = await api("/api/dates");
  if (!edition) edition = data.dates[0] || today;
  const dates = [...new Set([today, ...data.dates].filter(Boolean))].sort().reverse();
  $("#edition-date").innerHTML = dates.map(d => `<option value="${esc(d)}">${esc(d)}</option>`).join("");
  $("#edition-date").value = edition || today;
}
async function loadItems() {
  const requestId = ++loadId;
  try {
    const result = await api(view === "saved" ? "/api/saved" : `/api/digest?date=${encodeURIComponent(edition)}`);
    if (requestId !== loadId) return;
    items = result.items;
    if (result.date) edition = result.date;
    loadError = false;
    renderSources(); renderItems();
  } catch (error) {
    if (requestId !== loadId) return;
    items = []; loadError = true; renderItems(); toast(error.message);
  }
}
function renderStatus() {
  ["#run", "#refresh", "#collect"].forEach(s => { $(s).disabled = running || starting; });
  $("#edition-date").disabled = view === "saved";
  if (!status) return;
  $("#today").textContent = today;
  $("#connection").textContent = t("connected");
  const ratio = status.exploration_ratio ?? .7;
  $("#rel-ratio").textContent = Number(((1 - ratio) * 10).toFixed(1));
  $("#exp-ratio").textContent = Number((ratio * 10).toFixed(1));
  $("#demo-label").hidden = !status.demo_label;
  $("#demo-label").textContent = status.demo_label || "";
  const run = status.run;
  $("#progress").hidden = !starting && !run.running && !run.done;
  $("#run-status").textContent = starting ? t("starting") : run.running ? t("busy") : run.error ? t("runFailed") : t("done");
  $("#log").textContent = run.lines.join("\n") + (run.error ? `\n${run.error}` : "");
}
async function poll() {
  if (pollBusy) return;
  pollBusy = true;
  try {
    status = await api("/api/status"); today = status.today; running = status.run.running;
    if (!edition) await loadDates();
    renderStatus();
    if (wasRunning && !running) {
      $("#run-details").open = !!status.run.error;
      await loadDates(); await loadItems();
    }
    wasRunning = running;
  } catch { $("#connection").textContent = t("offline"); }
  finally { pollBusy = false; }
}
async function start(body) {
  if (running || starting) return;
  starting = true; renderStatus();
  try {
    await api("/api/run", {...body, language});
    wasRunning = true;
    $("#run-details").open = true;
    await poll();
  } catch (error) { toast(error.message); }
  finally { starting = false; renderStatus(); }
}
function renderProfile() {
  if (!profileData) return;
  $("#profile-text").innerHTML = profileMarkup(profileData.text || t("profileEmpty"));
  $("#profile-facts").textContent = `${profileData.captures} ${t("captures")} · ${t("decay")} ${profileData.half_life_days} ${t("days")} · ${t(profileData.implicit_feedback ? "implicitOn" : "implicitOff")}`;
  $("#profile-image").hidden = !profileData.image_url;
  if (profileData.image_url) $("#profile-image").src = profileData.image_url;
}
function profileMarkup(text) {
  const inline = value => esc(value).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  const output = []; let list = false;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("- ")) {
      if (!list) { output.push("<ul>"); list = true; }
      output.push(`<li>${inline(line.slice(2))}</li>`); continue;
    }
    if (list) { output.push("</ul>"); list = false; }
    if (!line) continue;
    const heading = line.match(/^#{1,6}\s+(.+)$/) || line.match(/^\*\*(.+)\*\*$/);
    output.push(heading ? `<h3>${inline(heading[1])}</h3>` : `<p>${inline(line)}</p>`);
  }
  if (list) output.push("</ul>");
  return output.join("");
}
async function mutate(article, button) {
  const key = article.dataset.key, item = items.find(it => `${it.date}\t${it.link}` === key);
  if (!item || pending.has(key)) return;
  const action = button.dataset.action;
  pending.add(key); article.setAttribute("aria-busy", "true");
  article.querySelectorAll("button").forEach(b => { b.disabled = true; });
  try {
    if (action === "feedback") {
      const verdict = item.verdict === button.dataset.value ? null : button.dataset.value;
      await api("/api/feedback", {date:item.date, link:item.link, verdict});
      item.verdict = verdict;
      toast(t(verdict === "pos" ? "savedGood" : verdict === "neg" ? "savedBad" : "cleared"));
    } else {
      const value = !(action === "save" ? item.saved : item.read);
      await api("/api/activity", {date:item.date, link:item.link, event:action, value});
      item[action === "save" ? "saved" : "read"] = value;
      toast(t(action === "save" ? value ? "savedItem" : "removedItem" : value ? "readDone" : "readUndone"));
      if (view === "saved" && action === "save" && !value) items = items.filter(it => it !== item);
    }
  } catch (error) { toast(error.message || t("writeFailed")); }
  finally {
    pending.delete(key); renderItems();
    const replacement = $$("article").find(a => a.dataset.key === key);
    replacement?.querySelector(`[data-action="${action}"]${action === "feedback" ? `[data-value="${button.dataset.value}"]` : ""}`)?.focus({preventScroll:true});
  }
}
document.addEventListener("click", async event => {
  const button = event.target.closest("button");
  if (button?.dataset.bucket) {
    bucket = button.dataset.bucket;
    $$('[data-bucket]').forEach(b => b.setAttribute("aria-pressed", String(b === button)));
    renderItems();
  } else if (button?.dataset.view) {
    view = button.dataset.view;
    $$('[data-view]').forEach(b => b.setAttribute("aria-pressed", String(b === button)));
    renderStatus(); await loadItems();
  } else if (button?.dataset.action) {
    await mutate(button.closest("article"), button);
  }
  const link = event.target.closest("article a");
  if (link) {
    const item = items.find(it => `${it.date}\t${it.link}` === link.closest("article").dataset.key);
    if (item) void api("/api/activity", {date:item.date, link:item.link, event:"open"}).catch(() => {});
  }
});
$("#language").onclick = () => { language = language === "en" ? "zh-CN" : "en"; try { localStorage.setItem("infoflow.language", language); } catch {} applyLanguage(); };
$("#run").onclick = () => start({});
$("#refresh").onclick = () => start({refresh_profile:true});
$("#collect").onclick = () => start({feedback_only:true});
$("#retry").onclick = () => loadItems();
$("#search").oninput = renderItems;
$("#source").onchange = event => { source = event.target.value; renderItems(); };
$("#edition-date").onchange = event => { edition = event.target.value; void loadItems(); };
$("#profile").onclick = async () => {
  $("#profile-dialog").showModal(); $("#profile-text").textContent = t("connecting");
  try { profileData = await api("/api/profile"); renderProfile(); } catch (error) { $("#profile-text").textContent = error.message; }
};
$("#close-profile").onclick = () => $("#profile-dialog").close();
$("#profile-dialog").addEventListener("click", event => { if (event.target === $("#profile-dialog")) { const r = event.target.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) event.target.close(); } });
document.addEventListener("keydown", event => {
  if (event.ctrlKey || event.metaKey || event.altKey || $("#profile-dialog").open || $("#settings-dialog").open || /INPUT|SELECT|TEXTAREA/.test(event.target.tagName)) return;
  if (event.key === "/") { event.preventDefault(); $("#search").focus(); return; }
  const articles = $$("article"), active = document.activeElement?.closest("article");
  const index = articles.indexOf(active);
  if (["j","k"].includes(event.key)) { event.preventDefault(); articles[Math.max(0, Math.min(articles.length - 1, index + (event.key === "j" ? 1 : -1)))]?.focus(); }
  if (event.key === "s") active?.querySelector('[data-action="save"]')?.click();
  if (event.key === "m") active?.querySelector('[data-action="read"]')?.click();
  if (event.key === "o") active?.querySelector("h2 a")?.click();
});
// Only opted-in users accrue visible-page dwell time; background tabs never accrue time.
const dwell = new Map();
setInterval(() => {
  if (!status?.implicit_feedback || document.visibilityState !== "visible" || !document.hasFocus()) return;
  for (const article of $$("article")) {
    const r = article.getBoundingClientRect();
    const visible = Math.max(0, Math.min(r.bottom, innerHeight) - Math.max(r.top, 0));
    if (visible < Math.min(r.height, innerHeight) * .6) continue;
    const key = article.dataset.key, seconds = Math.min(600, (dwell.get(key) || 0) + 5);
    dwell.set(key, seconds);
    if (seconds >= 30 && seconds % 30 === 0) {
      const item = items.find(it => `${it.date}\t${it.link}` === key);
      if (item) void api("/api/activity", {date:item.date, link:item.link, event:"dwell", value:seconds}).catch(() => {});
    }
  }
}, 5000);
applyLanguage();
void (async () => { await poll(); await loadItems(); })();
setInterval(poll, 2000);

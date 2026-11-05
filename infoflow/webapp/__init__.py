"""Web 前端：单文件极简页面，无框架无构建。

以字符串常量内嵌在包里（``INDEX_HTML``），由 ``web.serve`` 托管。
设计原则与项目一致——克制、留白、只留必要元素。
"""

INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>个人信息日报 · Personal InfoFlow</title>
<style>
:root {
  --page:#eee9df; --paper:#f6f2e9; --ink:#25251f; --muted:#68665c;
  --soft:#807b6d; --line:#c8c0b0; --accent:#94432c; --accent-ink:#fff8ee;
  --good:#45604b; --bad:#94432c; --good-bg:#e8ecdf; --bad-bg:#f2e2d7;
  --sans:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
  --serif:"Source Han Serif SC","Noto Serif SC","SimSun","Songti SC",Georgia,serif;
  --mono:"Cascadia Mono",Consolas,monospace;
}
*{box-sizing:border-box}
html{background:var(--page);scroll-behavior:smooth}
body{max-width:1440px;margin:0 auto;padding:0 48px 28px;background:var(--paper);color:var(--ink);font:14px/1.8 var(--sans);min-height:100vh;border-inline:1px solid var(--line);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}button,select{font:inherit;color:inherit}button{cursor:pointer}button:disabled{opacity:.45;cursor:not-allowed}
button:focus-visible,a:focus-visible,select:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:4px}
header,h1,h2,p{margin:0}button,a{-webkit-tap-highlight-color:transparent}
.topline{display:flex;justify-content:space-between;gap:20px;padding:14px 0 9px;border-bottom:1px solid var(--ink);font:11px/1.5 var(--mono);letter-spacing:.1em;color:var(--muted)}
.topline strong{color:var(--accent);font-weight:600}
.masthead{display:grid;grid-template-columns:180px minmax(0,1fr) 180px;gap:24px;align-items:center;padding:24px 0 20px;border-bottom:5px double var(--ink)}
.masthead-copy{text-align:center}.eyebrow{font:11px/1.5 var(--mono);letter-spacing:.24em;color:var(--muted);margin-bottom:10px}
h1{font:900 clamp(48px,5.6vw,78px)/1.15 var(--serif);letter-spacing:.08em;padding-left:.08em}
.intro{font:14px/1.8 var(--serif);letter-spacing:.12em;margin-top:10px;color:var(--muted)}
.edition-stamp{border-top:2px solid var(--ink);border-bottom:1px solid var(--ink);padding:12px 0;font:12px/1.7 var(--mono)}
.edition-stamp .date{display:block;font-size:17px;color:var(--ink);margin-bottom:5px}.edition-stamp p{color:var(--muted);font:12px/1.8 var(--sans)}
.masthead-aside{text-align:right;font:13px/1.8 var(--serif);color:var(--muted)}
.masthead-aside span{display:block;font:10px/1.5 var(--mono);letter-spacing:.1em;margin-bottom:7px;color:var(--accent)}
.recipe{font:italic 33px/1.2 Georgia,serif;color:var(--ink);margin-bottom:7px}.recipe small{font:12px/1 var(--sans);color:var(--muted);margin-inline:5px}
.command-panel{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:12px 0;border-bottom:1px solid var(--ink)}
.command-copy span{display:block;font:11px/1.5 var(--mono);letter-spacing:.12em;color:var(--accent)}
.command-copy p{font-size:12px;color:var(--muted);margin-top:4px}
.actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.actions button{border:1px solid var(--ink);border-radius:0;background:transparent;padding:7px 15px;min-height:38px;font-size:12px;transition:background .15s,color .15s}
.actions button:hover:not(:disabled){background:#e6dfd0}.actions .primary{background:var(--ink);color:var(--paper);font-weight:700}.actions .primary:hover:not(:disabled){background:var(--accent);border-color:var(--accent);color:var(--paper)}
#demo-label{display:none;border-bottom:1px solid var(--line);padding:8px 12px;color:var(--accent);font-size:12px;background:#ede5d6}
.summary{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:10px 0;color:var(--muted);font:12px/1.6 var(--sans)}.summary strong{color:var(--ink)}
.reading-head{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:9px 0;border-top:2px solid var(--ink);border-bottom:1px solid var(--ink)}
.reading-head>div:first-child{display:flex;gap:12px;align-items:center}.reading-head span{font:10px/1.4 var(--mono);letter-spacing:.12em;color:var(--accent)}.reading-head h2{font:700 21px/1.4 var(--serif)}
.filters{display:flex;gap:4px;flex-wrap:wrap}.filters button{border:0;background:transparent;padding:5px 12px;font-size:12px;color:var(--muted)}.filters button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}
main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));counter-reset:entry;gap:0}
article{min-width:0;padding:23px 22px 22px;display:flex;flex-direction:column;border-bottom:1px solid var(--line);border-right:1px solid var(--line);counter-increment:entry}
article:nth-child(3n+2){border-right:0}article:first-child{grid-column:span 2;padding-left:0;padding-right:30px;border-bottom:1px solid var(--ink)}article:nth-child(2){padding-right:0;border-bottom:1px solid var(--ink)}
article:nth-child(3n){padding-left:0}article::before{content:"第 " counter(entry,decimal-leading-zero) " 则 / READING";font:10px/1.5 var(--mono);letter-spacing:.1em;color:var(--soft);margin-bottom:12px}
article:first-child::before{content:"本期头条 / THE LEAD";color:var(--accent);font-weight:700}
.meta{display:flex;gap:7px 9px;flex-wrap:wrap;align-items:center;color:var(--soft);font:11px/1.5 var(--sans);margin-bottom:9px}
.meta span[class^="tag"]{color:var(--accent);font-weight:700;border-bottom:1px solid var(--accent);padding-bottom:1px}.tag-explore::before{content:"开眼界"}.tag-rel::before{content:"贴合兴趣"}
article h2{font:700 clamp(20px,1.65vw,26px)/1.5 var(--serif);overflow-wrap:anywhere}
article:first-child h2{font-size:clamp(30px,3vw,43px);line-height:1.35;letter-spacing:-.025em;max-width:95%}article h2 a:hover{color:var(--accent)}
.reason{margin:15px 0 22px;font:14px/1.95 var(--serif);color:var(--muted)}article:first-child .reason{font-size:16px;max-width:95%}
.fb{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:auto;padding-top:11px;border-top:1px dotted var(--line);font-size:11px;color:var(--soft)}.fb .lbl{margin-right:auto}
.fb button{border:1px solid var(--line);background:transparent;padding:3px 12px;min-height:29px;font-size:11px}.fb button:hover{border-color:var(--ink)}
.fb button.on-good{color:var(--good);border-color:var(--good);background:var(--good-bg)}.fb button.on-bad{color:var(--bad);border-color:var(--bad);background:var(--bad-bg)}
.empty{padding:70px 24px;text-align:center;border-bottom:1px solid var(--line);font:20px/1.8 var(--serif);color:var(--muted)}
.empty::before{content:"等待开版";display:block;font:700 34px/1.5 var(--serif);color:var(--ink);margin-bottom:12px}
.run-progress{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid var(--line);font-size:12px;color:var(--muted)}.run-progress[hidden]{display:none}#run-status{color:var(--accent)}summary{cursor:pointer}#run-details[open]{flex-basis:100%}#log{max-height:220px;overflow:auto;white-space:pre-wrap;padding:14px;border:1px solid var(--line);background:#ece6da;font:12px/1.8 var(--mono)}
footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:36px;padding-top:12px;border-top:3px double var(--ink);font-size:11px;color:var(--soft)}footer strong{font:700 12px/1.5 var(--serif);color:var(--ink);letter-spacing:.08em}
#toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,10px);max-width:90vw;padding:10px 20px;background:var(--ink);color:var(--paper);opacity:0;z-index:10;pointer-events:none;font-size:13px;transition:opacity .2s,transform .2s}#toast.show{opacity:1;transform:translate(-50%,0)}
@media(min-width:821px) and (max-height:800px){.masthead{padding:17px 0 15px}h1{font-size:58px}.topline{padding-top:10px}article{padding-top:18px}article:first-child h2{font-size:35px}}
@media(max-width:1000px){body{padding-inline:28px}.masthead{grid-template-columns:140px 1fr 140px;gap:16px}h1{font-size:48px}.intro{font-size:12px}.command-copy p{display:none}article{padding-inline:16px}}
@media(max-width:820px){.masthead{grid-template-columns:1fr 1fr}.masthead-copy{grid-column:1/-1;grid-row:1}.edition-stamp{border:0;padding:0}.masthead-aside{font-size:12px}.recipe{font-size:26px}main{grid-template-columns:repeat(2,minmax(0,1fr))}article:first-child{grid-column:1/-1;border-right:0;padding-right:0}article{padding-inline:18px!important;border-right:0!important}article:nth-child(even){padding-left:0!important;border-right:1px solid var(--line)!important}article:first-child{padding-left:0!important}.command-panel{align-items:flex-start}.actions{gap:6px}.actions button{padding-inline:10px}.reading-head>div:first-child{display:block}}
@media(max-width:540px){body{padding-inline:18px}.topline{font-size:9px;letter-spacing:0}.topline span:last-child{max-width:145px;text-align:right}h1{font-size:43px}.masthead{gap:12px;padding:22px 0 16px}.eyebrow{font-size:9px}.intro{letter-spacing:0}.masthead-aside span{font-size:9px}.edition-stamp .date{font-size:14px}.edition-stamp p{font-size:10px}.command-panel{display:block}.command-copy{margin-bottom:9px}.actions{justify-content:flex-start}.actions button{font-size:11px;flex:1;padding-inline:5px}.summary{font-size:11px}.reading-head{display:block}.reading-head>div:first-child{display:flex}.reading-head h2{font-size:19px}.filters{margin-top:8px}.filters button{flex:1;font-size:11px}main{grid-template-columns:1fr}article{padding-inline:0!important;border-right:0!important}article:nth-child(even){border-right:0!important}article:first-child h2{font-size:29px}article h2{font-size:23px}footer{margin-top:22px}.empty{padding:45px 10px;font-size:15px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
@media print{body{max-width:none;border:0;background:white;padding:0}.actions,.filters,.fb,.run-progress,#toast{display:none}article{break-inside:avoid}h1{font-size:48px}}
</style>
</head>
<body>

<div class="topline"><span>PERSONAL INFOFLOW <strong>· 私人日报</strong></span><span id="model-status">阅读你的世界，每日一版</span></div>
<div class="masthead">
  <div class="edition-stamp"><span class="date" id="date"></span><p>每日精选 · 个人阅读版<br>你的兴趣，是这份报纸的起点。</p></div>
  <div class="masthead-copy">
    <p class="eyebrow">THE PERSONAL INFOFLOW DAILY</p>
    <header><h1>个人信息日报</h1></header>
    <p class="intro">从熟悉的兴趣出发，给意外发现留出位置。</p>
  </div>
  <div class="masthead-aside"><span>THE READING RECIPE</span><div class="recipe" id="recipe">3 <small>贴合</small> / 7 <small>拓展</small></div><p>一部分懂你，一部分打开视野。</p></div>
</div>
<div id="demo-label" role="note"></div>
<section class="command-panel" aria-label="简报操作">
  <div class="command-copy"><span>编辑台 / EDITOR'S DESK</span><p>汇入多方消息，编成只属于你的这一版。</p></div>
  <div class="actions">
    <button class="primary" id="run">生成今日简报</button>
    <button id="refresh">重建画像并跑一轮</button>
    <button id="collect">只收集反馈</button>
  </div>
</section>
<div class="run-progress" id="run-progress" hidden>
  <span id="run-status" role="status" aria-live="polite"></span>
  <details id="run-details"><summary>查看完整日志</summary><pre id="log"></pre></details>
</div>
<div class="summary" id="summary" aria-live="polite"></div>

<div class="reading-head"><div><span>THE EDITION</span><h2>本期精选</h2></div><nav class="filters" aria-label="阅读栏目"><button data-filter="all" aria-pressed="true">全部条目</button><button data-filter="rel" aria-pressed="false">贴合兴趣</button><button data-filter="explore" aria-pressed="false">开眼界</button></nav></div>
<main id="items"></main>
<div class="empty" id="empty" style="display:none"></div>

<footer><strong>PERSONAL INFOFLOW · 私人日报</strong><span>好 / 差反馈会同步到 Obsidian 简报，让下一版更懂你。</span></footer>
<div id="toast" role="status" aria-live="polite"></div>

<script>
const $ = s => document.querySelector(s);
let today = "", running = false, starting = false, digestItems = [], activeFilter = "all";

function updateActions() {
  for (const b of [$("#run"), $("#refresh"), $("#collect")]) b.disabled = running || starting;
  $("#run").textContent = starting ? "正在启动…" : running ? "正在编报…" : "生成今日简报";
  $(".command-panel").setAttribute("aria-busy", String(running || starting));
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.classList.add("show");
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 1800);
}

async function api(path, body) {
  const r = await fetch(path, body
    ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)}
    : {});
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.status);
  return r.json();
}

/* ---- 状态轮询：驱动日志面板与按钮态 ---- */
async function poll() {
  try {
    const st = await api("/api/status");
    const dateChanged = today && today !== st.today;
    today = st.today;
    const label = $("#demo-label");
    label.textContent = st.demo_label || ""; label.style.display = st.demo_label ? "block" : "none";
    const model = st.model || {};
    $("#model-status").textContent = st.demo_label ? "示例简报 · 演示版" : model.configured ? `${model.provider} · ${model.model} · 密钥已配置` : "模型尚未配置";
    const explore = Math.round((st.exploration_ratio ?? .7) * 10);
    $("#recipe").innerHTML = `${10-explore} <small>贴合</small> / ${explore} <small>拓展</small>`;
    const run = st.run;
    if (run.running !== running) {          // 状态翻转时刷新一次页面数据
      $("#run-details").open = run.running;
      running = run.running;
      updateActions();
      if (!run.running) await loadDigest();
    }
    if (dateChanged && !run.running) await loadDigest();
    const progress = $("#run-progress");
    const log = $("#log");
    progress.hidden = !(run.lines.length || run.running || run.error || run.done);
    if (!progress.hidden) {
      const txt = run.lines.join("\n") + (run.error ? "\n✗ " + run.error
                    : run.done && !run.error ? "\n✓ 完成" : "");
      if (log.textContent !== txt) {
        log.textContent = txt;
        log.scrollTop = log.scrollHeight;
      }
      const result = run.result || {};
      const feedback = result.feedback || {};
      const overall = feedback.quality && feedback.quality.overall;
      const rate = overall == null ? "暂无统计" : `${Math.round(overall * 100)}%`;
      const outcome = result.digest_path
        ? `精选 ${result.picked} 条`
        : `新增标注 ${feedback.new ?? 0} 条`;
      $("#run-status").textContent = run.running
        ? `运行中 · ${(run.lines.at(-1) || "正在准备…").replace(/\bNone\b/g, "暂无统计")}`
        : run.error ? "本轮失败 · 请查看完整日志"
        : run.done ? `本轮完成 · ${outcome} · 反馈命中率 ${rate}`
        : "准备中";
    }
    if (run.done && !run.running && !starting && !poll._reported) {
      poll._reported = true;
      toast(run.error ? "失败了，请展开日志" : "这一轮完成");
    }
    if (run.running) poll._reported = false;
    if (!st.digest_exists && !run.running)
      $("#summary").textContent = "今天还没有简报。点上面的「生成今日简报」开始编报。";
  } catch (e) { $("#summary").textContent = "暂时无法连接服务，请确认程序仍在运行。"; }
}

/* ---- 简报渲染 ---- */
function itemHTML(it) {
  const dup = it.dup_count > 1 ? ` · 也被 ${it.dup_count - 1} 个其他源报道` : "";
  return `<article data-link="${esc(it.link)}">
    <div class="meta"><span class="tag-${it.bucket}"></span><span>${esc(it.source)}${dup}</span></div>
    <h2><a href="${esc(it.link)}" target="_blank" rel="noopener">${esc(it.title)}</a></h2>
    <p class="reason">${esc(it.reason)}</p>
    <div class="fb"><span class="lbl">这条对我</span>
      <button data-v="pos" aria-pressed="${it.verdict==='pos'}" class="${it.verdict==="pos"?"on-good":""}">好</button>
      <button data-v="neg" aria-pressed="${it.verdict==='neg'}" class="${it.verdict==="neg"?"on-bad":""}">差</button>
    </div>
  </article>`;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g,
    c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function renderSummary(st) {
  $("#summary").innerHTML = `<strong>今日精选 ${st.items} 条</strong><span>已标注 ${st.marked} 条 · 点击已选反馈可取消</span>`;
}

async function loadDigest() {
  try {
  const [st, dg] = await Promise.all([api("/api/status"), api("/api/digest")]);
  today = dg.date;
  $("#date").textContent = dg.date;
  $("#empty").style.display = "none";
  renderSummary(st);
  if (!dg.exists) {
    digestItems = [];
    $("#items").innerHTML = "";
    $("#empty").style.display = "";
    $("#empty").textContent = "点击「生成今日简报」，让值得读的消息汇入这一页。";
    return;
  }
  digestItems = dg.items;
  renderItems();
  } catch {
    digestItems = [];
    $("#items").innerHTML = "";
    $("#empty").style.display = "";
    $("#empty").setAttribute("role", "alert");
    $("#empty").innerHTML = '简报暂时无法加载，请检查本地服务。 <button type="button" id="retry-digest">重试</button>';
  }
}

function renderItems() {
  const visible = digestItems.filter(it => activeFilter === "all" || it.bucket === activeFilter);
  $("#items").innerHTML = visible.map(itemHTML).join("");
  $("#empty").style.display = visible.length ? "none" : "";
  $("#empty").textContent = digestItems.length ? "这一栏目暂时没有条目，试试其他栏目。" : "点击「生成今日简报」，让值得读的消息汇入这一页。";
}
/* ---- 事件 ---- */
document.addEventListener("click", async e => {
  if (e.target.closest("#retry-digest")) { void loadDigest(); return; }
  const filter = e.target.closest("[data-filter]");
  if (filter) {
    activeFilter = filter.dataset.filter;
    for (const b of document.querySelectorAll("[data-filter]")) b.setAttribute("aria-pressed", String(b === filter));
    renderItems();
    return;
  }
  const btn = e.target.closest(".fb button");
  if (btn) {
    const art = btn.closest("article");
    if (art.getAttribute("aria-busy") === "true") return;
    const link = art.dataset.link;
    const cur = art.querySelector("button.on-good,button.on-bad");
    const v = (cur === btn) ? null : btn.dataset.v;   // 再点一次取消
    art.setAttribute("aria-busy", "true");
    for (const b of art.querySelectorAll(".fb button")) b.disabled = true;
    try {
      const result = await api("/api/feedback", {date: today, link, verdict: v});
      if (!result.ok) throw new Error("没有找到对应条目，请刷新简报后重试");
      for (const b of art.querySelectorAll(".fb button")) {
        b.classList.remove("on-good", "on-bad"); b.disabled = false;
        b.setAttribute("aria-pressed", "false");
      }
      if (v) {
        btn.setAttribute("aria-pressed", "true");
        btn.classList.add(v === "pos" ? "on-good" : "on-bad");
      }
      const item = digestItems.find(it => it.link === link);
      if (item) item.verdict = v;
      toast(v === "pos" ? "记下了：好" : v === "neg" ? "记下了：差" : "已清除标注");
      renderSummary({items:digestItems.length, marked:digestItems.filter(item=>item.verdict).length});
    } catch (err) { toast("写入失败：" + err.message); }
    finally {
      art.setAttribute("aria-busy", "false");
      for (const b of art.querySelectorAll(".fb button")) b.disabled = false;
    }
    return;
  }
});

$("#run").onclick = () => start({});
$("#refresh").onclick = () => start({refresh_profile: true});
$("#collect").onclick = () => start({feedback_only: true});

async function start(body) {
  if (running || starting) return;
  starting = true;
  updateActions();
  let started = false;
  try {
    const r = await api("/api/run", body);
    if (!r.ok) throw new Error(r.error || "启动失败");
    started = true;
    poll._reported = false;
    if (!running) $("#run-details").open = false;
  } catch (err) { toast(err.message); }
  finally { starting = false; updateActions(); }
  if (started) await poll();
}

poll();
setInterval(poll, 1500);
loadDigest().catch(e => { $("#empty").style.display = ""; $("#empty").textContent = "简报加载失败：" + e.message; });
</script>
</body>
</html>
"""

/* ==========================================================================
   CCDASH — Application Logic
   Open-source usage analytics dashboard for Claude Code CLI
   ========================================================================== */

const notyf = new Notyf({ duration:3000, position:{x:'right',y:'top'}, types:[{type:'success',background:'#10b981',icon:false},{type:'error',background:'#f87171',icon:false}] });

/* ---- i18n (Complete) ---- */
const I18N = {
  zh: {
    refresh:'刷新', plan:'套餐', usage5h:'5h 用量', reset:'重置',
    today:'今日', msgs:'消息', sessions_l:'会话', weekUsage:'本周',
    totalMsgs:'总消息', totalSessions:'总会话', totalTokens:'总 Token',
    inputTokens:'输入', outputTokens:'输出',
    cacheHit:'缓存命中', cacheRate:'命中率', cacheCreate:'缓存写', cacheRead:'缓存读',
    projects:'项目', input:'输入', output:'输出',
    dailyTrend:'趋势', tokenDist:'Token', heatmap:'热力图',
    dailyTrendDesc:'消息、会话和工具调用的每日统计',
    modelUsage:'模型用量', modelUsageDesc:'各模型 Token 用量与缓存效率',
    model:'模型', calls:'调用', hitRate:'命中率',
    cacheAnalysis:'缓存分析', cacheAnalysisDesc:'缓存命中率分布',
    directInput:'直接输入',
    projectTop:'项目 TOP 10', projectTopDesc:'按 Token 用量排序', project:'项目',
    recentSessions:'最近会话', recentSessionsDesc:'最近活跃的会话',
    allProjects:'全部', search:'搜索', time:'时间', content:'内容',
    liveLog:'今日实时', liveLogDesc:'实时 API 调用监控',
    activeSessions:'活跃会话',
    filterTitle:'筛选', startDate:'开始', endDate:'结束',
    allModels:'全部模型', apply:'应用', resetFilters:'重置',
    usageLog:'使用记录', usageLogDesc:'API 调用明细',
    status:'状态', stopAutoRefresh:'停止刷新', startAutoRefresh:'开始刷新',
    modelCount:'模型数', todayCalls:'今日', todayTools:'工具', avgDuration:'平均耗时', avgTtft:'平均首字',
    perPage:'条/页', ttft:'首字', duration:'耗时',
    loading:'加载中...',
    navOverview:'概览', navAnalytics:'分析', navLive:'实时', navLogs:'日志'
  },
  en: {
    refresh:'Refresh', plan:'Plan', usage5h:'5h Usage', reset:'Resets in',
    today:'Today', msgs:'msgs', sessions_l:'sessions', weekUsage:'Weekly',
    totalMsgs:'Total Messages', totalSessions:'Total Sessions', totalTokens:'Total Tokens',
    inputTokens:'Input', outputTokens:'Output',
    cacheHit:'Cache Hit', cacheRate:'Hit Rate', cacheCreate:'Cache W', cacheRead:'Cache R',
    projects:'Projects', input:'Input', output:'Output',
    dailyTrend:'Trend', tokenDist:'Token', heatmap:'Heatmap',
    dailyTrendDesc:'Daily stats for messages, sessions, tools',
    modelUsage:'Model Usage', modelUsageDesc:'Token usage & cache efficiency',
    model:'Model', calls:'Calls', hitRate:'Hit%',
    cacheAnalysis:'Cache Analysis', cacheAnalysisDesc:'Cache hit rate distribution',
    directInput:'Direct Input',
    projectTop:'Project TOP 10', projectTopDesc:'Projects by token usage', project:'Project',
    recentSessions:'Recent Sessions', recentSessionsDesc:'Recently active sessions',
    allProjects:'All', search:'Search', time:'Time', content:'Content',
    liveLog:'Today Live', liveLogDesc:'Real-time API call monitoring',
    activeSessions:'Active Sessions',
    filterTitle:'Filters', startDate:'Start', endDate:'End',
    allModels:'All Models', apply:'Apply', resetFilters:'Reset',
    usageLog:'Usage Logs', usageLogDesc:'Detailed API call records',
    status:'Status', stopAutoRefresh:'Stop Refresh', startAutoRefresh:'Auto Refresh',
    modelCount:'Models', todayCalls:'Today', todayTools:'Tools', avgDuration:'Avg Duration', avgTtft:'Avg TTFT',
    perPage:'per page', ttft:'TTFT', duration:'Duration',
    loading:'Loading...',
    navOverview:'Overview', navAnalytics:'Analytics', navLive:'Live Stream', navLogs:'System Logs'
  }
};
let curLang = localStorage.getItem('ccdash_lang') || 'zh';

function applyI18n() {
  const t = I18N[curLang] || I18N.zh;
  document.querySelectorAll('[data-i]').forEach(el => {
    if (t[el.dataset.i]) el.textContent = t[el.dataset.i];
  });
  const lb = document.getElementById('langBtn');
  if (lb) lb.querySelector('span').textContent = curLang === 'zh' ? 'EN' : '中';
  const si = document.getElementById('sSearch');
  if (si) si.placeholder = curLang === 'zh' ? '搜索会话...' : 'Search sessions...';
  // Update page title
  const titleMap = { overview:'navOverview', analytics:'navAnalytics', live:'navLive', logs:'navLogs' };
  const curPage = localStorage.getItem('ccdash_page') || 'overview';
  const pt = document.getElementById('pageTitle');
  if (pt && titleMap[curPage]) pt.textContent = t[titleMap[curPage]] || curPage;
}

function toggleLang() {
  curLang = curLang === 'zh' ? 'en' : 'zh';
  localStorage.setItem('ccdash_lang', curLang);
  applyI18n();
  renderCharts();
  loadLive();
  loadLogs();
}

/* ---- Theme ---- */
function initTheme() {
  const s = localStorage.getItem('ccdash_theme') || 'dark';
  document.body.dataset.theme = s;
  updateThemeIcon(s);
}

function updateThemeIcon(t) {
  const b = document.getElementById('themeBtn');
  if (!b) return;
  const i = b.querySelector('i');
  if (i) { i.className = t === 'dark' ? 'ph ph-sun' : 'ph ph-moon'; }
}

function toggleTheme() {
  const n = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
  document.body.dataset.theme = n;
  localStorage.setItem('ccdash_theme', n);
  updateThemeIcon(n);
  renderCharts();
  if (window._ringData) drawRing(...window._ringData);
}
initTheme();

/* ---- Filter ---- */
function toggleFilter() {
  document.getElementById('filterToggle').classList.toggle('open');
  document.getElementById('filterBody').classList.toggle('open');
}

/* ---- Formatters ---- */
function fmt(n) {
  if (n == null) return '0';
  if (n >= 1e9) return (n/1e9).toFixed(2)+'B';
  if (n >= 1e6) return (n/1e6).toFixed(2)+'M';
  if (n >= 1e3) return (n/1e3).toFixed(1)+'K';
  return n.toLocaleString();
}
function fmtRaw(n) { return n == null ? 0 : n; }
function fmtT(ms) {
  if (!ms) return '—';
  const d = new Date(ms);
  return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}
function fmtISO(s) {
  try { return new Date(s).toLocaleTimeString(curLang==='zh'?'zh-CN':'en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'}); }
  catch { return s; }
}

/* ---- relativeTime (frontend, bilingual) ---- */
function relativeTime(s) {
  try {
    const diff = (new Date() - new Date(s)) / 1000;
    if (diff < 60) return curLang==='zh' ? `${Math.floor(diff)}秒前` : `${Math.floor(diff)}s ago`;
    if (diff < 3600) return curLang==='zh' ? `${Math.floor(diff/60)}分钟前` : `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return curLang==='zh' ? `${Math.floor(diff/3600)}小时前` : `${Math.floor(diff/3600)}h ago`;
    return curLang==='zh' ? `${Math.floor(diff/86400)}天前` : `${Math.floor(diff/86400)}d ago`;
  } catch { return s; }
}

/* ---- Model colors (Zinc palette) ---- */
const MC = {
  'claude-opus-4-6':'#60a5fa',
  'claude-sonnet-4-6':'#60a5fa',
  'claude-sonnet-4-5':'#c084fc',
  'claude-sonnet-4-5-20250929':'#c084fc',
  'claude-haiku-4-5-20251001':'#4ade80'
};
function mC(m) { return MC[m] || '#2dd4bf'; }
function mS(m) { return m.replace('claude-','').replace(/-\d{8}$/,''); }

/* ---- API helper ---- */
async function api(p) { return (await fetch(p)).json(); }

/* ---- CountUp ---- */
const _cu = {};
function animateValue(id, val, sfx) {
  sfx = sfx || '';
  const el = document.getElementById(id);
  if (!el) return;
  let n = val, ds = sfx;
  if (typeof val === 'string') {
    const m = val.match(/^([\d.]+)\s*(.*)$/);
    if (m) { n = parseFloat(m[1]); ds = m[2] || sfx; }
    else { el.textContent = val; return; }
  }
  if (isNaN(n)) { el.textContent = val; return; }
  try {
    const o = { startVal:0, duration:1.8, separator:',', suffix:ds, decimalPlaces:n>=100?0:n>=1?1:2, useEasing:true };
    if (_cu[id]) _cu[id].update(n);
    else { const c = new countUp.CountUp(id, n, o); if (!c.error) { c.start(); _cu[id] = c; } else el.textContent = val; }
  } catch { el.textContent = val; }
}

function apexTheme() {
  return { mode: document.body.dataset.theme === 'dark' ? 'dark' : 'light', palette:'palette1' };
}

/* ---- Sparkline renderer ---- */
function renderSparkline(svgId, data, color) {
  const svg = document.getElementById(svgId);
  if (!svg || !data || !data.length) return;
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => `${(i / Math.max(data.length - 1, 1)) * 100},${30 - (v / max) * 26}`).join(' ');
  svg.innerHTML = `<defs><linearGradient id="sg-${svgId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${color}" stop-opacity="0.3"/><stop offset="100%" stop-color="${color}" stop-opacity="0"/></linearGradient></defs><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><polygon points="0,30 ${pts} 100,30" fill="url(#sg-${svgId})"/>`;
}

/* ---- Debounce for session search ---- */
let _searchTimer;
function debounceSearch() { clearTimeout(_searchTimer); _searchTimer = setTimeout(loadSess, 400); }

/* ===== Page Switching ===== */
function switchPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
  const pageEl = document.getElementById('page-' + pageId);
  if (pageEl) pageEl.classList.add('active');
  const navEl = document.querySelector(`.nav-item[data-page="${pageId}"]`);
  if (navEl) navEl.classList.add('active');
  localStorage.setItem('ccdash_page', pageId);
  // Update page title
  const t = I18N[curLang] || I18N.zh;
  const titleMap = { overview:'navOverview', analytics:'navAnalytics', live:'navLive', logs:'navLogs' };
  const pt = document.getElementById('pageTitle');
  if (pt && titleMap[pageId]) pt.textContent = t[titleMap[pageId]] || pageId;
  // Lazy load
  if (pageId === 'overview' && !chA) renderCharts();
  if (pageId === 'live') { loadLive(); }
  if (pageId === 'analytics') { loadModels(); loadProjects(); }
  if (pageId === 'logs') { loadLogs(); loadSess(); }
}

/* ===== Data Loading ===== */
let _cdI, curRange = '7d';

/* -- Gauge update -- */
function updateGauge(pct) {
  const circ = 2 * Math.PI * 52; // ~326.73
  const offset = circ - (pct / 100) * circ;
  const fill = document.getElementById('gaugeFill');
  if (fill) {
    fill.style.strokeDashoffset = offset;
    fill.style.stroke = pct > 80 ? 'var(--red)' : pct > 50 ? 'var(--orange)' : 'var(--green)';
  }
  const val = document.getElementById('gaugeVal');
  if (val) val.textContent = pct + '%';
}

async function loadStatus() {
  const d = await api('/api/status');
  document.getElementById('pName').textContent = d.profile_name || '—';
  updateGauge(d.utilization || 0);
  document.getElementById('tMsg').textContent = d.today_messages;
  document.getElementById('tSes').textContent = d.today_sessions;
  if (d.resets_at) {
    const rt = new Date(d.resets_at);
    clearInterval(_cdI);
    function u() {
      const df = rt - new Date();
      if (df <= 0) { document.getElementById('cd').textContent = '—'; return; }
      const h = Math.floor(df/36e5), m = Math.floor((df%36e5)/6e4), s = Math.floor((df%6e4)/1e3);
      document.getElementById('cd').textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }
    u(); _cdI = setInterval(u, 1000);
  }
  try {
    const dd = await api('/api/daily?days=7');
    const wk = dd.activity.reduce((s, a) => s + a.messages, 0);
    document.getElementById('weekDots').innerHTML = dd.activity.map(a =>
      `<div class="week-dot${a.messages>0?' filled':''}" title="${a.date}: ${a.messages}"></div>`
    ).join('');
    document.getElementById('weekPct').textContent = wk + ' msgs';
    // Build sparkline data from last 7 days
    window._spark7 = {
      msgs: dd.activity.map(a => a.messages),
      sessions: dd.activity.map(a => a.sessions),
      tools: dd.activity.map(a => a.tools || 0)
    };
    // Weekly gauge — fetch from claude.ai API
    try {
      const usage = await api('/api/claude-usage');
      if (usage && !usage.error) {
        // 7-day overall
        const s7 = usage.seven_day;
        if (s7) {
          const weekGauge = document.getElementById('weekGaugeFill');
          const weekGaugeVal = document.getElementById('weekGaugeVal');
          const weekTokensEl = document.getElementById('weekTokens');
          const pct = Math.round(s7.utilization || 0);
          const circ = 326.73;
          if (weekGauge) {
            weekGauge.style.strokeDashoffset = circ - (circ * pct / 100);
            weekGauge.style.stroke = pct > 80 ? 'var(--red)' : pct > 50 ? 'var(--orange)' : 'var(--blue)';
          }
          if (weekGaugeVal) weekGaugeVal.textContent = pct + '%';
          if (weekTokensEl) {
            const resetDt = s7.resets_at ? new Date(s7.resets_at) : null;
            const resetStr = resetDt ? resetDt.toLocaleDateString(curLang==='zh'?'zh-CN':'en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
            weekTokensEl.textContent = resetStr ? (curLang==='zh'?'重置: ':'Reset: ')+resetStr : pct+'%';
          }
        }
        // Update 5h gauge too (more accurate than statusline cache)
        const s5 = usage.five_hour;
        if (s5) updateGauge(Math.round(s5.utilization || 0));
      }
    } catch(e) { console.warn('Claude usage fetch failed:', e); }
  } catch(e) { console.error(e); }
}

async function loadOverview() {
  const d = await api('/api/overview');
  animateValue('cMsg', fmtRaw(d.total_messages));
  animateValue('cSes', fmtRaw(d.total_sessions));
  // Use fmt() for large token counts to avoid truncation
  document.getElementById('cTok').textContent = fmt(d.total_tokens);
  document.getElementById('cIn').textContent = fmt(d.total_input);
  document.getElementById('cOut').textContent = fmt(d.total_output);
  document.getElementById('cCR').textContent = fmt(d.total_cache_read);
  document.getElementById('cCC').textContent = fmt(d.total_cache_create);
  document.getElementById('cRate').textContent = (d.cache_hit_rate || 0) + '%';
  document.getElementById('cProj').textContent = d.total_projects;
  animateValue('cModels', fmtRaw(d.total_models || 0));
  document.getElementById('cTodayCalls').textContent = d.today_messages || 0;
  document.getElementById('cTodayTools').textContent = d.today_tools || 0;
  document.getElementById('bdToday').textContent = (curLang==='zh' ? '今日 +' : 'Today +') + d.today_messages;
  // RPM, TPM, Avg Duration, Avg TTFT
  const rpmEl = document.getElementById('rpmVal'); if (rpmEl) rpmEl.textContent = d.rpm || 0;
  const tpmEl = document.getElementById('tpmVal'); if (tpmEl) tpmEl.textContent = fmt(d.tpm || 0);
  const avgDurEl = document.getElementById('avgDurVal');
  if (avgDurEl) avgDurEl.textContent = d.avg_duration_ms ? (d.avg_duration_ms < 1000 ? d.avg_duration_ms + 'ms' : (d.avg_duration_ms / 1000).toFixed(1) + 's') : '—';
  const avgTtftEl = document.getElementById('avgTtftVal');
  if (avgTtftEl) avgTtftEl.textContent = d.avg_ttft_ms ? (d.avg_ttft_ms < 1000 ? d.avg_ttft_ms + 'ms' : (d.avg_ttft_ms / 1000).toFixed(1) + 's') : '—';
  // Cost is updated by loadModels() to ensure consistency with analytics page
  window._ringData = [d.total_input||0, d.total_cache_read||0, d.total_cache_create||0, d.cache_hit_rate||0];
  drawRing(...window._ringData);
  // Render sparklines if data available — each card gets a distinct color matching its icon
  if (window._spark7) {
    renderSparkline('sparkMsgs', window._spark7.msgs, '#60a5fa');         // Messages (si-a, blue icon)
    renderSparkline('sparkTokens', window._spark7.sessions, '#22d3ee');   // Tokens (si-b, cyan icon)
    renderSparkline('sparkCache', window._spark7.tools, '#4ade80');       // Cache (si-g, green icon)
    renderSparkline('sparkModels', window._spark7.msgs.map((v,i) => v + (window._spark7.sessions[i]||0)), '#c084fc'); // Models (si-p, purple icon)
  }
}

function drawRing(inp, cr, cc, rate) {
  document.getElementById('rlH').textContent = fmt(cr);
  document.getElementById('rlC').textContent = fmt(cc);
  document.getElementById('rlD').textContent = fmt(inp);
  if (window._ringChart) window._ringChart.destroy();
  const dk = document.body.dataset.theme === 'dark';
  window._ringChart = new ApexCharts(document.getElementById('chartRing'), {
    chart: { type:'donut', height:190, background:'transparent', foreColor:dk?'#a1a1aa':'#71717a' },
    series: [cr, cc, inp],
    labels: [curLang==='zh'?'缓存命中':'Cache Hit', curLang==='zh'?'缓存创建':'Cache Create', curLang==='zh'?'直接输入':'Direct'],
    colors: ['#4ade80', '#fbbf24', '#60a5fa'],
    plotOptions: { pie:{ donut:{ size:'65%', labels:{ show:true, name:{show:false}, value:{ show:true, fontSize:'17px', fontWeight:700, fontFamily:'JetBrains Mono', color:dk?'#e2e8f0':'#09090b', formatter:()=>rate+'%' }, total:{ show:true, label:'Rate', formatter:()=>rate+'%' } } } } },
    dataLabels: { enabled:false },
    legend: { show:false },
    stroke: { width:0 },
    theme: apexTheme(),
    tooltip: { style:{fontFamily:'JetBrains Mono',fontSize:'11px'}, y:{ formatter:v=>fmt(v) } }
  });
  window._ringChart.render();
}

/* ---- Cost calculation for daily chart ---- */
const MODEL_PRICING_JS = {
  'claude-opus-4-6':{input:5,output:25,cache_read:0.5,cache_create:6.25},
  'claude-opus-4-5-20251101':{input:5,output:25,cache_read:0.5,cache_create:6.25},
  'claude-opus-4-1-20250805':{input:15,output:75,cache_read:1.5,cache_create:18.75},
  'claude-opus-4-20250514':{input:15,output:75,cache_read:1.5,cache_create:18.75},
  'claude-sonnet-4-6':{input:3,output:15,cache_read:0.3,cache_create:3.75},
  'claude-sonnet-4-5':{input:3,output:15,cache_read:0.3,cache_create:3.75},
  'claude-sonnet-4-5-20250929':{input:3,output:15,cache_read:0.3,cache_create:3.75},
  'claude-sonnet-4-20250514':{input:3,output:15,cache_read:0.3,cache_create:3.75},
  'claude-haiku-4-5-20251001':{input:1,output:5,cache_read:0.1,cache_create:1.25},
};
const DEFAULT_PRICING_JS = {input:3,output:15,cache_read:0.3,cache_create:3.75};

function calcDayCost(byModel) {
  let cost = 0;
  for (const [model, data] of Object.entries(byModel || {})) {
    const p = MODEL_PRICING_JS[model] || DEFAULT_PRICING_JS;
    cost += (data.input * p.input + data.output * p.output +
             data.cache_read * p.cache_read + data.cache_create * p.cache_create) / 1000000;
  }
  return Math.round(cost * 100) / 100;
}

let chA, chT;
async function loadCharts() {
  const days = parseInt(curRange) || 30;
  const d = await api('/api/daily?days=' + days);
  const dates = d.activity.map(a => a.date.slice(5));
  const dk = document.body.dataset.theme === 'dark';
  const fg = dk ? '#71717a' : '#a1a1aa';

  /* --- Cost data from token byModel --- */
  const costData = d.tokens.map(t => calcDayCost(t.byModel));

  if (chA) chA.destroy();
  chA = new ApexCharts(document.getElementById('chartAct'), {
    chart: { type:'area', height:290, background:'transparent', foreColor:fg, toolbar:{show:false}, animations:{enabled:true,easing:'easeinout',speed:900} },
    series: [
      { name:curLang==='zh'?'消息':'Messages', data:d.activity.map(a=>a.messages) },
      { name:curLang==='zh'?'会话':'Sessions', data:d.activity.map(a=>a.sessions) },
      { name:curLang==='zh'?'工具':'Tools', data:d.activity.map(a=>a.tools) },
      { name:curLang==='zh'?'成本($)':'Cost($)', data:costData }
    ],
    colors: ['#4ade80','#60a5fa','#c084fc','#fbbf24'],
    xaxis: { categories:dates, labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono',colors:fg}}, axisBorder:{show:false}, axisTicks:{show:false} },
    yaxis: [
      { seriesName:curLang==='zh'?'消息':'Messages', labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono'}, formatter:v=>fmt(v)}, axisBorder:{show:false} },
      { seriesName:curLang==='zh'?'会话':'Sessions', show:false },
      { seriesName:curLang==='zh'?'工具':'Tools', show:false },
      { seriesName:curLang==='zh'?'成本($)':'Cost($)', opposite:true, labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono',color:'#fbbf24'}, formatter:v=>'$'+v.toFixed(1)}, axisBorder:{show:false} }
    ],
    grid: { show:false },
    stroke: { curve:'smooth', width:[2.5,2.5,2.5,2.5] },
    fill: { type:'gradient', gradient:{shadeIntensity:1,opacityFrom:0.25,opacityTo:0.02,stops:[0,90,100]} },
    dataLabels: { enabled:false },
    legend: { position:'top', horizontalAlign:'left', fontSize:'10px', fontFamily:'Inter', labels:{colors:fg}, markers:{shape:'circle',size:4} },
    tooltip: { theme:dk?'dark':'light', style:{fontFamily:'JetBrains Mono',fontSize:'11px'}, y:{formatter:(v,{seriesIndex})=>seriesIndex===3?'$'+v.toFixed(2):fmt(v)} },
    theme: apexTheme()
  });
  chA.render();

  const am = new Set();
  d.tokens.forEach(t => Object.keys(t.byModel || {}).forEach(m => am.add(m)));

  if (chT) chT.destroy();
  chT = new ApexCharts(document.getElementById('chartTok'), {
    chart: { type:'bar', height:290, stacked:true, background:'transparent', foreColor:fg, toolbar:{show:false}, animations:{enabled:true,speed:800} },
    series: [...am].map(m => ({ name:mS(m), data:d.tokens.map(t => { const v=(t.byModel||{})[m]; return v ? v.input+v.output+v.cache_read+v.cache_create : 0; }) })),
    colors: [...am].map(m => mC(m)),
    xaxis: { categories:dates, labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono'}}, axisBorder:{show:false}, axisTicks:{show:false} },
    yaxis: { labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono'}, formatter:v=>fmt(v)} },
    grid: { show:false },
    plotOptions: { bar:{borderRadius:4,columnWidth:'60%'} },
    dataLabels: { enabled:false },
    legend: { position:'top', horizontalAlign:'left', fontSize:'10px', fontFamily:'Inter', labels:{colors:fg} },
    tooltip: { theme:dk?'dark':'light', style:{fontFamily:'JetBrains Mono',fontSize:'11px'}, y:{formatter:v=>fmt(v)} },
    theme: apexTheme()
  });
  chT.render();
}

let chHm;
async function loadHeatmap() {
  const days = parseInt(curRange) || 30;
  const d = await api('/api/hourly?days=' + days);
  const hm = d.heatmap;
  const dk = document.body.dataset.theme === 'dark';
  const fg = dk ? '#71717a' : '#a1a1aa';
  const dn = curLang==='zh' ? ['周一','周二','周三','周四','周五','周六','周日'] : ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const series = dn.map((n,i) => ({ name:n, data:Array.from({length:24},(_,h)=>({x:h+':00',y:hm[i][h]})) })).reverse();

  if (chHm) chHm.destroy();
  chHm = new ApexCharts(document.getElementById('chartHm'), {
    chart: { type:'heatmap', height:240, background:'transparent', foreColor:fg, toolbar:{show:false}, animations:{enabled:true,speed:500} },
    series,
    colors: ['#10b981'],
    plotOptions: { heatmap:{ radius:6, enableShades:true, shadeIntensity:0.6, colorScale:{ ranges:[{from:0,to:0,color:dk?'#1a1e27':'#f1f2f6',name:'0'}] } } },
    dataLabels: { enabled:false },
    xaxis: { labels:{style:{fontSize:'8px',fontFamily:'JetBrains Mono'}} },
    yaxis: { labels:{style:{fontSize:'9px',fontFamily:'Inter'}} },
    grid: { show:false },
    stroke: { width:3, colors:[dk?'#13161d':'#ffffff'] },
    tooltip: { theme:dk?'dark':'light', style:{fontFamily:'JetBrains Mono',fontSize:'11px'} },
    theme: apexTheme()
  });
  chHm.render();
}

/* Unified renderCharts: calls both chart loaders + heatmap */
async function renderCharts() {
  await loadCharts();
  if (document.getElementById('pHm').style.display !== 'none') {
    await loadHeatmap();
  }
}

function swTab(t) {
  const tm = { act:'dailyTrend', tok:'tokenDist', hm:'heatmap' };
  document.querySelectorAll('.tabs .tab').forEach(el => el.classList.toggle('on', el.dataset.i === tm[t]));
  document.getElementById('pAct').style.display = t === 'act' ? '' : 'none';
  document.getElementById('pTok').style.display = t === 'tok' ? '' : 'none';
  document.getElementById('pHm').style.display = t === 'hm' ? '' : 'none';
  if (t === 'hm') loadHeatmap();
}

function setRange(r) {
  curRange = r;
  document.querySelectorAll('.pill').forEach(el => el.classList.toggle('on', el.textContent === r.toUpperCase()));
  loadCharts();
  if (document.getElementById('pHm').style.display !== 'none') loadHeatmap();
}

async function loadModels() {
  const d = await api('/api/models');
  const ms = Object.entries(d.models).sort((a,b) => {
    const ta = a[1].input+a[1].output+a[1].cache_read+a[1].cache_create;
    const tb = b[1].input+b[1].output+b[1].cache_read+b[1].cache_create;
    return tb - ta;
  });
  const tot = ms.reduce((s,[,v]) => s+v.input+v.output+v.cache_read+v.cache_create, 0);
  document.getElementById('tbMod').innerHTML = ms.map(([m,v]) => {
    const t = v.input+v.output+v.cache_read+v.cache_create;
    const p = tot > 0 ? (t/tot*100).toFixed(1) : 0;
    const ai = v.input+v.cache_read+v.cache_create;
    const hr = ai > 0 ? (v.cache_read/ai*100).toFixed(0) : 0;
    const cost = v.cost_usd != null ? '$'+v.cost_usd.toFixed(2) : '—';
    return `<tr><td><span class="mdot" style="background:${mC(m)}"></span>${mS(m)}</td><td class="mono"><span class="tk-in">↓</span>${fmt(v.input)}</td><td class="mono"><span class="tk-out">↑</span>${fmt(v.output)}</td><td class="mono"><span class="tk-cr">⟲</span>${fmt(v.cache_read)}</td><td class="mono"><span class="tk-cw">⟳</span>${fmt(v.cache_create)}</td><td>${v.calls}</td><td>${hr}%</td><td style="color:var(--green);font-weight:600">${cost}</td></tr>`;
  }).join('');
  // Update overview cost badge from models total (single source of truth)
  const totalModelCost = ms.reduce((s,[,v]) => s + (v.cost_usd||0), 0);
  const costEl = document.getElementById('totalCost');
  if (costEl) costEl.textContent = '$' + (totalModelCost >= 1000 ? (totalModelCost/1000).toFixed(1)+'K' : totalModelCost.toFixed(2));
  const sel = document.getElementById('filterModel');
  if (sel.options.length <= 1) ms.forEach(([m]) => { const o = document.createElement('option'); o.value = m; o.textContent = mS(m); sel.appendChild(o); });
}

async function loadProjects() {
  const d = await api('/api/projects');
  const tot = d.projects.reduce((s,p) => s+p.tokens_total, 0);
  document.getElementById('tbProj').innerHTML = d.projects.map(p => {
    const pc = tot > 0 ? (p.tokens_total/tot*100).toFixed(1) : 0;
    let sb = '', dn = p.name || '';
    if (dn.includes('(local)')) {
      const lbl = curLang==='zh' ? '本地' : 'LOCAL';
      sb = `<span style="font:600 8px var(--font);padding:1px 6px;border-radius:4px;background:var(--accent-bg);color:var(--accent);margin-left:4px">${lbl}</span>`;
      dn = dn.replace(/\s*\(local\)/, '');
    } else if (dn.includes('(cloud)')) {
      const lbl = curLang==='zh' ? '云端' : 'CLOUD';
      sb = `<span style="font:600 8px var(--font);padding:1px 6px;border-radius:4px;background:var(--blue-bg);color:var(--blue);margin-left:4px">${lbl}</span>`;
      dn = dn.replace(/\s*\(cloud\)/, '');
    }
    return `<tr><td title="${p.dir_name||''}">${dn}${sb}</td><td>${fmt(p.messages)}</td><td>${p.sessions}</td><td class="mono">${fmt(p.tokens_total)}</td><td>${pc}%</td></tr>`;
  }).join('');
  const sel = document.getElementById('filterProject');
  if (sel.options.length <= 1) d.projects.forEach(p => { const o = document.createElement('option'); o.value = p.name; o.textContent = p.name; sel.appendChild(o); });
}

async function loadSess() {
  const f = document.getElementById('sFilt').value;
  const q = document.getElementById('sSearch').value.trim();
  let url = '/api/sessions?limit=40';
  if (f) url += `&project=${encodeURIComponent(f)}`;
  if (q) url += `&q=${encodeURIComponent(q)}`;
  const d = await api(url);
  const sel = document.getElementById('sFilt');
  if (sel.options.length <= 1 && d.projects) d.projects.forEach(p => { const o = document.createElement('option'); o.value = p; o.textContent = p.split('/').pop() || '~'; sel.appendChild(o); });
  document.getElementById('tbSess').innerHTML = d.sessions.map(s =>
    `<tr><td>${fmtT(s.timestamp)}</td><td title="${s.project}">${s.projectShort}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${s.firstPrompt||'—'}</td></tr>`
  ).join('');
}

async function loadLive() {
  const d = await api('/api/live');
  const badge = document.getElementById('liveBadge');
  if (badge) badge.textContent = d.calls.length;
  document.getElementById('liveN').textContent = d.calls.length + (curLang==='zh' ? ' 条' : ' calls');
  document.getElementById('tbLive').innerHTML = d.calls.slice(0,80).map(c => {
    const cost = c.cost_usd != null ? '$'+c.cost_usd.toFixed(4) : '—';
    return `<tr><td>${fmtISO(c.timestamp)}</td><td><span class="mdot" style="background:${mC(c.model)}"></span>${mS(c.model)}</td><td style="max-width:90px;overflow:hidden;text-overflow:ellipsis">${c.project||'—'}</td><td class="mono"><span class="tk-in">↓</span> ${fmt(c.input_tokens)}</td><td class="mono"><span class="tk-out">↑</span> ${fmt(c.output_tokens)}</td><td class="mono"><span class="tk-cr">⟲</span> ${fmt(c.cache_read)}</td><td class="mono"><span class="tk-cw">⟳</span> ${fmt(c.cache_create)}</td><td class="mono" style="color:var(--green)">${cost}</td></tr>`;
  }).join('');
  document.getElementById('lCalls').textContent = d.totals.calls;
  document.getElementById('lIn').textContent = fmt(d.totals.input);
  document.getElementById('lOut').textContent = fmt(d.totals.output);
  document.getElementById('lCR').textContent = fmt(d.totals.cache_read);
  document.getElementById('lCC').textContent = fmt(d.totals.cache_create);
  const lCost = document.getElementById('lCost'); if (lCost) lCost.textContent = '$' + (d.totals.cost || 0).toFixed(2);
  showActiveSessions(d.calls);
}

function showActiveSessions(calls) {
  const now = new Date();
  const cut = 5 * 60 * 1000;
  const rec = {};
  calls.forEach(c => {
    try {
      const dt = new Date(c.timestamp);
      if (now - dt < cut) {
        const k = c.project || '?';
        if (!rec[k]) rec[k] = { model:c.model, project:c.project, count:0, tokens:0, first:dt, last:dt };
        rec[k].count++;
        rec[k].tokens += c.input_tokens + c.output_tokens;
        if (dt < rec[k].first) rec[k].first = dt;
        if (dt > rec[k].last) rec[k].last = dt;
      }
    } catch {}
  });
  const items = Object.values(rec);
  const w = document.getElementById('activeSessionsWrap');
  if (!items.length) { w.style.display = 'none'; return; }
  w.style.display = '';
  document.getElementById('activeCount').textContent = items.length + (curLang==='zh' ? ' 个活跃' : ' active');
  document.getElementById('activeList').innerHTML = items.map(it => {
    const dur = Math.round((it.last - it.first) / 1000);
    const ds = dur > 60 ? Math.round(dur/60) + 'm' : dur + 's';
    return `<div class="active-item"><div class="active-item-model"><span class="mdot" style="background:${mC(it.model)}"></span>${mS(it.model)}</div><div class="active-item-detail">${it.project||'—'} · ${it.count} calls · ${fmt(it.tokens)} tok · ${ds}</div></div>`;
  }).join('');
}

/* ---- Logs ---- */
let logPage = 0, logLimit = 50, autoRefreshEnabled = true, autoRefreshTimer = null;

async function loadLogs() {
  const start = document.getElementById('filterStart').value;
  const end = document.getElementById('filterEnd').value;
  const model = document.getElementById('filterModel').value;
  const project = document.getElementById('filterProject').value;
  let url = `/api/logs?limit=${logLimit}&offset=${logPage*logLimit}`;
  if (start) url += `&start=${encodeURIComponent(new Date(start).toISOString())}`;
  if (end) url += `&end=${encodeURIComponent(new Date(end).toISOString())}`;
  if (model) url += `&model=${encodeURIComponent(model)}`;
  if (project) url += `&project=${encodeURIComponent(project)}`;
  const d = await api(url);
  const tp = Math.ceil(d.total / logLimit) || 1;
  document.getElementById('logTotal').textContent = d.total + (curLang==='zh' ? ' 条' : ' records');
  document.getElementById('tbLogs').innerHTML = d.logs.map(c => {
    const ts = relativeTime(c.timestamp);
    const sc = c.status === 200 ? 'badge-success' : 'badge-error';
    const ttft = c.ttft_ms != null ? (c.ttft_ms < 1000 ? c.ttft_ms+'ms' : (c.ttft_ms/1000).toFixed(1)+'s') : '—';
    const tc = c.ttft_ms != null ? (c.ttft_ms < 3000 ? 'ttft-green' : c.ttft_ms < 10000 ? 'ttft-yellow' : 'ttft-red') : '';
    const dur = c.duration_ms != null ? (c.duration_ms < 1000 ? c.duration_ms+'ms' : c.duration_ms < 60000 ? (c.duration_ms/1000).toFixed(1)+'s' : (c.duration_ms/60000).toFixed(1)+'m') : '—';
    let cb = '';
    if ((c.project||'').includes('(cloud)') || (c.project||'').includes('远程')) {
      const lbl = curLang==='zh' ? '云' : '☁';
      cb = `<span style="font:600 7px var(--font);padding:0 4px;border-radius:3px;background:var(--blue-bg);color:var(--blue);margin-left:3px">${lbl}</span>`;
    }
    const rowCost = c.cost_usd != null ? '$'+c.cost_usd.toFixed(4) : '—';
    return `<tr><td title="${c.timestamp}">${ts}</td><td style="max-width:110px;overflow:hidden;text-overflow:ellipsis">${c.project||'—'}${cb}</td><td><span class="mdot" style="background:${mC(c.model)}"></span>${mS(c.model)}</td><td class="mono"><span class="tk-in">↓</span> ${fmt(c.input_tokens)}</td><td class="mono"><span class="tk-out">↑</span> ${fmt(c.output_tokens)}</td><td class="mono"><span class="tk-cw">⟳</span> ${fmt(c.cache_create)}</td><td class="mono"><span class="tk-cr">⟲</span> ${fmt(c.cache_read)}</td><td class="mono" style="color:var(--green)">${rowCost}</td><td class="mono ${tc}">${ttft}</td><td class="mono">${dur}</td><td><span class="badge ${sc}">${c.status||200}</span></td></tr>`;
  }).join('');

  const info = document.getElementById('paginationInfo');
  const sr = logPage * logLimit + 1, er = Math.min((logPage+1)*logLimit, d.total);
  info.textContent = d.total > 0 ? `${sr}–${er} / ${d.total}` : '—';

  const btns = document.getElementById('paginationBtns');
  let h = '';
  h += `<button class="page-btn" onclick="logPageGo(0)" ${logPage===0?'disabled':''}>&laquo;</button>`;
  h += `<button class="page-btn" onclick="logPageGo(${logPage-1})" ${logPage===0?'disabled':''}>&lsaquo;</button>`;
  let ps = Math.max(0, logPage - 2);
  for (let i = ps; i < ps + Math.min(tp,5) && i < tp; i++)
    h += `<button class="page-btn ${i===logPage?'active':''}" onclick="logPageGo(${i})">${i+1}</button>`;
  h += `<button class="page-btn" onclick="logPageGo(${logPage+1})" ${logPage>=tp-1?'disabled':''}>&rsaquo;</button>`;
  h += `<button class="page-btn" onclick="logPageGo(${tp-1})" ${logPage>=tp-1?'disabled':''}>&raquo;</button>`;
  btns.innerHTML = h;
}

function logPageGo(p) { if (p < 0) p = 0; logPage = p; loadLogs(); }
function applyLogFilters() { logPage = 0; loadLogs(); }
function resetLogFilters() {
  document.getElementById('filterStart').value = '';
  document.getElementById('filterEnd').value = '';
  document.getElementById('filterModel').value = '';
  document.getElementById('filterProject').value = '';
  logPage = 0; loadLogs();
}
function toggleAutoRefresh() {
  autoRefreshEnabled = !autoRefreshEnabled;
  const b = document.getElementById('autoRefreshBtn');
  const t = document.getElementById('autoRefreshText');
  b.classList.toggle('active', autoRefreshEnabled);
  t.dataset.i = autoRefreshEnabled ? 'stopAutoRefresh' : 'startAutoRefresh';
  t.textContent = autoRefreshEnabled ? (curLang==='zh'?'停止刷新':'Stop Refresh') : (curLang==='zh'?'开始刷新':'Auto Refresh');
  if (autoRefreshEnabled) startAutoRefresh(); else stopAutoRefresh();
}
function startAutoRefresh() { if (autoRefreshTimer) clearInterval(autoRefreshTimer); autoRefreshTimer = setInterval(() => { loadLogs(); loadLive(); }, 15000); }
function stopAutoRefresh() { if (autoRefreshTimer) { clearInterval(autoRefreshTimer); autoRefreshTimer = null; } }

/* ===== Init ===== */
async function init() {
  try {
    // Load everything in parallel — don't block on slow remote calls
    await Promise.all([
      loadStatus(), loadOverview(), loadCharts(), loadModels(),
      loadProjects(), loadSess(), loadLive(), loadLogs()
    ]);
    notyf.success(curLang==='zh' ? 'Dashboard 加载完成' : 'Dashboard loaded');
  } catch(e) {
    console.error(e);
    notyf.error(curLang==='zh' ? '连接失败' : 'Connection failed');
  }
  const ov = document.getElementById('ldOv');
  ov.style.opacity = '0';
  setTimeout(() => ov.remove(), 600);
  document.getElementById('lastUp').textContent = (curLang==='zh' ? '更新于 ' : 'Updated ') + new Date().toLocaleTimeString(curLang==='zh'?'zh-CN':'en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  setInterval(loadStatus, 30000);
  startAutoRefresh();
  applyI18n();
  const savedPage = localStorage.getItem('ccdash_page') || 'overview';
  switchPage(savedPage);
}

async function refreshAll() {
  document.getElementById('lastUp').textContent = curLang==='zh' ? '刷新中...' : 'Refreshing...';
  try {
    await api('/api/overview?refresh=1');
    await Promise.all([loadStatus(), loadOverview(), loadCharts(), loadModels(), loadProjects(), loadSess(), loadLive(), loadLogs()]);
    notyf.success(curLang==='zh' ? '已更新' : 'Updated');
  } catch { notyf.error(curLang==='zh' ? '刷新失败' : 'Refresh failed'); }
  document.getElementById('lastUp').textContent = (curLang==='zh' ? '更新于 ' : 'Updated ') + new Date().toLocaleTimeString(curLang==='zh'?'zh-CN':'en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

document.addEventListener('DOMContentLoaded', () => { init(); });

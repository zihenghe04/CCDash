/* ==========================================================================
   CLAUDE CORE CONSOLE — Application Logic
   Zinc-gray SaaS aesthetic. All features merged.
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
    navOverview:'概览', navAnalytics:'分析', navLive:'实时', navLogs:'日志',
    toolUsage:'工具分布', toolUsageDesc:'所有会话中最常使用的工具',
    codingRhythm:'编码节奏', codingRhythmDesc:'按时间段的活跃分布', workMode:'工作模式', workModeDesc:'探索 vs 构建 vs 执行', modelDNA:'模型 DNA', modelDNADesc:'按模型家族的 Token 分布', projection:'预估',
    burnRate:'消耗速率', exportCSV:'导出CSV', exportJSON:'导出JSON',
    monthly:'月度', projectCost:'项目成本',
    weekCompare:'周环比', dayCompare:'日环比', thisWeek:'本周', lastWeek:'上周', today:'今日', yesterday:'昨日',
    ctxUsage:'上下文%', tokens:'Token',
    sessionDetail:'会话详情', duration:'耗时', cost:'成本', tools:'工具',
    filesAccessed:'访问文件', noEvents:'无事件记录',
    sessUser:'用户', sessAssistant:'助手',
    navSettings:'设置', apiConfig:'API 配置', apiConfigDesc:'Claude.ai Session Key 用于额度追踪',
    modelPricing:'模型定价', modelPricingDesc:'自定义非 Anthropic 模型的定价（每百万 Token）',
    addModel:'添加模型', savePricing:'保存定价', save:'保存',
    detectedModels:'检测到的模型', detectedModelsDesc:'在使用数据中发现的模型',
    dataSources:'数据源', dataSourcesDesc:'已检测到的 CLI 工具数据',
    claudeCode:'Claude Code', codexCli:'Codex CLI',
    sourceCodex:'Codex', sourceClaude:'Claude',
    webConversations:'Web & 客户端', webConversationsDesc:'来自网页版、桌面客户端和 SDK 的会话',
    todayBreakdown:'今日模型消耗', todayBreakdownDesc:'按模型统计今日调用次数、Token 和成本',
    mcpServers:'MCP 服务器', mcpServersDesc:'按服务器统计 MCP 工具使用', mcpTrend:'MCP 趋势', mcpTrendDesc:'内置工具 vs MCP 工具每日使用趋势',
    ratePredict:'限速预测', riskLevel:'风险等级', timeToThrottle:'预计限速', currentRpm:'当前 RPM (30m)', currentTpm:'当前 TPM (30m)', safeRpm:'安全 RPM',
    efficiency:'Prompt 效率', efficiencyDesc:'输出比率、缓存评级与交互模式分类', effTrend:'效率趋势', effTrendDesc:'每日输出比率与缓存命中率',
    outputRatio:'输出比率', cacheGrade:'缓存评级', sessionsAnalyzed:'分析会话数', interactionModes:'交互模式',
    modeExploration:'探索', modeBuilding:'构建', modeDebugging:'调试', modeReview:'审查',
    builtinTools:'内置工具', mcpTools:'MCP 工具',
    insights:'优化建议', noInsights:'暂无建议',
    budget:'预算', budgetConfig:'预算配置', budgetConfigDesc:'设定每日/每周/每月成本上限',
    dailyBudget:'每日 ($)', weeklyBudget:'每周 ($)', monthlyBudget:'每月 ($)',
    budgetDaily:'每日', budgetWeekly:'每周', budgetMonthly:'每月',
    spent:'已花费', remaining:'剩余', overBudget:'超出预算',
    compReport:'对比报告', compReportDesc:'本期与上期对比',
    weeklyReport:'周报', monthlyReport:'月报',
    current:'本期', previous:'上期', change:'变化',
    highlights:'亮点', avgDailyCost:'日均成本', topModel:'最活跃模型', mostActiveDay:'最活跃日',
    savingPotential:'节省潜力'
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
    navOverview:'Overview', navAnalytics:'Analytics', navLive:'Live Stream', navLogs:'System Logs',
    toolUsage:'Tool Distribution', toolUsageDesc:'Most used tools across all sessions',
    codingRhythm:'Coding Rhythm', codingRhythmDesc:'Activity distribution by time of day', workMode:'Work Mode', workModeDesc:'Exploration vs Building vs Execution', modelDNA:'Model DNA', modelDNADesc:'Token distribution by model family', projection:'Projection',
    burnRate:'Burn Rate', exportCSV:'Export CSV', exportJSON:'Export JSON',
    monthly:'Monthly', projectCost:'Project Cost',
    weekCompare:'Week over Week', dayCompare:'Day over Day', thisWeek:'This Week', lastWeek:'Last Week', today:'Today', yesterday:'Yesterday',
    ctxUsage:'Ctx%', tokens:'Tokens',
    sessionDetail:'Session Detail', duration:'Duration', cost:'Cost', tools:'Tools',
    filesAccessed:'Files Accessed', noEvents:'No events found',
    sessUser:'User', sessAssistant:'Assistant',
    navSettings:'Settings', apiConfig:'API Configuration', apiConfigDesc:'Claude.ai session key for quota tracking',
    modelPricing:'Model Pricing', modelPricingDesc:'Custom pricing for non-Anthropic models (per million tokens)',
    addModel:'Add Model', savePricing:'Save Pricing', save:'Save',
    detectedModels:'Detected Models', detectedModelsDesc:'Models found in your usage data',
    dataSources:'Data Sources', dataSourcesDesc:'Detected CLI tool data',
    claudeCode:'Claude Code', codexCli:'Codex CLI',
    sourceCodex:'Codex', sourceClaude:'Claude',
    webConversations:'Web & Desktop', webConversationsDesc:'Conversations from web, desktop app & SDK',
    todayBreakdown:"Today's Cost by Model", todayBreakdownDesc:'Per-model calls, tokens and cost for today',
    mcpServers:'MCP Servers', mcpServersDesc:'MCP tool usage by server', mcpTrend:'MCP Trend', mcpTrendDesc:'Built-in vs MCP tool usage over time',
    ratePredict:'Rate Limit Prediction', riskLevel:'Risk Level', timeToThrottle:'Time to Throttle', currentRpm:'Current RPM (30m)', currentTpm:'Current TPM (30m)', safeRpm:'Safe RPM',
    efficiency:'Prompt Efficiency', efficiencyDesc:'Output ratio, cache grade & interaction modes', effTrend:'Efficiency Trend', effTrendDesc:'Daily output ratio & cache rate',
    outputRatio:'Output Ratio', cacheGrade:'Cache Grade', sessionsAnalyzed:'Sessions Analyzed', interactionModes:'Interaction Modes',
    modeExploration:'Exploration', modeBuilding:'Building', modeDebugging:'Debugging', modeReview:'Review',
    builtinTools:'Built-in Tools', mcpTools:'MCP Tools',
    insights:'Optimization Insights', noInsights:'No suggestions',
    budget:'Budget', budgetConfig:'Budget Configuration', budgetConfigDesc:'Set daily/weekly/monthly cost limits',
    dailyBudget:'Daily ($)', weeklyBudget:'Weekly ($)', monthlyBudget:'Monthly ($)',
    budgetDaily:'Daily', budgetWeekly:'Weekly', budgetMonthly:'Monthly',
    spent:'Spent', remaining:'Remaining', overBudget:'Over budget',
    compReport:'Comparison Report', compReportDesc:'This period vs last period',
    weeklyReport:'Weekly', monthlyReport:'Monthly',
    current:'Current', previous:'Previous', change:'Change',
    highlights:'Highlights', avgDailyCost:'Avg Daily Cost', topModel:'Top Model', mostActiveDay:'Most Active Day',
    savingPotential:'Saving potential'
  }
};
let curLang = localStorage.getItem('claude_dash_lang') || 'zh';

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
  const titleMap = { overview:'navOverview', analytics:'navAnalytics', live:'navLive', logs:'navLogs', settings:'navSettings' };
  const curPage = localStorage.getItem('claude_dash_page') || 'overview';
  const pt = document.getElementById('pageTitle');
  if (pt && titleMap[curPage]) pt.textContent = t[titleMap[curPage]] || curPage;
}

function toggleLang() {
  curLang = curLang === 'zh' ? 'en' : 'zh';
  localStorage.setItem('claude_dash_lang', curLang);
  applyI18n();
  renderCharts();
  loadLive();
  loadLogs();
}

/* ---- Theme ---- */
function initTheme() {
  const s = localStorage.getItem('claude_dash_theme') || 'dark';
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
  localStorage.setItem('claude_dash_theme', n);
  updateThemeIcon(n);
  renderCharts();
  if (window._ringData) drawRing(...window._ringData);
}
initTheme();

/* ---- Privacy Mode ---- */
let privacyMode = localStorage.getItem('claude_dash_privacy') === 'true';
/* ---- Data Source Switching ---- */
let activeSource = 'all';
/* ---- Data Source Switching (pure frontend, zero API calls) ---- */
window._allData = {};

function switchSource(src) {
  activeSource = src;
  document.querySelectorAll('.source-tabs .pill').forEach(el => el.classList.toggle('on', el.dataset.source === src));

  // Gauge visibility
  const gaugeCard = document.getElementById('gaugeCard');
  const overviewTop = document.getElementById('overviewTop');
  if (gaugeCard && overviewTop) {
    gaugeCard.style.display = src === 'codex' ? 'none' : '';
    overviewTop.style.gridTemplateColumns = src === 'codex' ? '1fr' : '';
  }

  // Reload all data from backend with source filter (backend skips remote for non-all)
  const main = document.querySelector('.page.active');
  if (main) {
    main.style.transition = 'opacity .12s ease-out, transform .12s ease-out';
    main.style.opacity = '0';
    main.style.transform = 'scale(0.98)';
  }
  Promise.all([
    loadOverview(), loadCharts(), loadModels(), loadProjects(),
    loadLive(), loadLogs(), loadSess(), loadTools(), loadRhythm(),
    loadTodayBreakdown(), loadRatePrediction(), loadMcpStats(),
    loadMcpTrend(), loadEfficiency(), loadInsights(), loadBudget(),
    loadReport('weekly')
  ]).then(() => {
    if (main) {
      main.style.transition = 'opacity .2s ease-in, transform .2s ease-in';
      main.style.opacity = '1';
      main.style.transform = 'scale(1)';
    }
    notyf.success(curLang==='zh' ? `数据源: ${src==='all'?'全部':src}` : `Source: ${src==='all'?'All':src}`);
  });
}

function applySourceFilter() {
  // Use CSS data-source attribute to show/hide rows — instant, no re-render needed
  const src = activeSource;
  // Tables: hide rows that don't match source
  document.querySelectorAll('[data-row-source]').forEach(el => {
    if (src === 'all') { el.style.display = ''; return; }
    el.style.display = (el.dataset.rowSource === src) ? '' : 'none';
  });

  const _match = (model, source) => {
    if (src === 'all') return true;
    if (source) return source === src;
    const isCodex = /^gpt|codex/i.test(model||'');
    return src === 'codex' ? isCodex : !isCodex;
  };

  // Recalculate overview stats from cached models data
  if (window._allData.models) {
    const models = window._allData.models.models || {};
    let totalTokens = 0, totalInput = 0, totalOutput = 0, totalCR = 0, totalCC = 0, totalCalls = 0;
    for (const [m, v] of Object.entries(models)) {
      if (!_match(m, v.source)) continue;
      totalInput += v.input || 0; totalOutput += v.output || 0;
      totalCR += v.cache_read || 0; totalCC += v.cache_create || 0;
      totalCalls += v.calls || 0;
    }
    totalTokens = totalInput + totalOutput + totalCR + totalCC;
    document.getElementById('cTok').textContent = fmt(totalTokens);
    document.getElementById('cIn').textContent = fmt(totalInput);
    document.getElementById('cOut').textContent = fmt(totalOutput);
    document.getElementById('cCR').textContent = fmt(totalCR);
    document.getElementById('cCC').textContent = fmt(totalCC);
    const allInput = totalInput + totalCR + totalCC;
    const hitRate = allInput > 0 ? Math.round(totalCR / allInput * 100) : 0;
    document.getElementById('cRate').textContent = hitRate + '%';

    // Total messages from stat card
    document.getElementById('cMsg').textContent = fmt(totalCalls);
    // Model count
    const filteredModelCount = Object.keys(models).filter(m => _match(m, models[m].source)).length;
    document.getElementById('cModels').textContent = filteredModelCount;

    // Update cost badge from filtered models
    const totalCost = Object.entries(models).filter(([m, v]) => _match(m, v.source)).reduce((s,[,v]) => s + (v.cost_usd||0), 0);
    const costEl = document.getElementById('totalCost');
    if (costEl) costEl.textContent = '$' + (totalCost >= 1000 ? (totalCost/1000).toFixed(1)+'K' : totalCost.toFixed(2));
  }

  // Recalculate live totals from visible rows
  if (window._allData.live) {
    const calls = (window._allData.live.calls || []).filter(c => _match(c.model, c.source));
    const badge = document.getElementById('liveBadge');
    if (badge) badge.textContent = calls.length;
    document.getElementById('liveN').textContent = calls.length + (curLang==='zh' ? ' 条' : ' calls');
    const tot = { input:0, output:0, cache_read:0, cache_create:0, calls:calls.length, cost:0 };
    calls.forEach(c => { tot.input += c.input_tokens||0; tot.output += c.output_tokens||0; tot.cache_read += c.cache_read||0; tot.cache_create += c.cache_create||0; tot.cost += c.cost_usd||0; });
    document.getElementById('lCalls').textContent = tot.calls;
    document.getElementById('lIn').textContent = fmt(tot.input);
    document.getElementById('lOut').textContent = fmt(tot.output);
    document.getElementById('lCR').textContent = fmt(tot.cache_read);
    document.getElementById('lCC').textContent = fmt(tot.cache_create);
    const lCost = document.getElementById('lCost'); if (lCost) lCost.textContent = '$' + tot.cost.toFixed(2);
  }

  // Recalculate log count
  const visibleLogs = document.querySelectorAll('#tbLogs tr[data-row-source]');
  let logCount = 0;
  visibleLogs.forEach(el => { if (el.style.display !== 'none') logCount++; });
  const logTotal = document.getElementById('logTotal');
  if (logTotal) logTotal.textContent = logCount + (curLang==='zh' ? ' 条' : ' records');

  // Session count
  const visibleSess = document.querySelectorAll('#tbSess tr[data-row-source]');
  let sessCount = 0;
  visibleSess.forEach(el => { if (el.style.display !== 'none') sessCount++; });

  // Update today stats
  document.getElementById('tMsg').textContent = src === 'all' ? (window._allData._todayMsgs || 0) : '—';
  document.getElementById('tSes').textContent = src === 'all' ? (window._allData._todaySess || 0) : '—';
}

// sourceParam: pass source to backend for full data filtering (charts, analytics, etc.)
function sourceParam(prefix) {
  if (!activeSource || activeSource === 'all') return '';
  return (prefix || '&') + 'source=' + activeSource;
}

function togglePrivacy() {
  privacyMode = !privacyMode;
  localStorage.setItem('claude_dash_privacy', privacyMode);
  document.body.classList.toggle('privacy-mode', privacyMode);
  const btn = document.getElementById('privacyBtn');
  if (btn) btn.innerHTML = privacyMode ? '<i class="ph ph-eye-slash"></i>' : '<i class="ph ph-eye"></i>';
  notyf.success(privacyMode ? (curLang==='zh'?'隐私模式已开启':'Privacy mode on') : (curLang==='zh'?'隐私模式已关闭':'Privacy mode off'));
}
// Apply on load
if (privacyMode) {
  document.body.classList.add('privacy-mode');
  const btn = document.getElementById('privacyBtn');
  if (btn) btn.innerHTML = '<i class="ph ph-eye-slash"></i>';
}

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

/* ---- Model colors (max contrast between commonly used models) ---- */
const MC = {
  'claude-opus-4-6':'#f97316',       // orange — primary, stands out
  'claude-sonnet-4-6':'#3b82f6',     // blue — clearly different from orange
  'claude-opus-4-5-20251101':'#ef4444', // red
  'claude-sonnet-4-5':'#8b5cf6',     // violet
  'claude-sonnet-4-5-20250929':'#8b5cf6',
  'claude-haiku-4-5-20251001':'#22c55e', // green
  'gpt-5.3-codex':'#eab308',        // yellow
  'gpt-5.4':'#ec4899',              // pink
  'gpt-5.2-codex':'#14b8a6',        // teal
  'gpt-4o':'#f43f5e',               // rose
  'gpt-4o-mini':'#a3e635',          // lime
  'gpt-5-mini':'#e879f9',           // fuchsia
  'GLM-5':'#06b6d4',                // cyan
  'MiniMax-M2.5':'#a855f7',         // purple
  '<synthetic>':'#6b7280',          // gray
};
function mC(m) { return MC[m] || '#94a3b8'; }
function mS(m) { return m.replace('claude-','').replace(/-\d{8}$/,''); }

/* ---- Entrypoint Badge ---- */
function epBadge(ep) {
  if (!ep || ep === 'cli') return '';
  if (ep === 'claude-desktop') return '<span class="ep-badge ep-desktop">Desktop</span>';
  if (ep === 'sdk-ts' || ep === 'sdk-cli') return '<span class="ep-badge ep-sdk">SDK</span>';
  if (ep === 'local-agent') return '<span class="ep-badge ep-sdk">Agent</span>';
  return '<span class="ep-badge ep-sdk">' + ep + '</span>';
}

/* ---- API helper ---- */
async function api(p) { try { return await (await fetch(p)).json(); } catch(e) { console.warn('API error:', p, e); return null; } }

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
  // Slide the nav indicator pill
  moveNavSlider(navEl);
  localStorage.setItem('claude_dash_page', pageId);
  // Update page title
  const t = I18N[curLang] || I18N.zh;
  const titleMap = { overview:'navOverview', analytics:'navAnalytics', live:'navLive', logs:'navLogs', settings:'navSettings' };
  const pt = document.getElementById('pageTitle');
  if (pt && titleMap[pageId]) pt.textContent = t[titleMap[pageId]] || pageId;
  // Lazy load
  if (pageId === 'overview') { if (!chA) renderCharts(); loadTodayBreakdown(); loadRatePrediction(); loadInsights(); loadBudget(); }
  if (pageId === 'live') { loadLive(); }
  if (pageId === 'analytics') { loadModels(); loadProjects(); loadTools(); loadRhythm(); loadMcpStats(); loadMcpTrend(); loadEfficiency(); loadReport('weekly'); }
  if (pageId === 'logs') { loadLogs(); loadSess(); loadWebConversations(); }
  if (pageId === 'settings') { loadSettings(); }
}

function moveNavSlider(activeEl) {
  const slider = document.getElementById('navSlider');
  if (!slider || !activeEl) return;
  // Get all nav items and find index
  const items = Array.from(document.querySelectorAll('#sidebarNav .nav-item'));
  const idx = items.indexOf(activeEl);
  if (idx < 0) return;
  // Calculate offset: each item is ~42px (padding 10+10 + font ~20 + gap 2)
  // Use actual measurements
  const firstItem = items[0];
  if (!firstItem) return;
  const navPadding = 8; // var(--space-sm)
  const gap = 2;
  const itemH = firstItem.offsetHeight;
  const offset = navPadding + idx * (itemH + gap);
  slider.style.transform = `translateY(${offset}px)`;
  slider.style.height = itemH + 'px';
  slider.style.opacity = '1';
}

function initNavSlider() {
  const activeNav = document.querySelector('.nav-item.active');
  if (activeNav) moveNavSlider(activeNav);
}
setTimeout(initNavSlider, 300);
window.addEventListener('resize', initNavSlider);

/* ===== Data Loading ===== */
let _cdI, curRange = '7d';

/* -- Gauge update -- */
function updateGauge(pct) {
  const arcLen = 251.33; // half-circle arc length (PI * 80)
  const offset = arcLen - (pct / 100) * arcLen;
  const fill = document.getElementById('gaugeFill');
  if (fill) {
    fill.style.strokeDashoffset = offset;
    if (pct > 80) fill.style.stroke = 'var(--red)';
    else if (pct > 50) fill.style.stroke = 'var(--orange)';
    else fill.style.stroke = 'url(#g5h)';
  }
  const val = document.getElementById('gaugeVal');
  if (val) val.textContent = pct + '%';
}

async function loadStatus() {
  const d = await api('/api/status');
  if (!d) return;

  // Detect data sources and adjust UI
  const settings = await api('/api/settings');
  if (settings && settings.data_sources) {
    const ds = settings.data_sources;
    const hasClaude = ds.claude_code && ds.claude_code.detected;
    const hasCodex = ds.codex_cli && ds.codex_cli.detected;
    const gaugeCard = document.getElementById('gaugeCard');
    const sourceTabs = document.getElementById('sourceTabs');

    // Show source tabs only if multiple sources
    if (hasClaude && hasCodex && sourceTabs) {
      sourceTabs.style.display = 'flex';
    }

    // Hide gauge card only if Claude Code is not detected at all
    if (gaugeCard) {
      if (!hasClaude) {
        gaugeCard.style.display = 'none';
        const overviewTop = document.getElementById('overviewTop');
        if (overviewTop) overviewTop.style.gridTemplateColumns = '1fr';
      }
    }
  }

  document.getElementById('pName').textContent = d.profile_name || '—';
  updateGauge(d.utilization || 0);
  document.getElementById('tMsg').textContent = d.today_messages;
  document.getElementById('tSes').textContent = d.today_sessions;
  window._allData._todayMsgs = d.today_messages;
  window._allData._todaySess = d.today_sessions;
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
          const circ = 251.33; // half-circle arc
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

function renderOverviewData(d) {
  if (!d) return;
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
  // Burn rate with severity classification
  const brEl = document.getElementById('burnRate');
  const brBadge = document.getElementById('burnBadge');
  if (brEl) {
    const br = d.burn_rate_tokens_per_min || 0;
    brEl.textContent = br ? fmt(br) : '—';
    if (brBadge) {
      let sev, sevColor;
      if (br >= 2000000) { sev = curLang==='zh'?'极高':'Extreme'; sevColor = 'var(--red)'; }
      else if (br >= 500000) { sev = curLang==='zh'?'高':'High'; sevColor = 'var(--orange)'; }
      else if (br >= 100000) { sev = curLang==='zh'?'中':'Moderate'; sevColor = 'var(--blue)'; }
      else if (br >= 10000) { sev = curLang==='zh'?'低':'Low'; sevColor = 'var(--green)'; }
      else { sev = curLang==='zh'?'空闲':'Idle'; sevColor = 'var(--text-2)'; }
      brBadge.textContent = sev;
      brBadge.style.color = sevColor;
    }
  }
  // Cache efficiency grade
  const cacheGrade = document.getElementById('cacheGrade');
  if (cacheGrade) {
    const hr = d.cache_hit_rate || 0;
    let grade, gc;
    if (hr >= 85) { grade = curLang==='zh'?'优秀':'Excellent'; gc = 'var(--green)'; }
    else if (hr >= 60) { grade = curLang==='zh'?'良好':'Good'; gc = 'var(--blue)'; }
    else if (hr >= 30) { grade = curLang==='zh'?'一般':'Fair'; gc = 'var(--orange)'; }
    else { grade = curLang==='zh'?'较低':'Poor'; gc = 'var(--red)'; }
    cacheGrade.textContent = grade;
    cacheGrade.style.color = gc;
  }
  // Usage projection (estimated daily cost at current rate)
  const projEl = document.getElementById('projCost');
  if (projEl && d.burn_rate_cost_per_hour) {
    projEl.textContent = '$' + (d.burn_rate_cost_per_hour * 24).toFixed(0) + '/day';
  }
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

/* ---- loadOverview: fetch, cache, render ---- */
async function loadOverview() {
  const d = await api('/api/overview' + sourceParam('?'));
  if (!d) return;
  // Cache models breakdown for client-side source filtering
  window._allData.overview = d;
  renderOverviewData(d);
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
  'gpt-5.3-codex':{input:1.75,output:14,cache_read:0.175,cache_create:0},
  'gpt-5.4':{input:2.5,output:15,cache_read:0.25,cache_create:0},
  'gpt-5.4-mini':{input:0.75,output:4.5,cache_read:0.075,cache_create:0},
  'gpt-5.2-codex':{input:1.75,output:14,cache_read:0.175,cache_create:0},
  'gpt-4o':{input:2.5,output:10,cache_read:1.25,cache_create:0},
  'gpt-4o-mini':{input:0.15,output:0.6,cache_read:0.075,cache_create:0},
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

function aggregateMonthly(activity, tokens) {
  const actMap = {}, tokMap = {};
  activity.forEach(a => {
    const m = a.date.slice(0,7); // YYYY-MM
    if (!actMap[m]) actMap[m] = {date:m,messages:0,sessions:0,tools:0};
    actMap[m].messages += a.messages; actMap[m].sessions += a.sessions; actMap[m].tools += (a.tools||0);
  });
  tokens.forEach(t => {
    const m = t.date.slice(0,7);
    if (!tokMap[m]) tokMap[m] = {date:m,byModel:{}};
    for (const [model,v] of Object.entries(t.byModel||{})) {
      if (!tokMap[m].byModel[model]) tokMap[m].byModel[model] = {input:0,output:0,cache_read:0,cache_create:0};
      for (const k of ['input','output','cache_read','cache_create']) tokMap[m].byModel[model][k] += (v[k]||0);
    }
  });
  const months = [...new Set([...Object.keys(actMap),...Object.keys(tokMap)])].sort();
  return {
    activity: months.map(m => actMap[m] || {date:m,messages:0,sessions:0,tools:0}),
    tokens: months.map(m => tokMap[m] || {date:m,byModel:{}})
  };
}

async function loadCharts() {
  const is24h = curRange === '24h';
  const isMonthly = curRange === 'monthly';

  // 24H mode: use hourly-trend API
  if (is24h) {
    const h = await api('/api/hourly-trend' + sourceParam('?'));
    if (!h) return;
    const dates = h.hours.map(x => x.hour);
    const msgs = h.hours.map(x => x.messages);
    const toks = h.hours.map(x => x.tokens);
    const costs = h.hours.map(x => x.cost);
    const dk = document.body.dataset.theme === 'dark';
    const fg = dk ? '#71717a' : '#a1a1aa';

    if (chA) chA.destroy();
    chA = new ApexCharts(document.getElementById('chartAct'), {
      chart:{type:'bar',height:290,background:'transparent',foreColor:fg,toolbar:{show:false},fontFamily:'Inter'},
      series:[
        {name:curLang==='zh'?'消息':'Messages',data:msgs},
        {name:curLang==='zh'?'Token':'Tokens',data:toks,type:'line'},
        {name:curLang==='zh'?'成本($)':'Cost($)',data:costs,type:'line'}
      ],
      colors:['#4ade80','#22d3ee','#fbbf24'],
      xaxis:{categories:dates,axisBorder:{show:false},axisTicks:{show:false},labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono'}}},
      yaxis:[
        {labels:{formatter:v=>fmt(v),style:{fontSize:'9px'}}},
        {opposite:true,labels:{formatter:v=>fmt(v),style:{fontSize:'9px'}},show:false},
        {opposite:true,labels:{formatter:v=>'$'+v.toFixed(1),style:{fontSize:'9px'}},show:false}
      ],
      plotOptions:{bar:{borderRadius:4,columnWidth:'60%'}},
      grid:{show:false},dataLabels:{enabled:false},stroke:{width:[0,2.5,2.5],curve:'smooth'},
      legend:{position:'top',horizontalAlign:'left',fontSize:'10px',fontFamily:'Inter',labels:{colors:fg}},
      tooltip:{theme:dk?'dark':'light'},theme:{mode:dk?'dark':'light'}
    });
    chA.render();
    // Also render weekly comparison if available
    if (typeof renderWeeklyComparison === 'function') {
      const wc = document.getElementById('weeklyCompare');
      if (wc) wc.style.display = 'none';
    }
    return;
  }

  const days = isMonthly ? 365 : (parseInt(curRange) || 30);
  const d = await api('/api/daily?days=' + days + sourceParam());
  if (!d) return;
  let activity = d.activity, tokens = d.tokens;
  if (isMonthly) {
    const agg = aggregateMonthly(activity, tokens);
    activity = agg.activity; tokens = agg.tokens;
  }
  const dates = activity.map(a => isMonthly ? a.date : a.date.slice(5));
  const dk = document.body.dataset.theme === 'dark';
  const fg = dk ? '#71717a' : '#a1a1aa';

  /* --- Cost data from token byModel --- */
  const costData = tokens.map(t => calcDayCost(t.byModel));

  /* --- Daily total tokens --- */
  const dailyTokens = tokens.map(t => {
    let total = 0;
    for (const v of Object.values(t.byModel || {})) {
      total += (v.input||0) + (v.output||0) + (v.cache_read||0) + (v.cache_create||0);
    }
    return total;
  });

  if (chA) chA.destroy();
  const tokLabel = curLang==='zh'?'Token':'Tokens';
  chA = new ApexCharts(document.getElementById('chartAct'), {
    chart: { type:'line', height:290, background:'transparent', foreColor:fg, toolbar:{show:false}, animations:{enabled:true,easing:'easeinout',speed:900} },
    series: [
      { name:curLang==='zh'?'消息':'Messages', type:'area', data:activity.map(a=>a.messages) },
      { name:curLang==='zh'?'会话':'Sessions', type:'area', data:activity.map(a=>a.sessions) },
      { name:curLang==='zh'?'工具':'Tools', type:'area', data:activity.map(a=>a.tools) },
      { name:curLang==='zh'?'成本($)':'Cost($)', type:'area', data:costData },
      { name:tokLabel, type:'column', data:dailyTokens }
    ],
    colors: ['#4ade80','#60a5fa','#c084fc','#fbbf24','#22d3ee'],
    xaxis: { categories:dates, labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono',colors:fg}}, axisBorder:{show:false}, axisTicks:{show:false} },
    yaxis: [
      { seriesName:curLang==='zh'?'消息':'Messages', labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono'}, formatter:v=>fmt(v)}, axisBorder:{show:false} },
      { seriesName:curLang==='zh'?'会话':'Sessions', show:false },
      { seriesName:curLang==='zh'?'工具':'Tools', show:false },
      { seriesName:curLang==='zh'?'成本($)':'Cost($)', opposite:true, labels:{style:{fontSize:'9px',fontFamily:'JetBrains Mono',color:'#fbbf24'}, formatter:v=>'$'+v.toFixed(1)}, axisBorder:{show:false} },
      { seriesName:tokLabel, opposite:true, show:false }
    ],
    grid: { show:false },
    stroke: { curve:'smooth', width:[2.5,2.5,2.5,2.5,0] },
    fill: { type:['gradient','gradient','gradient','gradient','solid'], gradient:{shadeIntensity:1,opacityFrom:0.25,opacityTo:0.02,stops:[0,90,100]}, opacity:[1,1,1,1,0.25] },
    plotOptions: { bar:{ borderRadius:2, columnWidth:'40%' } },
    dataLabels: { enabled:false },
    legend: { position:'top', horizontalAlign:'left', fontSize:'10px', fontFamily:'Inter', labels:{colors:fg}, markers:{shape:'circle',size:4} },
    tooltip: { theme:dk?'dark':'light', style:{fontFamily:'JetBrains Mono',fontSize:'11px'}, y:{formatter:(v,{seriesIndex})=>seriesIndex===3?'$'+v.toFixed(2):fmt(v)} },
    theme: apexTheme()
  });
  chA.render();

  // Weekly comparison
  // Store both comparisons for toggle
  window._compareData = { weekly: d.weekly_comparison, daily: d.daily_comparison };
  renderComparison();

  const am = new Set();
  tokens.forEach(t => Object.keys(t.byModel || {}).forEach(m => am.add(m)));

  if (chT) chT.destroy();
  chT = new ApexCharts(document.getElementById('chartTok'), {
    chart: { type:'bar', height:290, stacked:true, background:'transparent', foreColor:fg, toolbar:{show:false}, animations:{enabled:true,speed:800} },
    series: [...am].map(m => ({ name:mS(m), data:tokens.map(t => { const v=(t.byModel||{})[m]; return v ? v.input+v.output+v.cache_read+v.cache_create : 0; }) })),
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
  const d = await api('/api/hourly?days=' + days + sourceParam());
  if (!d) return;
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
  const panels = { act:'pAct', tok:'pTok', hm:'pHm' };
  Object.entries(panels).forEach(([k,id]) => {
    const el = document.getElementById(id);
    if (k === t) { el.style.display = ''; el.style.animation = 'none'; el.offsetHeight; el.style.animation = 'chartIn .4s ease'; }
    else { el.style.display = 'none'; }
  });
  if (t === 'hm') loadHeatmap();
}

function setRange(r) {
  curRange = r;
  document.querySelectorAll('.pill').forEach(el => {
    const txt = el.textContent.trim();
    if (r === 'monthly') el.classList.toggle('on', el.hasAttribute('data-i') && el.dataset.i === 'monthly');
    else el.classList.toggle('on', txt === r.toUpperCase());
  });
  loadCharts();
  if (document.getElementById('pHm').style.display !== 'none') loadHeatmap();
}

function renderModelsData(d) {
  if (!d) return;
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
    const ctxPct = v.avg_context_usage_pct || 0;
    const ctxColor = ctxPct > 80 ? 'var(--red)' : ctxPct > 50 ? 'var(--orange)' : 'var(--green)';
    const provider = v.provider || classifyProvider(m);
    const provColors = {Anthropic:'var(--accent)',OpenAI:'var(--green)',ZhipuAI:'var(--blue)',MiniMax:'var(--purple)',Google:'var(--orange)',DeepSeek:'var(--cyan,var(--blue))',Mistral:'var(--orange)',Meta:'var(--blue)',Alibaba:'var(--orange)',Other:'var(--text-2)'};
    const provColor = provColors[provider] || 'var(--text-2)';
    const modSrc = v.source || 'claude';
    return `<tr data-row-source="${modSrc}"><td><span class="mdot" style="background:${mC(m)}"></span>${mS(m)}</td><td><span style="display:inline-flex;align-items:center;gap:4px;font-size:11px"><span style="width:6px;height:6px;border-radius:50%;background:${provColor}"></span>${provider}</span></td><td class="mono"><span class="tk-in">↓</span>${fmt(v.input)}</td><td class="mono"><span class="tk-out">↑</span>${fmt(v.output)}</td><td class="mono"><span class="tk-cr">⟲</span>${fmt(v.cache_read)}</td><td class="mono"><span class="tk-cw">⟳</span>${fmt(v.cache_create)}</td><td>${v.calls}</td><td>${hr}%</td><td><span class="ctx-bar-wrap"><span class="ctx-bar-fill" style="width:${Math.min(ctxPct,100)}%;background:${ctxColor}"></span></span><span class="ctx-pct" style="color:${ctxColor}">${ctxPct}%</span></td><td style="color:var(--green);font-weight:600">${cost}</td></tr>`;
  }).join('');
  // Update overview cost badge from models total (single source of truth)
  const totalModelCost = ms.reduce((s,[,v]) => s + (v.cost_usd||0), 0);
  const costEl = document.getElementById('totalCost');
  if (costEl) costEl.textContent = '$' + (totalModelCost >= 1000 ? (totalModelCost/1000).toFixed(1)+'K' : totalModelCost.toFixed(2));
  const sel = document.getElementById('filterModel');
  if (sel.options.length <= 1) ms.forEach(([m]) => { const o = document.createElement('option'); o.value = m; o.textContent = mS(m); sel.appendChild(o); });
}
async function loadModels() { const d = await api('/api/models' + sourceParam('?')); if(!d) return; window._allData.models = d; renderModelsData(d); }

/* ---- Today's Model Breakdown ---- */
async function loadTodayBreakdown() {
  const d = await api('/api/today-breakdown' + sourceParam('?'));
  if (!d) return;
  const dateEl = document.getElementById('todayDate');
  if (dateEl) dateEl.textContent = d.date || '';
  const container = document.getElementById('todayBreakdownContent');
  if (!container) return;

  if (!d.models || d.models.length === 0) {
    container.innerHTML = '<div class="tbd-empty">' + (curLang==='zh' ? '今日暂无数据' : 'No data for today') + '</div>';
    return;
  }

  const totalCost = d.total_cost || 0;
  const t = I18N[curLang] || I18N.zh;

  // Build table (left) + donut chart (right)
  let tableHtml = '<table class="tbd-table"><thead><tr>';
  tableHtml += '<th>' + (t.model || 'Model') + '</th>';
  tableHtml += '<th>' + (t.calls || 'Calls') + '</th>';
  tableHtml += '<th><span class="tk-in">\u2193</span> In</th>';
  tableHtml += '<th><span class="tk-out">\u2191</span> Out</th>';
  tableHtml += '<th><span class="tk-cr">\u27F2</span> Cache</th>';
  tableHtml += '<th style="color:var(--green)">Cost</th>';
  tableHtml += '</tr></thead><tbody>';

  d.models.forEach(m => {
    const color = mC(m.model);
    const costStr = m.cost_usd >= 1000 ? '$' + (m.cost_usd/1000).toFixed(1) + 'K' : '$' + m.cost_usd.toFixed(2);
    const cache = fmt(m.cache_read + m.cache_create);
    tableHtml += '<tr data-row-source="' + (m.source || 'claude') + '">';
    tableHtml += '<td><span class="mdot" style="background:' + color + '"></span>' + mS(m.model) + '</td>';
    tableHtml += '<td class="mono">' + m.calls + '</td>';
    tableHtml += '<td class="mono">' + fmt(m.input_tokens) + '</td>';
    tableHtml += '<td class="mono">' + fmt(m.output_tokens) + '</td>';
    tableHtml += '<td class="mono">' + cache + '</td>';
    tableHtml += '<td style="color:var(--green);font-weight:600">' + costStr + '</td>';
    tableHtml += '</tr>';
  });

  const totalCostStr = totalCost >= 1000 ? '$' + (totalCost/1000).toFixed(1) + 'K' : '$' + totalCost.toFixed(2);
  tableHtml += '<tr class="tbd-total"><td>' + (curLang==='zh' ? '\u5408\u8BA1' : 'Total') + '</td>';
  tableHtml += '<td class="mono">' + d.total_calls + '</td>';
  tableHtml += '<td class="mono" colspan="3">' + fmt(d.total_tokens) + ' tok</td>';
  tableHtml += '<td style="color:var(--green)">' + totalCostStr + '</td></tr>';
  tableHtml += '</tbody></table>';

  // Donut chart + legend list (same style as Tool Distribution)
  let legendHtml = d.models.map(m => {
    const c = mC(m.model);
    const pct = totalCost > 0 ? (m.cost_usd / totalCost * 100).toFixed(0) : 0;
    const costStr = m.cost_usd >= 1 ? '$'+m.cost_usd.toFixed(2) : '$'+m.cost_usd.toFixed(4);
    return `<div style="display:flex;align-items:center;gap:6px;margin:4px 0">
      <span style="width:8px;height:8px;border-radius:50%;background:${c};flex-shrink:0;box-shadow:0 0 6px ${c}"></span>
      <span style="font-size:12px;flex:1">${mS(m.model)}</span>
      <span class="mono" style="font-size:11px;color:var(--green)">${costStr}</span>
      <span style="font-size:10px;color:var(--text-2)">${pct}%</span>
    </div>`;
  }).join('');

  container.innerHTML = '<div class="tbd-split"><div class="tbd-table-wrap">' + tableHtml + '</div><div class="tbd-chart-wrap"><div class="ring-c"><div class="ring-ch" id="todayDonut"></div><div class="ring-info">' + legendHtml + '</div></div></div></div>';

  // Render donut chart (same config as Tool Distribution)
  const dk = document.body.dataset.theme === 'dark';
  if (window._todayDonut) window._todayDonut.destroy();
  window._todayDonut = new ApexCharts(document.getElementById('todayDonut'), {
    chart:{type:'donut',height:190,background:'transparent',foreColor:dk?'#9ca3b0':'#4b5563'},
    series: d.models.map(m => m.cost_usd),
    labels: d.models.map(m => mS(m.model)),
    colors: d.models.map(m => mC(m.model)),
    plotOptions:{pie:{donut:{size:'60%',labels:{show:true,name:{show:false},value:{show:true,fontSize:'15px',fontWeight:700,fontFamily:'JetBrains Mono',color:dk?'#e8ecf1':'#111827',formatter:()=>totalCostStr},total:{show:true,label:'Total',formatter:()=>totalCostStr}}}}},
    dataLabels:{enabled:false},legend:{show:false},stroke:{width:0},
    theme:apexTheme(),
    tooltip:{style:{fontFamily:'JetBrains Mono',fontSize:'11px'},y:{formatter:v=>'$'+v.toFixed(2)}}
  });
  window._todayDonut.render();
}

function renderProjectsData(d) {
  if (!d) return;
  const tot = d.projects.reduce((s,p) => s+p.tokens_total, 0);
  document.getElementById('tbProj').innerHTML = d.projects.map(p => {
    const pc = tot > 0 ? (p.tokens_total/tot*100).toFixed(1) : 0;
    let sb = '', dn = p.name || '';
    if (p.source === 'codex') {
      const lbl = curLang==='zh' ? 'Codex' : 'CODEX';
      sb = `<span style="font:600 8px var(--font);padding:1px 6px;border-radius:4px;background:var(--green-bg,rgba(74,222,128,0.1));color:var(--green);margin-left:4px">${lbl}</span>`;
    } else if (dn.includes('(local)')) {
      const lbl = curLang==='zh' ? '本地' : 'LOCAL';
      sb = `<span style="font:600 8px var(--font);padding:1px 6px;border-radius:4px;background:var(--accent-bg);color:var(--accent);margin-left:4px">${lbl}</span>`;
      dn = dn.replace(/\s*\(local\)/, '');
    } else if (dn.includes('(cloud)')) {
      const lbl = curLang==='zh' ? '云端' : 'CLOUD';
      sb = `<span style="font:600 8px var(--font);padding:1px 6px;border-radius:4px;background:var(--blue-bg);color:var(--blue);margin-left:4px">${lbl}</span>`;
      dn = dn.replace(/\s*\(cloud\)/, '');
    }
    const pcost = p.cost_usd != null ? '$'+p.cost_usd.toFixed(2) : '—';
    const projSrc = p.source === 'codex' ? 'codex' : 'claude';
    return `<tr data-row-source="${projSrc}"><td title="${p.dir_name||''}">${dn}${sb}</td><td>${fmt(p.messages)}</td><td>${p.sessions}</td><td class="mono">${fmt(p.tokens_total)}</td><td>${pc}%</td><td class="mono" style="color:var(--green)">${pcost}</td></tr>`;
  }).join('');
  const sel = document.getElementById('filterProject');
  if (sel.options.length <= 1) d.projects.forEach(p => { const o = document.createElement('option'); o.value = p.name; o.textContent = p.name; sel.appendChild(o); });
}

async function loadProjects() { const d = await api('/api/projects' + sourceParam('?')); if(!d) return; window._allData.projects = d; renderProjectsData(d); }

function renderSessionsData(d) {
  if (!d) return;
  const sel = document.getElementById('sFilt');
  if (sel && sel.options.length <= 1 && d.projects) d.projects.forEach(p => { const o = document.createElement('option'); o.value = p; o.textContent = p.split('/').pop() || '~'; sel.appendChild(o); });
  // Desktop/SDK entrypoints that should go to Web & Desktop section
  const _desktopEntrypoints = ['claude-desktop', 'sdk-ts', 'sdk-cli', 'local-agent'];
  const _isDesktopSession = s => _desktopEntrypoints.includes(s.entrypoint);

  // CLI + Codex + remote (no entrypoint) sessions stay in main list
  const cliSessions = d.sessions.filter(s => !_isDesktopSession(s));
  document.getElementById('tbSess').innerHTML = cliSessions.map(s =>
    `<tr data-row-source="${s.source||'claude'}" onclick="showSessionDetail('${s.sessionId}')" title="${curLang==='zh'?'点击查看详情':'Click for details'}"><td>${fmtT(s.timestamp)}</td><td title="${s.project}">${s.projectShort}${epBadge(s.entrypoint)}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${s.firstPrompt||'—'}</td></tr>`
  ).join('');

  // Desktop/SDK sessions → render in Web & Desktop section
  const nonCliSessions = d.sessions.filter(s => _isDesktopSession(s));
  window._allData._desktopSessions = nonCliSessions;
  renderDesktopSessions(nonCliSessions);
}

async function loadSess() {
  const f = document.getElementById('sFilt').value;
  const q = document.getElementById('sSearch').value.trim();
  let url = '/api/sessions?limit=40' + sourceParam();
  if (f) url += `&project=${encodeURIComponent(f)}`;
  if (q) url += `&q=${encodeURIComponent(q)}`;
  const d = await api(url);
  if (!d) return;
  const sel = document.getElementById('sFilt');
  window._allData.sessions = d;
  renderSessionsData(d);
}

function renderLiveData(d) {
  if (!d) return;
  const badge = document.getElementById('liveBadge');
  if (badge) badge.textContent = (d.calls||[]).length;
  document.getElementById('liveN').textContent = (d.calls||[]).length + (curLang==='zh' ? ' 条' : ' calls');
}
async function loadLive() {
  const d = await api('/api/live' + sourceParam('?'));
  if (!d) return;
  window._allData.live = d;
  const badge = document.getElementById('liveBadge');
  if (badge) badge.textContent = d.calls.length;
  document.getElementById('liveN').textContent = d.calls.length + (curLang==='zh' ? ' 条' : ' calls');
  document.getElementById('tbLive').innerHTML = d.calls.slice(0,80).map(c => {
    const cost = c.cost_usd != null ? '$'+c.cost_usd.toFixed(4) : '—';
    let srcBadge = '';
    if (c.source === 'codex' || (c.project||'').includes('(codex)')) {
      srcBadge = '<span style="font:600 7px var(--font);padding:0 4px;border-radius:3px;background:var(--green-bg,rgba(74,222,128,0.1));color:var(--green);margin-left:3px">CDX</span>';
    }
    const rowSrc = c.source || 'claude';
    return `<tr data-row-source="${rowSrc}"><td>${fmtISO(c.timestamp)}</td><td><span class="mdot" style="background:${mC(c.model)}"></span>${mS(c.model)}</td><td style="max-width:90px;overflow:hidden;text-overflow:ellipsis">${c.project||'—'}${srcBadge}${epBadge(c.entrypoint)}</td><td class="mono"><span class="tk-in">↓</span> ${fmt(c.input_tokens)}</td><td class="mono"><span class="tk-out">↑</span> ${fmt(c.output_tokens)}</td><td class="mono"><span class="tk-cr">⟲</span> ${fmt(c.cache_read)}</td><td class="mono"><span class="tk-cw">⟳</span> ${fmt(c.cache_create)}</td><td class="mono" style="color:var(--green)">${cost}</td></tr>`;
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
  url += sourceParam();
  const d = await api(url);
  if (!d) return;
  const tp = Math.ceil(d.total / logLimit) || 1;
  document.getElementById('logTotal').textContent = d.total + (curLang==='zh' ? ' 条' : ' records');
  document.getElementById('tbLogs').innerHTML = d.logs.map(c => {
    const ts = relativeTime(c.timestamp);
    const sc = c.status === 200 ? 'badge-success' : 'badge-error';
    const ttft = c.ttft_ms != null ? (c.ttft_ms < 1000 ? c.ttft_ms+'ms' : (c.ttft_ms/1000).toFixed(1)+'s') : '—';
    const tc = c.ttft_ms != null ? (c.ttft_ms < 3000 ? 'ttft-green' : c.ttft_ms < 10000 ? 'ttft-yellow' : 'ttft-red') : '';
    const dur = c.duration_ms != null ? (c.duration_ms < 1000 ? c.duration_ms+'ms' : c.duration_ms < 60000 ? (c.duration_ms/1000).toFixed(1)+'s' : (c.duration_ms/60000).toFixed(1)+'m') : '—';
    let cb = '';
    if (c.source === 'codex' || (c.project||'').includes('(codex)')) {
      cb = `<span style="font:600 7px var(--font);padding:0 4px;border-radius:3px;background:var(--green-bg,rgba(74,222,128,0.1));color:var(--green);margin-left:3px">CDX</span>`;
    } else if ((c.project||'').includes('(cloud)') || (c.project||'').includes('远程')) {
      const lbl = curLang==='zh' ? '云' : '☁';
      cb = `<span style="font:600 7px var(--font);padding:0 4px;border-radius:3px;background:var(--blue-bg);color:var(--blue);margin-left:3px">${lbl}</span>`;
    }
    const rowCost = c.cost_usd != null ? '$'+c.cost_usd.toFixed(4) : '—';
    const logSrc = c.source || 'claude';
    return `<tr data-row-source="${logSrc}"><td title="${c.timestamp}">${ts}</td><td style="max-width:110px;overflow:hidden;text-overflow:ellipsis">${c.project||'—'}${cb}${epBadge(c.entrypoint)}</td><td><span class="mdot" style="background:${mC(c.model)}"></span>${mS(c.model)}</td><td class="mono"><span class="tk-in">↓</span> ${fmt(c.input_tokens)}</td><td class="mono"><span class="tk-out">↑</span> ${fmt(c.output_tokens)}</td><td class="mono"><span class="tk-cw">⟳</span> ${fmt(c.cache_create)}</td><td class="mono"><span class="tk-cr">⟲</span> ${fmt(c.cache_read)}</td><td class="mono" style="color:var(--green)">${rowCost}</td><td class="mono ${tc}">${ttft}</td><td class="mono">${dur}</td><td><span class="badge ${sc}">${c.status||200}</span></td></tr>`;
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

/* ---- Tool Distribution ---- */
const TOOL_COLORS = {
  'Read':'#60a5fa','Edit':'#fbbf24','Bash':'#4ade80','Write':'#c084fc',
  'Grep':'#f87171','Glob':'#22d3ee','Agent':'#fb923c'
};
let chTools;

/* ---- Coding Rhythm + Work Mode + Model DNA ---- */
async function loadRhythm() {
  const d = await api('/api/rhythm' + sourceParam('?'));
  if (!d) return;

  // Coding Rhythm — horizontal bars
  const el = document.getElementById('rhythmBars');
  if (el && d.rhythm) {
    const labels = {morning: curLang==='zh'?'🌅 上午 6-12':'🌅 Morning', afternoon: curLang==='zh'?'☀️ 下午 12-18':'☀️ Afternoon', evening: curLang==='zh'?'🌆 晚上 18-24':'🌆 Evening', night: curLang==='zh'?'🌙 夜间 0-6':'🌙 Night'};
    const colors = {morning:'#fbbf24', afternoon:'#fb923c', evening:'#c084fc', night:'#60a5fa'};
    el.innerHTML = Object.entries(d.rhythm.periods).map(([k,pct]) =>
      `<div style="display:flex;align-items:center;gap:10px;margin:8px 0">
        <span style="font-size:12px;width:110px;flex-shrink:0">${labels[k]||k}</span>
        <div style="flex:1;height:20px;background:var(--bg-4);border-radius:10px;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:${colors[k]};border-radius:10px;transition:width .8s ease"></div>
        </div>
        <span class="mono" style="font-size:12px;width:35px;text-align:right">${pct}%</span>
      </div>`
    ).join('') + `<div style="font-size:11px;color:var(--text-2);margin-top:8px">${curLang==='zh'?'高峰时段':'Peak hour'}: <b style="color:var(--text-0)">${d.rhythm.peak_hour}:00</b></div>`;
  }

  // Work Mode — stacked bar
  const wm = document.getElementById('workModeChart');
  if (wm && d.work_mode) {
    const w = d.work_mode;
    const modeLabels = {exploration: curLang==='zh'?'探索 (Read/Grep/Glob)':'Exploration', building: curLang==='zh'?'构建 (Write/Edit)':'Building', execution: curLang==='zh'?'执行 (Bash/Agent)':'Execution'};
    const modeColors = {exploration:'#60a5fa', building:'#fbbf24', execution:'#4ade80'};
    const primary = curLang==='zh' ? (w.primary==='exploration'?'探索者':w.primary==='building'?'构建者':'执行者') : (w.primary.charAt(0).toUpperCase()+w.primary.slice(1)+' Focus');
    wm.innerHTML = `<div style="font:700 18px var(--mono);color:var(--text-0);margin-bottom:12px">${primary}</div>
      <div style="display:flex;height:24px;border-radius:12px;overflow:hidden;margin-bottom:14px">
        ${w.exploration?`<div style="width:${w.exploration}%;background:${modeColors.exploration}" title="Exploration ${w.exploration}%"></div>`:''}
        ${w.building?`<div style="width:${w.building}%;background:${modeColors.building}" title="Building ${w.building}%"></div>`:''}
        ${w.execution?`<div style="width:${w.execution}%;background:${modeColors.execution}" title="Execution ${w.execution}%"></div>`:''}
      </div>
      ${Object.entries(modeLabels).map(([k,label]) => `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px"><span style="width:8px;height:8px;border-radius:50%;background:${modeColors[k]}"></span>${label} <span class="mono" style="margin-left:auto">${w[k]}%</span> <span style="color:var(--text-2)">(${fmt(w.raw[k])})</span></div>`).join('')}`;
  }

  // Model DNA — horizontal stacked bar
  const dna = document.getElementById('modelDNAChart');
  if (dna && d.model_dna) {
    const total = Object.values(d.model_dna).reduce((s,v)=>s+v,0) || 1;
    const familyColors = {Opus:'#c084fc', Sonnet:'#60a5fa', Haiku:'#4ade80', 'GPT/Codex':'#10b981', Other:'#6b7280'};
    dna.innerHTML = `<div style="display:flex;height:28px;border-radius:14px;overflow:hidden;margin-bottom:14px">
        ${Object.entries(d.model_dna).map(([k,v]) => {const pct = (v/total*100).toFixed(1); return v > 0 ? `<div style="width:${pct}%;background:${familyColors[k]||'#6b7280'}" title="${k} ${pct}%"></div>` : '';}).join('')}
      </div>
      ${Object.entries(d.model_dna).map(([k,v]) => {const pct = (v/total*100).toFixed(1); return `<div style="display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12px"><span style="width:8px;height:8px;border-radius:50%;background:${familyColors[k]||'#6b7280'}"></span><span style="flex:1">${k}</span><span class="mono">${fmt(v)}</span><span style="color:var(--text-2);width:45px;text-align:right">${pct}%</span></div>`;}).join('')}`;
  }
}
async function loadTools() {
  try {
    const d = await api('/api/tools' + sourceParam('?'));
  if (!d) return;
    const entries = Object.entries(d.tools || {}).sort((a,b) => b[1].calls - a[1].calls);
    if (!entries.length) return;
    const labels = entries.map(([n]) => n);
    const series = entries.map(([,v]) => v.calls);
    const colors = entries.map(([n]) => TOOL_COLORS[n] || '#9ca3af');
    const dk = document.body.dataset.theme === 'dark';
    if (chTools) chTools.destroy();
    chTools = new ApexCharts(document.getElementById('chartTools'), {
      chart:{type:'donut',height:190,background:'transparent',foreColor:dk?'#a1a1aa':'#71717a'},
      series, labels, colors,
      plotOptions:{pie:{donut:{size:'60%',labels:{show:true,name:{show:false},value:{show:true,fontSize:'15px',fontWeight:700,fontFamily:'JetBrains Mono',color:dk?'#e2e8f0':'#09090b',formatter:()=>fmt(d.total_calls)},total:{show:true,label:'Total',formatter:()=>fmt(d.total_calls)}}}}},
      dataLabels:{enabled:false},legend:{show:false},stroke:{width:0},
      theme:apexTheme(),
      tooltip:{style:{fontFamily:'JetBrains Mono',fontSize:'11px'},y:{formatter:v=>fmt(v)+' calls'}}
    });
    chTools.render();
    const listEl = document.getElementById('toolsList');
    if (listEl) {
      listEl.innerHTML = entries.slice(0,8).map(([name,v]) => {
        const c = TOOL_COLORS[name] || '#9ca3af';
        return `<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:8px;height:8px;border-radius:50%;background:${c};flex-shrink:0"></span><span style="font-size:11px;flex:1">${name}</span><span class="mono" style="font-size:10px;color:var(--fg-2)">${fmt(v.calls)}</span><span style="font-size:9px;color:var(--fg-3)">${v.sessions}s</span></div>`;
      }).join('');
    }
  } catch(e) { console.warn('loadTools failed:', e); }
}

/* ---- Export ---- */
function exportData(format) {
  let url = `/api/export?format=${format}`;
  const start = document.getElementById('filterStart').value;
  const end = document.getElementById('filterEnd').value;
  const model = document.getElementById('filterModel').value;
  const project = document.getElementById('filterProject').value;
  if (start) url += `&start=${encodeURIComponent(new Date(start).toISOString())}`;
  if (end) url += `&end=${encodeURIComponent(new Date(end).toISOString())}`;
  if (model) url += `&model=${encodeURIComponent(model)}`;
  if (project) url += `&project=${encodeURIComponent(project)}`;
  window.open(url, '_blank');
}

/* ---- Session Detail Modal ---- */
async function showSessionDetail(sessionId) {
  if (!sessionId) return;
  const modal = document.getElementById('sessionModal');
  const content = document.getElementById('sessionModalContent');
  const isAlreadyOpen = modal.style.display === 'flex';
  modal.style.display = 'flex';
  const t = I18N[curLang] || I18N.zh;

  if (isAlreadyOpen) {
    // Just toggle active class — don't rebuild DOM
    if (window._chainData && window._chainData.chain) {
      window._chainData.chain.forEach(s => s.is_current = s.session_id === sessionId);
    }
    document.querySelectorAll('.chain-item').forEach(el => {
      const isThis = el.getAttribute('data-sid') === sessionId;
      el.classList.toggle('active', isThis);
    });
    // Don't touch main panel yet — keep old content visible while loading
  } else {
    content.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-2)">${t.loading||'Loading...'}</div>`;
  }

  const d = await api('/api/session-detail?id=' + encodeURIComponent(sessionId));
  if (!d || d.error) {
    content.innerHTML = `<div style="text-align:center;padding:40px;color:var(--red)">${d?.error || 'Error'}</div>`;
    return;
  }

  const s = d.stats || {};
  const dur = s.duration_ms ? (s.duration_ms < 60000 ? (s.duration_ms/1000).toFixed(1)+'s' : (s.duration_ms/60000).toFixed(1)+'m') : '—';
  const costStr = s.total_cost != null ? '$'+s.total_cost.toFixed(2) : '—';
  const modelsStr = (s.models||[]).map(m => mS(m)).join(', ') || '—';

  let toolsBadges = '';
  if (s.tools_summary) {
    toolsBadges = Object.entries(s.tools_summary)
      .sort((a,b) => b[1]-a[1])
      .map(([name, count]) => `<span class="timeline-tool">${name} (${count})</span>`)
      .join('');
  }

  let filesHtml = '';
  if (s.files_touched && Object.keys(s.files_touched).length > 0) {
    const filesEntries = Object.entries(s.files_touched).map(([path, ops]) => {
      const short = path.split('/').slice(-2).join('/');
      return `<div title="${path}"><span style="color:var(--blue)">R:${ops.read}</span> <span style="color:var(--orange)">E:${ops.edit}</span> ${short}</div>`;
    }).join('');
    filesHtml = `<details class="timeline-files"><summary>${t.filesAccessed||'Files Accessed'} (${Object.keys(s.files_touched).length})</summary><div class="timeline-files-list">${filesEntries}</div></details>`;
  }

  let statsHtml = `<div class="modal-stats">
    <div class="modal-stat"><div class="modal-stat-val">${s.messages||0}</div><div class="modal-stat-label">${t.msgs||'Messages'}</div></div>
    <div class="modal-stat"><div class="modal-stat-val">${dur}</div><div class="modal-stat-label">${t.duration||'Duration'}</div></div>
    <div class="modal-stat"><div class="modal-stat-val" style="color:var(--green)">${costStr}</div><div class="modal-stat-label">${t.cost||'Cost'}</div></div>
    <div class="modal-stat"><div class="modal-stat-val">${fmt(s.total_input||0)}</div><div class="modal-stat-label"><span class="tk-in">↓</span> Input</div></div>
    <div class="modal-stat"><div class="modal-stat-val">${fmt(s.total_output||0)}</div><div class="modal-stat-label"><span class="tk-out">↑</span> Output</div></div>
    <div class="modal-stat"><div class="modal-stat-val">${modelsStr}</div><div class="modal-stat-label">${t.model||'Model'}</div></div>
  </div>`;

  if (toolsBadges) {
    statsHtml += `<div style="margin-bottom:12px"><span style="font:600 10px var(--font);color:var(--text-2);margin-right:8px">${t.tools||'Tools'}:</span>${toolsBadges}</div>`;
  }
  statsHtml += filesHtml;

  // Load session chain (async, renders after main content)
  let chainHtml = `<div id="sessionChainArea"><div style="display:flex;align-items:center;gap:8px;padding:8px 0;font-size:11px;color:var(--text-2)"><i class="ph ph-spinner" style="animation:spin 1s linear infinite"></i> ${curLang==='zh'?'加载会话链...':'Loading session chain...'}</div></div>`;

  // Reuse cached chain if same project (avoid re-fetching when navigating within chain)
  const cachedChain = window._chainData;
  const chainPromise = (cachedChain && cachedChain.chain && cachedChain.chain.some(s => s.session_id === sessionId))
    ? Promise.resolve(cachedChain)
    : api('/api/session-chain?id=' + encodeURIComponent(sessionId));

  chainPromise.then(cd => {
    const area = document.getElementById('sessionChainArea');
    if (!area) return;
    if (!cd || !cd.chain || cd.chain.length <= 1) { area.innerHTML = ''; return; }
    // Update is_current flag for the new session
    cd.chain.forEach(s => s.is_current = s.session_id === sessionId);

    const chainTitle = curLang==='zh'?'会话链':'Session Chain';
    const sessLabel = curLang==='zh'?'个会话':'sessions';
    const clickHint = curLang==='zh'?'点击切换':'Click to switch';

    // Store chain data globally for re-sorting
    window._chainData = cd;
    window._chainSessionId = sessionId;

    const sortLabels = {
      time: curLang==='zh'?'时间':'Time',
      msgs: curLang==='zh'?'消息数':'Messages',
      cost: curLang==='zh'?'成本':'Cost',
      duration: curLang==='zh'?'时长':'Duration',
    };

    area.innerHTML = `<div class="chain-sidebar-header">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
          <i class="ph ph-git-branch" style="color:var(--accent);font-size:14px"></i>
          <span style="font:600 12px var(--font);color:var(--text-0)">${chainTitle}</span>
          <span style="font:400 10px var(--font);color:var(--text-2)">${cd.total}</span>
        </div>
        <div style="display:flex;gap:3px;margin-bottom:8px">
          ${Object.entries(sortLabels).map(([k,v]) => `<button class="btn chain-sort-btn${k==='time'?' active':''}" data-sort="${k}" onclick="sortChain('${k}')" style="font-size:9px;padding:2px 7px;border-radius:12px">${v}</button>`).join('')}
        </div>
      </div>
      <div id="chainList" class="chain-sidebar-list"></div>`;

    // Initial sort: time descending, CURRENT pinned to top
    const initChain = [...cd.chain].sort((a,b) => (b.last_ts||'0').localeCompare(a.last_ts||'0'));
    const curIdx = initChain.findIndex(s => s.is_current);
    if (curIdx > 0) initChain.unshift(initChain.splice(curIdx, 1)[0]);
    initChain.forEach((s,i) => s.index = i+1);
    renderChainList(initChain);
  });

  function sortChain(by) {
    if (!window._chainData || !window._chainData.chain) return;
    const chain = [...window._chainData.chain];
    const sorters = {
      time: (a,b) => (b.last_ts||'0').localeCompare(a.last_ts||'0'),
      msgs: (a,b) => (b.messages||0) - (a.messages||0),
      cost: (a,b) => (b.cost_usd||0) - (a.cost_usd||0),
      duration: (a,b) => {
        const parseDur = d => { if (!d) return 0; const h = d.match(/(\d+)h/); const m = d.match(/(\d+)m/); const s = d.match(/(\d+)s/); return (h?parseInt(h[1])*3600:0)+(m?parseInt(m[1])*60:0)+(s?parseInt(s[1]):0); };
        return parseDur(b.duration) - parseDur(a.duration);
      },
    };
    if (sorters[by]) chain.sort(sorters[by]);
    // Pin CURRENT to top
    const ci = chain.findIndex(s => s.is_current);
    if (ci > 0) chain.unshift(chain.splice(ci, 1)[0]);
    // Re-index
    chain.forEach((s,i) => s.index = i+1);
    renderChainList(chain);
    // Update active button
    document.querySelectorAll('.chain-sort-btn').forEach(b => b.classList.toggle('active', b.dataset.sort === by));
  }
  // Make sortChain globally accessible
  window.sortChain = sortChain;

  let eventsHtml = '';
  if (!d.events || d.events.length === 0) {
    eventsHtml = `<div style="text-align:center;padding:20px;color:var(--text-2)">${t.noEvents||'No events found'}</div>`;
  } else {
    // Filter out empty events, then group consecutive assistant events for folding
    const filtered = d.events.filter(ev => {
      if (ev.type === 'user') return !!(ev.content && ev.content.trim());
      // Assistant: keep if has content, tools, or tokens
      return !!((ev.content && ev.content.trim()) || (ev.tools_used && ev.tools_used.length) || ev.input_tokens || ev.output_tokens);
    });
    const groups = [];
    let curGroup = null;
    filtered.forEach(ev => {
      if (ev.type === 'user') {
        if (curGroup) { groups.push(curGroup); curGroup = null; }
        groups.push(ev);
      } else {
        if (!curGroup) curGroup = { type: 'assistant_group', events: [] };
        curGroup.events.push(ev);
      }
    });
    if (curGroup) groups.push(curGroup);

    eventsHtml = groups.map(g => {
      if (g.type === 'user') {
        const timeStr = g.timestamp ? fmtISO(g.timestamp) : '';
        return `<div class="timeline-event user">
          <div class="timeline-event-header">
            <span class="timeline-event-type">${t.sessUser||'User'}</span>
            <span class="timeline-event-time">${timeStr}</span>
          </div>
          <div class="timeline-event-content">${escHtml(g.content||'')}</div>
        </div>`;
      }
      // Assistant group
      const evts = g.events;
      const totalCost = evts.reduce((s,e) => s+(e.cost_usd||0), 0);
      const totalIn = evts.reduce((s,e) => s+(e.input_tokens||0), 0);
      const totalOut = evts.reduce((s,e) => s+(e.output_tokens||0), 0);
      const allTools = evts.flatMap(e => e.tools_used||[]);
      const toolCounts = {};
      allTools.forEach(t => toolCounts[t] = (toolCounts[t]||0)+1);
      const firstTime = evts[0]?.timestamp ? fmtISO(evts[0].timestamp) : '';
      const summaryMeta = [
        `${evts.length} ${curLang==='zh'?'轮':'turns'}`,
        '↓'+fmt(totalIn), '↑'+fmt(totalOut),
        '$'+totalCost.toFixed(4)
      ].join(' · ');
      const toolsBadges = Object.entries(toolCounts).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([n,c])=>`<span class="timeline-tool">${n}(${c})</span>`).join('');

      // Helper: render a single assistant event (full or compact)
      function renderOneAssistant(ev, compact) {
        const timeStr = ev.timestamp ? fmtISO(ev.timestamp) : '';
        const hasContent = !!(ev.content && ev.content.trim());
        const tools = ev.tools_used || [];
        const metaParts = [];
        if (ev.model) metaParts.push(mS(ev.model));
        if (ev.input_tokens) metaParts.push('↓'+fmt(ev.input_tokens));
        if (ev.output_tokens) metaParts.push('↑'+fmt(ev.output_tokens));
        if (ev.cost_usd) metaParts.push('$'+ev.cost_usd.toFixed(4));

        // Tool-only (no text content) → compact single line
        if (!hasContent && tools.length > 0) {
          return `<div class="timeline-compact">
            <span class="timeline-event-time">${timeStr}</span>
            <span class="timeline-event-meta">${metaParts.join(' · ')}</span>
            ${tools.map(tn=>`<span class="timeline-tool">${tn}</span>`).join('')}
          </div>`;
        }

        const toolsLine = tools.length ? `<div class="timeline-tools">${tools.map(tn=>`<span class="timeline-tool">${tn}</span>`).join('')}</div>` : '';
        const style = compact ? ' style="margin:4px 0;padding:10px 14px;border-left-width:2px"' : '';
        return `<div class="timeline-event assistant"${style}>
          <div class="timeline-event-header">
            ${compact?'':`<span class="timeline-event-type">${t.sessAssistant||'Assistant'}</span>`}
            <span class="timeline-event-time">${timeStr}</span>
            <span class="timeline-event-meta">${metaParts.join(' · ')}</span>
          </div>
          ${hasContent?`<div class="timeline-event-content">${escHtml(ev.content)}</div>`:''}
          ${toolsLine}
        </div>`;
      }

      if (evts.length === 1) {
        return renderOneAssistant(evts[0], false);
      }

      // Multiple consecutive assistant events — fold them
      const innerHtml = evts.map(ev => renderOneAssistant(ev, true)).join('');

      return `<details class="timeline-group">
        <summary class="timeline-group-summary">
          <span class="timeline-event-type">${t.sessAssistant||'Assistant'}</span>
          <span class="timeline-event-time">${firstTime}</span>
          <span class="timeline-event-meta">${summaryMeta}</span>
          ${toolsBadges ? `<div class="timeline-tools" style="margin-top:4px">${toolsBadges}</div>` : ''}
        </summary>
        <div class="timeline-group-body">${innerHtml}</div>
      </details>`;
    }).join('');
  }

  const actionBar = `<div class="modal-actions">
    <button class="btn" onclick="navigator.clipboard.writeText('${sessionId}');notyf.success(curLang==='zh'?'Session ID 已复制':'Session ID copied')"><i class="ph ph-copy"></i> ID</button>
    <button class="btn" onclick="navigator.clipboard.writeText('claude --resume ${sessionId}');notyf.success(curLang==='zh'?'Resume 命令已复制':'Resume command copied')"><i class="ph ph-terminal-window"></i> Resume</button>
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:document.querySelector('.modal-main-panel').scrollHeight,behavior:'smooth'})"><i class="ph ph-arrow-down"></i> ${curLang==='zh'?'底部':'Bottom'}</button>
  </div>`;
  const fab = `<div class="modal-fab">
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:0,behavior:'smooth'})" title="Top"><i class="ph ph-arrow-up"></i></button>
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:document.querySelector('.modal-main-panel').scrollHeight,behavior:'smooth'})" title="Bottom"><i class="ph ph-arrow-down"></i></button>
  </div>`;
  const mainContent = `<h3 style="font:700 18px var(--font);color:var(--text-0);margin:0 0 16px 0">${t.sessionDetail||'Session Detail'}</h3>
      ${actionBar}${statsHtml}
      <div style="margin-top:16px">${eventsHtml}</div>
      ${fab}`;

  if (isAlreadyOpen) {
    // Smooth swap: fade out old → replace → fade in new
    const mainPanel = document.querySelector('.modal-main-panel');
    if (mainPanel) {
      mainPanel.style.transition = 'opacity .12s ease-out';
      mainPanel.style.opacity = '0';
      setTimeout(() => {
        mainPanel.innerHTML = mainContent;
        mainPanel.scrollTop = 0;
        mainPanel.style.transition = 'opacity .2s ease-in';
        mainPanel.style.opacity = '1';
      }, 120);
    }
  } else {
    content.innerHTML = `<div class="modal-split">
      <div class="modal-chain-panel" id="modalChainPanel">${chainHtml}</div>
      <div class="modal-main-panel" style="transition:opacity .2s">
        ${mainContent}
      </div>
    </div>`;
  }
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderChainList(chain) {
  const el = document.getElementById('chainList');
  if (!el) return;
  el.innerHTML = chain.map((s, i) => {
    const isCur = s.is_current;
    const ts = s.last_ts ? new Date(s.last_ts).toLocaleString(curLang==='zh'?'zh-CN':'en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '—';
    const costStr = s.cost_usd ? '$'+s.cost_usd.toFixed(0) : '';
    let prompt = (s.last_prompt || '').split('\n').map(l=>l.trim()).filter(l=>l).join(' ').trim();
    if (prompt.length > 35) prompt = prompt.slice(0,35)+'…';
    return `<div class="chain-item${isCur?' active':''}" data-sid="${s.session_id}" ${isCur?'':`onclick="showSessionDetail('${s.session_id}')"`}>
      <div class="chain-item-top">
        <span class="chain-item-idx">#${s.index||(i+1)}</span>
        ${isCur?'<span class="chain-item-cur">●</span>':''}
        <span class="chain-item-meta">${s.messages}${curLang==='zh'?'条':'m'} ${costStr}</span>
      </div>
      ${prompt?`<div class="chain-item-prompt">${escHtml(prompt)}</div>`:''}
      <div class="chain-item-time">${ts}</div>
    </div>`;
  }).join('');
}

function closeSessionModal(e) {
  if (e && e.target && e.target !== document.getElementById('sessionModal')) return;
  document.getElementById('sessionModal').style.display = 'none';
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const modal = document.getElementById('sessionModal');
    if (modal && modal.style.display !== 'none') {
      modal.style.display = 'none';
    }
  }
});

/* ---- Weekly Comparison ---- */
let _compareMode = 'daily'; // 'daily' or 'weekly'
function toggleCompareMode() {
  _compareMode = _compareMode === 'daily' ? 'weekly' : 'daily';
  // Trigger flip animation
  const flipEl = document.getElementById('compareFlip');
  const toggleEl = document.getElementById('compareToggle');
  if (flipEl) {
    flipEl.classList.add('flipped');
    if (toggleEl) toggleEl.classList.toggle('flipped', _compareMode === 'weekly');
    setTimeout(() => {
      renderComparison();
      flipEl.classList.remove('flipped');
    }, 300);
  } else {
    renderComparison();
  }
}
function renderComparison() {
  const wrap = document.getElementById('weeklyCompare');
  const el = document.getElementById('weekCompareContent');
  const titleEl = document.getElementById('compareTitle');
  const cd = window._compareData;
  if (!wrap || !el || !cd) return;

  const t = I18N[curLang] || I18N.zh;
  const isDaily = _compareMode === 'daily';
  const data = isDaily ? cd.daily : cd.weekly;
  if (!data) { wrap.style.display = 'none'; return; }

  const cur = isDaily ? (data.today || {}) : (data.this_week || {});
  const prev = isDaily ? (data.yesterday || {}) : (data.last_week || {});
  const cp = data.change_pct || {};

  if (cur.messages === 0 && prev.messages === 0) { wrap.style.display = 'none'; return; }
  wrap.style.display = '';

  // Update title
  if (titleEl) titleEl.textContent = isDaily ? (curLang==='zh'?'日环比':'Day over Day') : (curLang==='zh'?'周环比':'Week over Week');

  const prevLabel = isDaily ? (curLang==='zh'?'昨日':'Yesterday') : (curLang==='zh'?'上周':'Last Week');
  const curLabel = isDaily ? (curLang==='zh'?'今日':'Today') : (curLang==='zh'?'本周':'This Week');

  const metrics = [
    { label:t.msgs||'Messages', val:cur.messages||0, prev:prev.messages||0, pct:cp.messages||0, fmtFn:v=>fmt(v) },
    { label:t.tokens||'Tokens', val:cur.tokens||0, prev:prev.tokens||0, pct:cp.tokens||0, fmtFn:v=>fmt(v) },
    { label:t.cost||'Cost', val:cur.cost||0, prev:prev.cost||0, pct:cp.cost||0, fmtFn:v=>'$'+v.toFixed(2) },
    { label:t.sessions_l||'Sessions', val:cur.sessions||0, prev:prev.sessions||0, pct:cp.sessions||0, fmtFn:v=>fmt(v) },
  ];

  el.innerHTML = `<div class="week-compare-row">${metrics.map(m => {
    const dir = m.pct > 0 ? 'up' : m.pct < 0 ? 'down' : 'flat';
    const arrow = m.pct > 0 ? '↑' : m.pct < 0 ? '↓' : '→';
    return `<div class="week-compare-item">
      <div class="week-compare-label">${m.label}</div>
      <div class="week-compare-vals">
        <span class="week-compare-current">${m.fmtFn(m.val)}</span>
        <span class="week-compare-change ${dir}">${arrow} ${Math.abs(m.pct).toFixed(0)}%</span>
      </div>
      <div class="week-compare-prev">${prevLabel}: ${m.fmtFn(m.prev)}</div>
    </div>`;
  }).join('')}</div>`;
}

/* ===== Settings ===== */
async function loadSettings() {
  const d = await api('/api/settings');
  if (!d) return;

  // API config
  document.getElementById('settingSessionKey').value = d.claude_session_key || '';
  document.getElementById('settingOrgId').value = d.claude_org_id || '';

  // Pricing table
  renderPricingTable(d.custom_pricing || {}, d.detected_models || []);

  // Detected models list
  renderDetectedModels(d.detected_models || []);

  // Data sources
  renderDataSources(d.data_sources || {});
}

function renderPricingTable(pricing, detectedModels) {
  const el = document.getElementById('pricingTable');
  if (!el) return;
  const rows = Object.entries(pricing);
  el.innerHTML = `<div class="tw"><table style="width:100%"><thead><tr>
    <th>${curLang==='zh'?'模型':'Model'}</th><th>Input $/M</th><th>Output $/M</th><th>Cache Read $/M</th><th>Cache Write $/M</th><th></th>
  </tr></thead><tbody id="pricingRows">${rows.map(([model, p]) => pricingRow(model, p)).join('')}</tbody></table></div>`;
}

function pricingRow(model, p) {
  return `<tr>
    <td><input class="filter-input pricing-model" value="${model}" style="width:100%"></td>
    <td><input class="filter-input pricing-input" type="number" step="0.01" value="${p.input||0}" style="width:80px"></td>
    <td><input class="filter-input pricing-output" type="number" step="0.01" value="${p.output||0}" style="width:80px"></td>
    <td><input class="filter-input pricing-cr" type="number" step="0.01" value="${p.cache_read||0}" style="width:80px"></td>
    <td><input class="filter-input pricing-cw" type="number" step="0.01" value="${p.cache_write||0}" style="width:80px"></td>
    <td><button class="btn" onclick="this.closest('tr').remove()" style="padding:4px 8px;color:var(--red)"><i class="ph ph-trash"></i></button></td>
  </tr>`;
}

function addPricingRow() {
  const tbody = document.getElementById('pricingRows');
  if (!tbody) return;
  tbody.insertAdjacentHTML('beforeend', pricingRow('', {input:3, output:15, cache_read:0.3, cache_write:3.75}));
}

async function savePricing() {
  const rows = document.querySelectorAll('#pricingRows tr');
  const pricing = {};
  rows.forEach(row => {
    const model = row.querySelector('.pricing-model')?.value?.trim();
    if (!model) return;
    pricing[model] = {
      input: parseFloat(row.querySelector('.pricing-input')?.value) || 0,
      output: parseFloat(row.querySelector('.pricing-output')?.value) || 0,
      cache_read: parseFloat(row.querySelector('.pricing-cr')?.value) || 0,
      cache_write: parseFloat(row.querySelector('.pricing-cw')?.value) || 0,
    };
  });
  const res = await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({custom_pricing: pricing})});
  if (res.ok) notyf.success(curLang==='zh'?'定价已保存':'Pricing saved');
  else notyf.error(curLang==='zh'?'保存失败':'Save failed');
}

async function saveApiConfig() {
  const sk = document.getElementById('settingSessionKey').value.trim();
  const oid = document.getElementById('settingOrgId').value.trim();
  const body = {};
  if (sk && !sk.includes('***')) body.claude_session_key = sk;
  if (oid && !oid.includes('***')) body.claude_org_id = oid;
  const res = await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  if (res.ok) notyf.success(curLang==='zh'?'配置已保存':'Config saved');
  else notyf.error(curLang==='zh'?'保存失败':'Save failed');
}

function renderDetectedModels(models) {
  const el = document.getElementById('detectedModelsList');
  if (!el) return;
  el.innerHTML = models.map(m => {
    const provider = classifyProvider(m);
    const colors = {Anthropic:'var(--accent)',OpenAI:'var(--green)',ZhipuAI:'var(--blue)',MiniMax:'var(--purple)',Google:'var(--orange)',DeepSeek:'var(--cyan,var(--blue))',Other:'var(--text-2)'};
    return `<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;margin:3px;border-radius:12px;background:var(--bg-3);font:400 11px var(--mono);border:1px solid var(--border-l)">
      <span style="width:6px;height:6px;border-radius:50%;background:${colors[provider]||'var(--text-2)'}"></span>
      ${m} <span style="font-size:9px;color:var(--text-2)">${provider}</span>
    </span>`;
  }).join('');
}

function renderDataSources(sources) {
  const el = document.getElementById('dataSourcesList');
  if (!el) return;
  const t = I18N[curLang] || I18N.zh;
  const items = [];
  const srcInfo = {
    claude_code: { name: t.claudeCode || 'Claude Code', icon: 'ph-terminal-window', color: 'var(--accent)' },
    codex_cli: { name: t.codexCli || 'Codex CLI', icon: 'ph-code', color: 'var(--green)' },
  };
  for (const [key, src] of Object.entries(sources)) {
    const info = srcInfo[key] || { name: key, icon: 'ph-plug', color: 'var(--text-2)' };
    const detected = src.detected;
    const enabled = src.enabled;
    const statusDot = detected ? (enabled ? 'var(--green)' : 'var(--orange)') : 'var(--red)';
    const statusText = detected ? (enabled ? (curLang==='zh'?'已启用':'Enabled') : (curLang==='zh'?'已禁用':'Disabled')) : (curLang==='zh'?'未检测到':'Not detected');
    let detail = src.path || '';
    if (src.model) detail += ` (${src.model})`;
    items.push(`<div style="display:flex;align-items:center;gap:10px;padding:10px 12px;margin:6px 0;border-radius:8px;background:var(--bg-3);border:1px solid var(--border-l)">
      <i class="ph ${info.icon}" style="font-size:18px;color:${info.color}"></i>
      <div style="flex:1">
        <div style="font:600 13px var(--font);color:var(--text-0)">${info.name}</div>
        <div style="font:400 10px var(--mono);color:var(--text-2);margin-top:2px">${detail}</div>
      </div>
      <div style="display:flex;align-items:center;gap:5px">
        <span style="width:7px;height:7px;border-radius:50%;background:${statusDot}"></span>
        <span style="font:500 11px var(--font);color:var(--text-1)">${statusText}</span>
      </div>
    </div>`);
  }
  el.innerHTML = items.join('');
}

function classifyProvider(model) {
  const m = model.toLowerCase();
  if (m.startsWith('claude') || m.includes('anthropic')) return 'Anthropic';
  if (m.startsWith('gpt') || m.includes('openai') || m.includes('codex')) return 'OpenAI';
  if (m.includes('glm') || m.includes('zhipu')) return 'ZhipuAI';
  if (m.includes('minimax')) return 'MiniMax';
  if (m.includes('gemini') || m.includes('google')) return 'Google';
  if (m.includes('deepseek')) return 'DeepSeek';
  if (m.includes('qwen')) return 'Alibaba';
  if (m.includes('mistral')) return 'Mistral';
  if (m.includes('llama') || m.includes('meta')) return 'Meta';
  return 'Other';
}

/* ===== Web Conversations ===== */
async function loadWebConversations() {
  const section = document.getElementById('webConvSection');
  const webConvs = await api('/api/web-conversations');
  const hasWeb = Array.isArray(webConvs) && webConvs.length > 0;
  const desktopSessions = window._allData._desktopSessions || [];
  const hasDesktop = desktopSessions.length > 0;

  if (!hasWeb && !hasDesktop) {
    if (section) section.style.display = 'none';
    return;
  }
  if (section) section.style.display = '';
  renderWebAndDesktop(hasWeb ? webConvs : [], desktopSessions);
}

function renderDesktopSessions(sessions) {
  // Called from renderSessionsData — just store for now, actual render happens in loadWebConversations
  window._allData._desktopSessions = sessions;
}

function renderWebAndDesktop(webConvs, desktopSessions) {
  const el = document.getElementById('webConvList');
  if (!el) return;

  let html = '';

  // Desktop sessions first
  if (desktopSessions.length > 0) {
    html += `<div style="font:600 11px var(--font);color:var(--text-2);text-transform:uppercase;letter-spacing:.5px;padding:8px 16px;display:flex;align-items:center;gap:6px"><span class="ep-badge ep-desktop">Desktop</span> ${desktopSessions.length} ${curLang==='zh'?'个会话':'sessions'}</div>`;
    html += desktopSessions.map(s => {
      const date = s.timestamp ? new Date(typeof s.timestamp === 'number' ? s.timestamp : s.timestamp).toLocaleDateString(curLang==='zh'?'zh-CN':'en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
      const name = escHtml(s.firstPrompt || s.projectShort || (curLang==='zh'?'未命名':'Untitled'));
      const proj = s.projectShort || '';
      return `<div class="web-conv-item" onclick="showSessionDetail('${s.sessionId}')">
        <div class="web-conv-header">
          <span class="ep-badge ep-desktop">Desktop</span>
          <span class="web-conv-name">${name}</span>
          <span class="web-conv-date">${date}</span>
        </div>
        <div class="web-conv-summary">${proj}</div>
      </div>`;
    }).join('');
  }

  // Web conversations
  if (webConvs.length > 0) {
    html += `<div style="font:600 11px var(--font);color:var(--text-2);text-transform:uppercase;letter-spacing:.5px;padding:8px 16px;display:flex;align-items:center;gap:6px;${desktopSessions.length?'margin-top:12px;border-top:1px solid var(--border-l);padding-top:16px':''}"><span class="ep-badge ep-web">Web</span> ${webConvs.length} ${curLang==='zh'?'个对话':'conversations'}</div>`;
    html += renderWebConversationsHtml(webConvs);
  }

  el.innerHTML = html;
}

function renderWebConversationsHtml(conversations) {
  return conversations.map(c => {
    const date = c.updated_at || c.created_at;
    const dateStr = date ? new Date(date).toLocaleDateString(curLang==='zh'?'zh-CN':'en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
    const model = c.model ? c.model.replace('claude-','').replace(/-\d{8}$/,'') : '?';
    const summary = escHtml((c.summary || '').slice(0, 100));
    const name = escHtml(c.name || (curLang==='zh'?'未命名':'Untitled'));
    const uuid = c.uuid || '';
    return `<div class="web-conv-item" onclick="showWebConversation('${uuid}')">
      <div class="web-conv-header">
        <span class="web-conv-model">${model}</span>
        <span class="web-conv-name">${name}</span>
        <span class="web-conv-date">${dateStr}</span>
      </div>
      ${summary ? `<div class="web-conv-summary">${summary}</div>` : ''}
    </div>`;
  }).join('');
}

async function showWebConversation(uuid) {
  if (!uuid) return;
  const modal = document.getElementById('sessionModal');
  const content = document.getElementById('sessionModalContent');
  modal.style.display = 'flex';
  const t = I18N[curLang] || I18N.zh;
  content.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-2)">${t.loading||'Loading...'}</div>`;

  const d = await api('/api/web-conversation-detail?id=' + encodeURIComponent(uuid));
  if (!d || d.error) {
    content.innerHTML = `<div style="text-align:center;padding:40px;color:var(--red)">${escHtml(d?.error || 'Error')}</div>`;
    return;
  }

  const msgs = d.messages || [];
  const dateStr = d.created_at ? new Date(d.created_at).toLocaleDateString(curLang==='zh'?'zh-CN':'en-US',{year:'numeric',month:'short',day:'numeric'}) : '';
  const modelStr = d.model ? d.model.replace('claude-','').replace(/-\d{8}$/,'') : '';

  const eventsHtml = msgs.map(m => {
    const isUser = m.sender === 'human';
    const time = m.created_at ? fmtISO(m.created_at) : '';
    const cls = isUser ? 'user' : 'assistant';
    const label = isUser ? (t.sessUser || 'You') : (t.sessAssistant || 'Claude');
    return `<div class="timeline-event ${cls}">
      <div class="timeline-event-header">
        <span class="timeline-event-type">${label}</span>
        ${time ? `<span class="timeline-event-time">${time}</span>` : ''}
      </div>
      <div class="timeline-event-content">${escHtml(m.text || '')}</div>
    </div>`;
  }).join('');

  const actionBar = `<div class="modal-actions">
    <span style="font:500 10px var(--font);color:var(--text-2);padding:2px 8px;border-radius:12px;background:var(--blue-bg);color:var(--blue)"><i class="ph ph-globe"></i> claude.ai</span>
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:document.querySelector('.modal-main-panel').scrollHeight,behavior:'smooth'})"><i class="ph ph-arrow-down"></i> ${curLang==='zh'?'底部':'Bottom'}</button>
  </div>`;
  const fab = `<div class="modal-fab">
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:0,behavior:'smooth'})" title="Top"><i class="ph ph-arrow-up"></i></button>
    <button class="btn" onclick="document.querySelector('.modal-main-panel').scrollTo({top:document.querySelector('.modal-main-panel').scrollHeight,behavior:'smooth'})" title="Bottom"><i class="ph ph-arrow-down"></i></button>
  </div>`;

  content.innerHTML = `<div class="modal-split">
    <div class="modal-main-panel" style="width:100%">
      <h3 style="font:700 18px var(--font);margin:0 0 8px">${escHtml(d.name || (curLang==='zh'?'对话':'Conversation'))}</h3>
      ${actionBar}
      <div style="font:400 12px var(--font);color:var(--text-2);margin-bottom:16px">
        ${modelStr ? modelStr + ' &middot; ' : ''}${msgs.length} ${t.msgs || 'messages'}${dateStr ? ' &middot; ' + dateStr : ''}
      </div>
      <div class="modal-stats" style="grid-template-columns:repeat(3,1fr)">
        <div class="modal-stat"><div class="modal-stat-val">${msgs.filter(m=>m.sender==='human').length}</div><div class="modal-stat-label">${t.sessUser||'User'}</div></div>
        <div class="modal-stat"><div class="modal-stat-val">${msgs.filter(m=>m.sender==='assistant').length}</div><div class="modal-stat-label">${t.sessAssistant||'Assistant'}</div></div>
        <div class="modal-stat"><div class="modal-stat-val">${msgs.length}</div><div class="modal-stat-label">${t.msgs||'Messages'}</div></div>
      </div>
      <div>${eventsHtml || `<div style="text-align:center;padding:40px;color:var(--text-2)">${t.noEvents||'No messages'}</div>`}</div>
      ${fab}
    </div>
  </div>`;
}

/* ===== v0.6.0: MCP Server Analytics ===== */
let chMcp, chMcpTrend;
const MCP_COLORS = ['#00e5ff','#4ade80','#f97316','#a78bfa','#f472b6','#facc15','#38bdf8','#fb923c','#818cf8','#34d399'];
async function loadMcpStats() {
  try {
    const d = await api('/api/mcp-stats' + sourceParam('?'));
    if (!d || !d.servers || !d.servers.length) {
      const el = document.getElementById('chartMcp'); if(el) el.closest('.card')?.style.setProperty('display','none'); return;
    }
    const el = document.getElementById('chartMcp'); if(el) el.closest('.card')?.style.removeProperty('display');
    const labels = d.servers.map(s => s.name);
    const series = d.servers.map(s => s.calls);
    const colors = d.servers.map((_,i) => MCP_COLORS[i % MCP_COLORS.length]);
    const dk = document.body.dataset.theme === 'dark';
    if (chMcp) chMcp.destroy();
    chMcp = new ApexCharts(document.getElementById('chartMcp'), {
      chart:{type:'donut',height:190,background:'transparent',foreColor:dk?'#a1a1aa':'#71717a'},
      series, labels, colors,
      plotOptions:{pie:{donut:{size:'60%',labels:{show:true,name:{show:false},value:{show:true,fontSize:'15px',fontWeight:700,fontFamily:'JetBrains Mono',color:dk?'#e2e8f0':'#09090b',formatter:()=>fmt(d.total_calls)},total:{show:true,label:'Total',formatter:()=>fmt(d.total_calls)}}}}},
      dataLabels:{enabled:false},legend:{show:false},stroke:{width:0},
      theme:apexTheme(),
      tooltip:{style:{fontFamily:'JetBrains Mono',fontSize:'11px'},y:{formatter:v=>fmt(v)+' calls'}}
    });
    chMcp.render();
    const listEl = document.getElementById('mcpList');
    if (listEl) {
      listEl.innerHTML = d.servers.slice(0,8).map((s,i) => {
        const c = MCP_COLORS[i % MCP_COLORS.length];
        return `<div style="display:flex;align-items:center;gap:6px;margin:3px 0"><span style="width:8px;height:8px;border-radius:50%;background:${c};flex-shrink:0"></span><span style="font-size:11px;flex:1">${s.name}</span><span class="mono" style="font-size:10px;color:var(--fg-2)">${fmt(s.calls)}</span><span style="font-size:9px;color:var(--fg-3)">${s.sessions}s</span></div>`;
      }).join('');
    }
  } catch(e) { console.warn('loadMcpStats:', e); }
}
async function loadMcpTrend() {
  try {
    const d = await api('/api/mcp-trend?days=30' + sourceParam());
    if (!d || !d.tool_type_trend || !d.tool_type_trend.length) return;
    const dk = document.body.dataset.theme === 'dark';
    const t = I18N[curLang] || I18N.zh;
    if (chMcpTrend) chMcpTrend.destroy();
    chMcpTrend = new ApexCharts(document.getElementById('chartMcpTrend'), {
      chart:{type:'area',height:220,background:'transparent',foreColor:dk?'#94a3b8':'#64748b',toolbar:{show:false},zoom:{enabled:false}},
      series:[
        {name:t.builtinTools||'Built-in Tools',data:d.tool_type_trend.map(r=>r.builtin)},
        {name:t.mcpTools||'MCP Tools',data:d.tool_type_trend.map(r=>r.mcp)}
      ],
      xaxis:{categories:d.tool_type_trend.map(r=>r.date.slice(5)),labels:{style:{fontSize:'10px'}},tickAmount:8},
      yaxis:{labels:{style:{fontSize:'10px'},formatter:v=>fmt(v)}},
      colors:['#4ade80','#00e5ff'],
      fill:{type:'gradient',gradient:{shadeIntensity:1,opacityFrom:.4,opacityTo:.05}},
      stroke:{curve:'smooth',width:2},
      dataLabels:{enabled:false},
      grid:{borderColor:dk?'#1e293b':'#e2e8f0',strokeDashArray:3},
      tooltip:{style:{fontFamily:'JetBrains Mono',fontSize:'11px'},y:{formatter:v=>fmt(v)+' calls'}},
      legend:{position:'top',fontSize:'11px',fontFamily:'Inter',labels:{colors:dk?'#94a3b8':'#64748b'}}
    });
    chMcpTrend.render();
  } catch(e) { console.warn('loadMcpTrend:', e); }
}

/* ===== v0.6.1: Rate Limit Predictor ===== */
async function loadRatePrediction() {
  try {
    const d = await api('/api/rate-prediction' + sourceParam('?'));
    if (!d) return;
    const card = document.getElementById('ratePredictCard');
    // Only show if we have some quota data
    if (d.utilization <= 0 && d.burn_rpm_30m <= 0) { if(card) card.style.display='none'; return; }
    if (card) card.style.display = '';

    // Risk badge
    const badge = document.getElementById('riskBadge');
    if (badge) {
      const riskMap = {safe:'risk-safe',caution:'risk-caution',warning:'risk-warning',danger:'risk-danger',critical:'risk-critical'};
      const riskLabelsEn = {safe:'SAFE',caution:'CAUTION',warning:'WARNING',danger:'DANGER',critical:'CRITICAL'};
      const riskLabelsZh = {safe:'安全',caution:'注意',warning:'警告',danger:'危险',critical:'紧急'};
      const rl = curLang === 'zh' ? riskLabelsZh : riskLabelsEn;
      badge.className = riskMap[d.risk] || 'risk-safe';
      badge.textContent = rl[d.risk] || d.risk.toUpperCase();
    }

    // Time to throttle
    const ttEl = document.getElementById('rpTimeLeft');
    if (ttEl) {
      if (d.minutes_to_throttle === null || d.minutes_to_throttle === undefined) {
        ttEl.textContent = '∞'; ttEl.style.color = 'var(--green)';
      } else if (d.minutes_to_throttle <= 0) {
        ttEl.textContent = curLang==='zh'?'已限速':'NOW'; ttEl.style.color = 'var(--red)';
      } else {
        const h = Math.floor(d.minutes_to_throttle / 60);
        const m = d.minutes_to_throttle % 60;
        ttEl.textContent = h > 0 ? `${h}h ${m}m` : `${m}m`;
        ttEl.style.color = d.minutes_to_throttle < 30 ? 'var(--red)' : d.minutes_to_throttle < 60 ? 'var(--orange)' : 'var(--green)';
      }
    }

    // Burn rates
    const brEl = document.getElementById('rpBurnRpm');
    if (brEl) brEl.textContent = d.burn_rpm_30m || '0';
    const btEl = document.getElementById('rpBurnTpm');
    if (btEl) btEl.textContent = fmt(d.burn_tpm_30m || 0);

    // Safe RPM
    const srEl = document.getElementById('rpSafeRpm');
    if (srEl) {
      srEl.textContent = d.safe_rpm ? d.safe_rpm.toFixed(1) : '—';
      srEl.style.color = 'var(--green)';
    }
  } catch(e) { console.warn('loadRatePrediction:', e); }
}

/* ===== v0.6.2: Efficiency Analysis ===== */
let chEffTrend;
async function loadEfficiency() {
  try {
    const d = await api('/api/efficiency' + sourceParam('?'));
    if (!d) return;

    const panel = document.getElementById('efficiencyPanel');
    if (!panel) return;

    const g = d.global || {};
    const modes = d.modes || {};
    const t = I18N[curLang] || I18N.zh;
    const modeColors = {exploration:'#38bdf8',building:'#4ade80',debugging:'#f97316',review:'#a78bfa'};
    const modeLabels = {exploration:t.modeExploration||'Exploration',building:t.modeBuilding||'Building',debugging:t.modeDebugging||'Debugging',review:t.modeReview||'Review'};
    const modePct = modes.percentages || {};
    const modeCounts = modes.counts || {};
    const gradeColors = {Excellent:'var(--green)',Good:'var(--blue)','Fair':'var(--orange)',Poor:'var(--red)'};
    const gradeLabelsZh = {Excellent:'优秀',Good:'良好',Fair:'一般',Poor:'较差'};
    const gradeDisplay = curLang==='zh' ? (gradeLabelsZh[g.cache_grade]||g.cache_grade||'—') : (g.cache_grade||'—');

    panel.innerHTML = `
      <div class="eff-grid">
        <div class="eff-stat"><div class="eff-stat-val" style="color:var(--blue)">${g.output_ratio || 0}%</div><div class="eff-stat-label">${t.outputRatio||'Output Ratio'}</div></div>
        <div class="eff-stat"><div class="eff-stat-val" style="color:${gradeColors[g.cache_grade]||'var(--text-0)'}">${g.cache_rate || 0}%</div><div class="eff-stat-label">${t.cacheGrade||'Cache Grade'} (${gradeDisplay})</div></div>
        <div class="eff-stat"><div class="eff-stat-val">${g.total_sessions_analyzed || 0}</div><div class="eff-stat-label">${t.sessionsAnalyzed||'Sessions Analyzed'}</div></div>
      </div>
      <div style="font:600 11px var(--font);color:var(--text-1);margin-bottom:6px">${t.interactionModes||'Interaction Modes'}</div>
      <div class="eff-mode-bar">
        ${Object.entries(modePct).filter(([,v])=>v>0).map(([k,v]) => `<div style="width:${v}%;background:${modeColors[k]||'#6b7280'}" title="${modeLabels[k]||k} ${v}%"></div>`).join('')}
      </div>
      <div class="eff-mode-legend">
        ${Object.entries(modePct).map(([k,v]) => `<div class="eff-mode-item"><span class="eff-mode-dot" style="background:${modeColors[k]||'#6b7280'}"></span>${modeLabels[k]||k} <span class="mono" style="font-size:10px">${v}%</span> <span style="color:var(--text-2)">(${modeCounts[k]||0})</span></div>`).join('')}
      </div>
    `;

    // Efficiency trend chart
    const trend = d.trend || [];
    if (trend.length > 0) {
      const dk = document.body.dataset.theme === 'dark';
      if (chEffTrend) chEffTrend.destroy();
      chEffTrend = new ApexCharts(document.getElementById('chartEffTrend'), {
        chart:{type:'line',height:220,background:'transparent',foreColor:dk?'#94a3b8':'#64748b',toolbar:{show:false},zoom:{enabled:false}},
        series:[
          {name:(t.outputRatio||'Output Ratio')+' %',data:trend.map(r=>r.output_ratio)},
          {name:(t.cacheRate||'Cache Rate')+' %',data:trend.map(r=>r.cache_rate)}
        ],
        xaxis:{categories:trend.map(r=>r.date.slice(5)),labels:{style:{fontSize:'10px'}},tickAmount:8},
        yaxis:{min:0,max:100,labels:{style:{fontSize:'10px'},formatter:v=>v+'%'}},
        colors:['#3b82f6','#22c55e'],
        stroke:{curve:'smooth',width:2},
        dataLabels:{enabled:false},
        grid:{borderColor:dk?'#1e293b':'#e2e8f0',strokeDashArray:3},
        tooltip:{style:{fontFamily:'JetBrains Mono',fontSize:'11px'},y:{formatter:v=>v+'%'}},
        legend:{position:'top',fontSize:'11px',fontFamily:'Inter',labels:{colors:dk?'#94a3b8':'#64748b'}},
        markers:{size:0,hover:{size:4}}
      });
      chEffTrend.render();
    }
  } catch(e) { console.warn('loadEfficiency:', e); }
}

/* ===== v0.7.0: Cost Optimization Insights ===== */
async function loadInsights() {
  try {
    const d = await api('/api/insights' + sourceParam('?'));
    if (!d || !d.insights || !d.insights.length) {
      const c = document.getElementById('insightsCard'); if(c) c.style.display='none'; return;
    }
    const c = document.getElementById('insightsCard'); if(c) c.style.display='';
    const t = I18N[curLang] || I18N.zh;
    const list = document.getElementById('insightsList');
    if (!list) return;
    list.innerHTML = d.insights.slice(0,4).map(i => {
      const title = curLang==='zh' ? i.title_zh : i.title_en;
      const desc = curLang==='zh' ? i.desc_zh : i.desc_en;
      const savingsHtml = i.savings_usd > 0 ? `<div class="insight-savings">${t.savingPotential||'Saving potential'}: $${i.savings_usd}</div>` : '';
      return `<div class="insight-item">
        <div class="insight-icon ${i.severity}"><i class="ph ${i.icon||'ph-lightbulb'}"></i></div>
        <div style="flex:1"><div class="insight-title">${title}</div><div class="insight-desc">${desc}</div>${savingsHtml}</div>
      </div>`;
    }).join('');
  } catch(e) { console.warn('loadInsights:', e); }
}

/* ===== v0.7.1: Budget Management ===== */
async function loadBudget() {
  try {
    const d = await api('/api/budget' + sourceParam('?'));
    if (!d || !d.configured) {
      const c = document.getElementById('budgetCard'); if(c) c.style.display='none'; return;
    }
    const c = document.getElementById('budgetCard'); if(c) c.style.display='';
    const t = I18N[curLang] || I18N.zh;
    const bars = document.getElementById('budgetBars');
    if (!bars) return;
    const labels = {daily:t.budgetDaily||'Daily',weekly:t.budgetWeekly||'Weekly',monthly:t.budgetMonthly||'Monthly'};
    let html = '';
    for (const [period, label] of Object.entries(labels)) {
      const s = d.status[period];
      if (!s) continue;
      const pct = Math.min(s.pct, 100);
      const overText = s.pct > 100 ? ` (${t.overBudget||'Over budget'}!)` : '';
      html += `<div class="budget-row">
        <div class="budget-label"><span>${label}</span><span>$${s.spent.toFixed(2)} / $${s.limit.toFixed(2)}${overText}</span></div>
        <div class="budget-bar"><div class="budget-fill ${s.alert}" style="width:${pct}%"></div></div>
      </div>`;
    }
    bars.innerHTML = html || `<div style="font:400 11px var(--font);color:var(--text-2)">${t.noInsights||'No budget set'}</div>`;
    // Populate settings form
    const bd = document.getElementById('budgetDaily');
    const bw = document.getElementById('budgetWeekly');
    const bm = document.getElementById('budgetMonthly');
    if (bd && d.budget.daily) bd.value = d.budget.daily;
    if (bw && d.budget.weekly) bw.value = d.budget.weekly;
    if (bm && d.budget.monthly) bm.value = d.budget.monthly;
  } catch(e) { console.warn('loadBudget:', e); }
}
async function saveBudget() {
  const daily = parseFloat(document.getElementById('budgetDaily')?.value) || 0;
  const weekly = parseFloat(document.getElementById('budgetWeekly')?.value) || 0;
  const monthly = parseFloat(document.getElementById('budgetMonthly')?.value) || 0;
  try {
    await fetch('/api/budget', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({daily,weekly,monthly})});
    notyf.success(curLang==='zh'?'预算已保存':'Budget saved');
    loadBudget();
  } catch(e) { notyf.error(curLang==='zh'?'保存失败':'Save failed'); }
}

/* ===== v0.7.2: Comparison Report ===== */
async function loadReport(type) {
  type = type || 'weekly';
  // Toggle active button
  document.getElementById('btnReportWeekly')?.classList.toggle('active', type==='weekly');
  document.getElementById('btnReportMonthly')?.classList.toggle('active', type==='monthly');
  const el = document.getElementById('reportContent');
  if (!el) return;
  try {
    const d = await api(`/api/report?type=${type}` + sourceParam());
    if (!d) { el.innerHTML = ''; return; }
    const t = I18N[curLang] || I18N.zh;
    const c = d.current, p = d.previous, dl = d.deltas;
    const periodLabel = curLang==='zh' ? d.period_label_zh : d.period_label_en;

    function deltaHtml(val) {
      if (val === 0) return `<div class="report-delta flat">—</div>`;
      const cls = val > 0 ? 'up' : 'down';
      const arrow = val > 0 ? '↑' : '↓';
      return `<div class="report-delta ${cls}">${arrow} ${Math.abs(val).toFixed(1)}%</div>`;
    }

    const metrics = [
      {key:'messages', label:t.msgs||'Messages', cur:c.messages, prev:p.messages, delta:dl.messages, fmt:v=>v.toLocaleString()},
      {key:'sessions', label:t.sessions_l||'Sessions', cur:c.sessions, prev:p.sessions, delta:dl.sessions, fmt:v=>v.toLocaleString()},
      {key:'tokens', label:t.tokens||'Tokens', cur:c.tokens, prev:p.tokens, delta:dl.tokens, fmt:v=>fmt(v)},
      {key:'cost', label:t.cost||'Cost', cur:c.cost, prev:p.cost, delta:dl.cost, fmt:v=>'$'+v.toFixed(2)},
      {key:'tools', label:t.tools||'Tools', cur:c.tools, prev:p.tools, delta:dl.tools, fmt:v=>v.toLocaleString()},
    ];

    el.innerHTML = `
      <div style="font:600 13px var(--font);color:var(--text-0);margin-bottom:12px">${periodLabel}</div>
      <div class="report-grid">
        ${metrics.map(m => `<div class="report-stat">
          <div class="report-stat-val">${m.fmt(m.cur)}</div>
          <div class="report-stat-label">${m.label}</div>
          ${deltaHtml(m.delta)}
          <div style="font:400 9px var(--mono);color:var(--text-2);margin-top:2px">${t.previous||'Prev'}: ${m.fmt(m.prev)}</div>
        </div>`).join('')}
      </div>
      ${d.highlights && d.highlights.length ? `
        <div style="font:600 11px var(--font);color:var(--text-1);margin-bottom:8px">${t.highlights||'Highlights'}</div>
        <div class="report-highlights">
          ${d.highlights.map(h => `<div class="report-hl"><i class="ph ${h.icon}"></i><div><div style="font:400 10px var(--font);color:var(--text-2)">${curLang==='zh'?h.label_zh:h.label_en}</div><div style="font:700 13px var(--mono);color:var(--text-0)">${h.value}</div></div></div>`).join('')}
        </div>` : ''}
    `;
  } catch(e) { console.warn('loadReport:', e); el.innerHTML = ''; }
}

/* ===== Init ===== */
async function init() {
  try {
    // Load everything in parallel — don't block on slow remote calls
    await Promise.all([
      loadStatus(), loadOverview(), loadCharts(), loadModels(),
      loadProjects(), loadSess(), loadLive(), loadLogs(), loadTools(),
      loadWebConversations(), loadTodayBreakdown(),
      loadRatePrediction(), loadMcpStats(), loadMcpTrend(), loadEfficiency(),
      loadInsights(), loadBudget()
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
  const savedPage = localStorage.getItem('claude_dash_page') || 'overview';
  switchPage(savedPage);
}

async function refreshAll() {
  document.getElementById('lastUp').textContent = curLang==='zh' ? '刷新中...' : 'Refreshing...';
  try {
    await api('/api/overview?refresh=1' + sourceParam());
    await Promise.all([loadStatus(), loadOverview(), loadCharts(), loadModels(), loadProjects(), loadSess(), loadLive(), loadLogs(), loadTools(), loadWebConversations(), loadTodayBreakdown(), loadRatePrediction(), loadMcpStats(), loadMcpTrend(), loadEfficiency(), loadInsights(), loadBudget()]);
    notyf.success(curLang==='zh' ? '已更新' : 'Updated');
  } catch { notyf.error(curLang==='zh' ? '刷新失败' : 'Refresh failed'); }
  document.getElementById('lastUp').textContent = (curLang==='zh' ? '更新于 ' : 'Updated ') + new Date().toLocaleTimeString(curLang==='zh'?'zh-CN':'en-US',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

document.addEventListener('DOMContentLoaded', () => { init(); });

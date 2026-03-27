# Changelog / 更新日志

All notable changes to CCDash will be documented in this file.
所有 CCDash 的重要变更都将记录在此文件中。

---

## [0.7.0] — 2026-03-27

### 🚀 New Features

#### Cost Optimization Engine (v0.7.0)
- **Smart insights** — rule-driven optimization suggestions on Overview page
- **Model downgrade detection** — identifies Opus usage for simple tasks, estimates savings from Sonnet
- **Cache optimization** — detects low cache hit rate with savings estimate
- **Cost anomaly detection** — flags days with 2.5x above average cost
- **Peak hour warning** — identifies usage concentration risk
- **`/api/insights`** — returns prioritized optimization suggestions with savings estimates

#### Token Budget Management (v0.7.1)
- **Budget configuration** — set daily/weekly/monthly cost limits in Settings
- **Budget progress bars** — real-time spend vs limit on Overview page
- **Alert thresholds** — OK / Warning (60%) / Danger (80%) / Over (100%) with color coding
- **`GET/POST /api/budget`** — budget CRUD with status tracking

#### Comparison Reports (v0.7.2)
- **Weekly report** — this week vs last week across all metrics
- **Monthly report** — this month vs last month
- **Delta percentages** — ↑↓ arrows with color-coded change indicators
- **Highlights** — top model, cache rate, avg daily cost, most active day
- **`/api/report?type=weekly|monthly`** — comparison report data

### 🎨 UI
- Insights card with severity icons (high/medium/low) and savings badges
- Budget progress bars with gradient fills and pulse animation on over-budget
- Report section on Analytics page with weekly/monthly toggle
- Report grid with delta arrows and highlight cards

### 🌐 i18n
- Full Chinese translations for all v0.7.x features
- Severity labels: 高/中/低, Budget labels: 每日/每周/每月
- Report labels: 本期/上期/变化, Highlights: 最活跃模型/日均成本

### 🚀 新功能

#### 智能成本优化 (v0.7.0)
- **优化建议** — 概览页显示基于规则的成本优化建议
- **模型降级建议** — 检测简单任务中的 Opus 使用，建议切换到 Sonnet
- **缓存优化** — 检测低缓存命中率，给出节省估算
- **成本异常检测** — 标记消费异常的日期
- **高峰时段提醒** — 提示使用集中风险

#### Token 预算管理 (v0.7.1)
- **预算配置** — 在设置页设定每日/每周/每月成本上限
- **预算进度条** — 概览页实时显示花费 vs 预算
- **预警阈值** — OK / 警告(60%) / 危险(80%) / 超标(100%)

#### 对比报告 (v0.7.2)
- **周报** — 本周 vs 上周全维度对比
- **月报** — 本月 vs 上月对比
- **变化百分比** — ↑↓ 箭头彩色标注
- **亮点** — 最活跃模型、缓存命中率、日均成本、最活跃日

---

## [0.6.0] — 2026-03-27

### 🚀 New Features

#### MCP Server Analytics (v0.6.0)
- **MCP server grouping** — `mcp__playwright__*` tools auto-grouped under "playwright" server
- **MCP donut chart** — per-server call distribution with session count
- **MCP trend chart** — daily Built-in vs MCP tool usage area chart
- **`/api/mcp-stats`** — MCP server-level aggregated statistics (calls, sessions, top tools)
- **`/api/mcp-trend`** — daily MCP usage trend data

#### Rate Limit Predictor (v0.6.1)
- **Risk level indicator** — 🟢 Safe → 🟡 Caution → 🟠 Warning → 🔴 Danger → ⚫ Critical
- **Time-to-throttle countdown** — predicts when 5h quota will be exhausted
- **Safe RPM suggestion** — recommended request rate to avoid throttling
- **Multi-window burn rates** — 5m / 15m / 30m / 60m sliding windows
- **`/api/rate-prediction`** — prediction data with risk level and safe RPM

#### Prompt Efficiency Analysis (v0.6.2)
- **Output ratio** — output_tokens / total_tokens percentage
- **Cache efficiency grade** — Excellent / Good / Fair / Poor with color coding
- **Interaction mode classification** — Exploration / Building / Debugging / Review
- **Mode distribution bar** — stacked bar showing session mode breakdown
- **Efficiency trend** — daily output ratio & cache rate line chart
- **`/api/efficiency`** — efficiency metrics, mode classification, trend data

### 🎨 UI
- Rate Limit Predictor card on Overview page (auto-hidden when no quota data)
- MCP Servers donut + MCP Trend area chart on Analytics page
- Efficiency panel with mode bar + trend chart on Analytics page
- New CSS: risk badges with pulse animation, efficiency grid, mode legend

### 🚀 新功能

#### MCP 工具分析 (v0.6.0)
- **MCP 服务器分组** — `mcp__playwright__*` 等工具自动归类到对应服务器
- **MCP 分布饼图** — 按服务器显示调用分布和会话数
- **MCP 趋势图** — 内置工具 vs MCP 工具每日使用趋势
- **`/api/mcp-stats`** + **`/api/mcp-trend`** — MCP 统计和趋势端点

#### 限速预测器 (v0.6.1)
- **风险等级指示器** — Safe / Caution / Warning / Danger / Critical 五档
- **限速倒计时** — 预测 5h 额度耗尽时间
- **安全 RPM 建议** — 推荐请求速率以避免限速
- **多窗口消耗率** — 5m / 15m / 30m / 60m 滑动窗口
- **`/api/rate-prediction`** — 预测数据端点

#### Prompt 效率分析 (v0.6.2)
- **输出比率** — output_tokens 占总 token 的百分比
- **缓存效率评级** — Excellent / Good / Fair / Poor
- **交互模式分类** — 探索 / 构建 / 调试 / 审查 四种模式
- **效率趋势** — 每日输出比率和缓存命中率变化

---

## [0.5.1] — 2026-03-27

### 🚀 New Features
- **Today's Model Cost Breakdown** — new overview card showing per-model calls, tokens, and cost for today with donut chart and legend list (same style as Tool Distribution)
- **`/api/today-breakdown`** — new endpoint returning today's usage grouped by model with cost calculation

### 🎨 UI
- Donut chart with `ring-c` layout (chart + legend list with colored dots and glow)
- Left-right split: table (Model/Calls/In/Out/Cache/Cost) + donut chart
- Responsive: stacks vertically on mobile

### 🐛 Fixes
- **Distinct model colors** — each model now has a unique high-contrast color (Opus=orange, Sonnet=blue, Haiku=green, GPT=yellow/pink/teal) instead of similar shades

### 🚀 新功能
- **今日模型消耗明细** — 概览页新增卡片，按模型显示今日调用次数、Token 和成本，配有甜甜圈图和图例
- **`/api/today-breakdown`** — 新端点，返回按模型分组的今日用量和成本

### 🐛 修复
- **模型颜色区分** — 每个模型独立高对比度颜色（Opus=橙、Sonnet=蓝、Haiku=绿、GPT=黄/粉/青），不再混淆

---

## [0.5.0] — 2026-03-27

### 🚀 New Features

#### claude.ai Web & Desktop Conversations
- **Web conversations browser** — fetch and display all claude.ai web conversations via Swift helper script
- **Desktop session separation** — sessions from Claude Desktop App split from CLI sessions, shown in "Web & Desktop" section
- **Conversation detail modal** — view full chat timeline with scroll-to-top/bottom buttons
- **Entrypoint tracking** — every session tagged with origin: `cli`, `claude-desktop`, `sdk-ts`, `sdk-cli`, `local-agent`
- **Smart session routing** — same project's sessions auto-split: CLI → "Recent Sessions", Desktop/SDK → "Web & Desktop"

### 🚀 新功能

#### claude.ai 网页版 & 桌面客户端对话
- **Web 对话浏览器** — 通过 Swift 脚本获取 claude.ai 所有网页对话
- **桌面客户端会话分离** — Desktop App 会话与 CLI 会话分开展示
- **对话详情弹窗** — 查看完整聊天时间轴，带滚动按钮
- **来源追踪** — 每个会话标记来源：`cli`、`claude-desktop`、`sdk-ts`、`sdk-cli`、`local-agent`
- **智能会话路由** — 同项目会话自动分流：CLI 在"最近会话"，桌面/SDK 在"Web & 客户端"

### 🔧 Backend
- `fetch-web-conversations.swift` — claude.ai chat API helper
- `/api/web-conversations`, `/api/web-conversation-detail` endpoints
- `entrypoint` field on sessions, live calls, and log entries
- `session_entrypoints` tracking in scanner

### 🐛 Fixes / 修复
- Fixed `codex_model_names` undefined error in `api_models`
- Fixed `import copy` missing at module level

---

## [0.4.2] — 2026-03-27

### 🐛 Critical Fixes
- **Cache pollution fix** — `copy.deepcopy` on all scan results before Codex merge, prevents source switching from corrupting cached data
- **Gauge display fix** — removed faulty session key check that hid gauges even when Claude Code was detected
- **Source filtering for all metrics** — RPM, TPM, burn rate, avg duration, avg TTFT, today messages all now filter by active source
- **Daily tokens source filtering** — trend chart tokens filtered by model source
- **Remote timeout increased** — 5s → 15s to prevent remote data loss on slow connections
- **Agent cache stability** — remote agent always scans all data, filters on return (no cache pollution)
- **Consistent scan architecture** — all API handlers use "scan all + deep copy + filter" pattern

### 🐛 关键修复
- **缓存污染修复** — 在 Codex 合并前对所有扫描结果使用 `copy.deepcopy`，防止数据源切换时破坏缓存数据
- **仪表盘显示修复** — 移除了错误的 session key 检查逻辑，该逻辑导致即使检测到 Claude Code 也会隐藏仪表盘
- **所有指标的数据源过滤** — RPM、TPM、消耗速率、平均时长、平均 TTFT、今日消息数现在均按活跃数据源过滤
- **每日 token 数据源过滤** — 趋势图中的 token 按模型来源过滤
- **远程超时时间增加** — 5s → 15s，防止慢速连接导致远程数据丢失
- **Agent 缓存稳定性** — 远程 agent 始终扫描全部数据，在返回时过滤（避免缓存污染）
- **统一扫描架构** — 所有 API 处理器使用"扫描全部 + 深拷贝 + 过滤"模式

---

## [0.4.1] — 2026-03-26

### 🔧 Improvements
- **Remote agent source filtering** — `agent.py` supports `?source=claude|codex|all` on all endpoints
- **Fast source switching** — switching data source tabs skips remote calls entirely (uses local data only), making it instant instead of waiting 5+ seconds
- **Sessions source filtering** — session list, logs, and live stream all respect the active source tab
- **No more data pollution** — `source=claude` shows zero Codex entries, `source=codex` shows zero Claude entries, across all views (overview, charts, models, projects, sessions, live, logs)
- **Remote only on initial load** — remote aggregation only happens on `source=all` (the default), specific source views use pure local data

### 🔧 改进
- **远程 agent 数据源过滤** — `agent.py` 在所有端点支持 `?source=claude|codex|all` 参数
- **快速数据源切换** — 切换数据源标签时完全跳过远程调用（仅使用本地数据），从等待 5 秒以上变为即时响应
- **会话数据源过滤** — 会话列表、日志和实时流均遵循活跃的数据源标签
- **消除数据污染** — `source=claude` 不显示任何 Codex 条目，`source=codex` 不显示任何 Claude 条目，覆盖所有视图（概览、图表、模型、项目、会话、实时、日志）
- **仅在初始加载时使用远程数据** — 远程聚合仅在 `source=all`（默认值）时发生，特定数据源视图使用纯本地数据

---

## [0.4.0] — 2026-03-26

### 🚀 Multi-CLI Support: Codex CLI Integration

#### Codex CLI Data Adapter
- **Automatic detection** of `~/.codex/` data — no configuration needed
- **Full session scanning** — reads `~/.codex/sessions/` (date-based dirs) and `~/.codex/archived_sessions/`
- **Token extraction** from cumulative `token_count` events (input, cached_input, output, reasoning_output)
- **Tool call tracking** from `function_call` response items
- **User message extraction** from `user_message` events
- **Session metadata** — cwd, model_provider, subagent parent relationships
- **Session chain by cwd** — groups Codex sessions sharing the same working directory
- **Session detail** — full conversation timeline for Codex sessions (user/assistant/tool events)

#### Dynamic Model Pricing (LiteLLM)
- **2500+ models** priced automatically from [LiteLLM](https://github.com/BerriAI/litellm) open-source pricing data
- **24-hour cache** — fetched once per day from GitHub, zero API key needed
- **Pricing chain**: custom_pricing (user) → LiteLLM (2500 models) → MODEL_PRICING (hardcoded fallback) → DEFAULT_PRICING
- **Official OpenAI pricing** updated: gpt-5.3-codex ($1.75/$14), gpt-5.4 ($2.50/$15), gpt-5.4-mini ($0.75/$4.50), gpt-4o ($2.50/$10)

#### Data Source Switching
- **Source tabs** on overview page — `All | Claude Code | Codex CLI` (auto-hidden if only one source)
- **`?source=` parameter** on 6 API endpoints: overview, daily, models, projects, live, logs
- **Per-source filtering** — switch to Claude-only or Codex-only view, all charts/tables/stats recalculate
- **Gauge auto-hide** — 5H/7D subscription gauges hidden when viewing Codex-only data

#### Remote Agent
- **Codex scanning** added to `agent.py` — merges `~/.codex/` data on remote servers
- **Codex model pricing** added to agent's pricing table
- **Codex session chain** with cwd-based grouping

### 🚀 多 CLI 支持：Codex CLI 集成

#### Codex CLI 数据适配器
- **自动检测** `~/.codex/` 数据 — 无需任何配置
- **完整会话扫描** — 读取 `~/.codex/sessions/`（按日期分目录）和 `~/.codex/archived_sessions/`
- **Token 提取** — 从累计 `token_count` 事件中获取（input、cached_input、output、reasoning_output）
- **工具调用追踪** — 从 `function_call` 响应项中提取
- **用户消息提取** — 从 `user_message` 事件中获取
- **会话元数据** — cwd、model_provider、子 agent 父级关系
- **按 cwd 的会话链** — 将共享相同工作目录的 Codex 会话归组
- **会话详情** — Codex 会话的完整对话时间线（用户/助手/工具事件）

#### 动态模型定价 (LiteLLM)
- **2500+ 模型** 自动从 [LiteLLM](https://github.com/BerriAI/litellm) 开源定价数据获取价格
- **24 小时缓存** — 每天从 GitHub 获取一次，无需 API 密钥
- **定价链**: custom_pricing（用户自定义）→ LiteLLM（2500 模型）→ MODEL_PRICING（硬编码兜底）→ DEFAULT_PRICING
- **OpenAI 官方定价** 已更新：gpt-5.3-codex ($1.75/$14)、gpt-5.4 ($2.50/$15)、gpt-5.4-mini ($0.75/$4.50)、gpt-4o ($2.50/$10)

#### 数据源切换
- **数据源标签** 在概览页 — `All | Claude Code | Codex CLI`（仅一个数据源时自动隐藏）
- **`?source=` 参数** 支持 6 个 API 端点：overview、daily、models、projects、live、logs
- **按数据源过滤** — 切换到仅 Claude 或仅 Codex 视图，所有图表/表格/统计自动重算
- **仪表盘自动隐藏** — 查看仅 Codex 数据时隐藏 5H/7D 订阅仪表盘

#### 远程 Agent
- **Codex 扫描** 已添加到 `agent.py` — 合并远程服务器上的 `~/.codex/` 数据
- **Codex 模型定价** 已添加到 agent 的定价表
- **Codex 会话链** 支持基于 cwd 的分组

### 🎨 UI
- Source tabs with colored dots (green for Codex, accent for Claude)
- "CDX" badges on Codex entries in live stream and logs
- "CODEX" badges on Codex projects
- Provider column shows "OpenAI" for GPT/Codex models
- Data Sources section in Settings page showing detection status

### 🎨 UI
- 数据源标签带彩色圆点（Codex 为绿色，Claude 为主题色）
- 实时流和日志中的 Codex 条目显示 "CDX" 标记
- Codex 项目显示 "CODEX" 标记
- 供应商列显示 GPT/Codex 模型为 "OpenAI"
- 设置页新增数据源检测状态区域

### 🔧 Backend
- `_scan_codex()` — full Codex JSONL scanner with caching
- `_merge_codex_into_scan()` — merges Codex data into Claude scan results
- `_find_codex_session_file()` — locates rollout files by session ID
- `_parse_codex_session()` — converts Codex JSONL to unified event timeline
- `_scan_codex_today()` — today's Codex calls for live view
- `_scan_codex_logs()` — all Codex log entries with caching
- `_fetch_litellm_pricing()` — dynamic pricing with 24h cache
- `_get_model_pricing()` — unified pricing lookup chain
- `_read_codex_model()` — reads default model from `~/.codex/config.toml`
- Background pre-scan thread for Codex data on startup

### 🔧 后端
- `_scan_codex()` — 带缓存的完整 Codex JSONL 扫描器
- `_merge_codex_into_scan()` — 将 Codex 数据合并到 Claude 扫描结果中
- `_find_codex_session_file()` — 通过会话 ID 定位 rollout 文件
- `_parse_codex_session()` — 将 Codex JSONL 转换为统一事件时间线
- `_scan_codex_today()` — 获取今日 Codex 调用用于实时视图
- `_scan_codex_logs()` — 带缓存的所有 Codex 日志条目
- `_fetch_litellm_pricing()` — 带 24 小时缓存的动态定价获取
- `_get_model_pricing()` — 统一定价查询链
- `_read_codex_model()` — 从 `~/.codex/config.toml` 读取默认模型
- 启动时后台预扫描 Codex 数据的线程

---

## [0.3.1] — 2026-03-26

### 🚀 New Features

#### Settings Page
- **Frontend Settings UI** — new sidebar page with gear icon for managing all configuration
- **API Configuration panel** — edit Session Key and Org ID directly in the browser (values masked on display for security)
- **Model Pricing editor** — table-based UI to add/edit/delete custom pricing per model (input/output/cache_read/cache_write per MTok)
- **Detected Models display** — auto-detected list of all models found in usage data, with provider-colored badges

#### Custom Model Pricing
- **Mixed pricing support** — each API call uses its own model's pricing: custom_pricing → MODEL_PRICING → DEFAULT_PRICING fallback chain
- **Third-party model support** — GLM-5, MiniMax-M2.5, gpt-5.3-codex and other non-Anthropic models can now have accurate cost estimation
- **Real-time recalculation** — saving new pricing clears caches and immediately reflects in all cost displays

#### Provider Classification
- **Automatic provider detection** — models auto-classified by name pattern: Anthropic, OpenAI, ZhipuAI, MiniMax, Google, Mistral, Meta, Alibaba, DeepSeek, Other
- **Provider column** in model usage table with colored indicator dots
- **Provider badges** on detected models list

### 🚀 新功能

#### 设置页面
- **前端设置 UI** — 侧边栏新增齿轮图标页面，用于管理所有配置
- **API 配置面板** — 在浏览器中直接编辑 Session Key 和 Org ID（显示时脱敏处理）
- **模型定价编辑器** — 基于表格的 UI，可按模型添加/编辑/删除自定义定价（每 MTok 的 input/output/cache_read/cache_write）
- **已检测模型展示** — 自动检测使用数据中发现的所有模型列表，带供应商彩色标记

#### 自定义模型定价
- **混合定价支持** — 每次 API 调用使用各自模型的定价：custom_pricing → MODEL_PRICING → DEFAULT_PRICING 兜底链
- **第三方模型支持** — GLM-5、MiniMax-M2.5、gpt-5.3-codex 等非 Anthropic 模型现在可以准确估算成本
- **实时重算** — 保存新定价后清除缓存，立即反映在所有成本显示中

#### 供应商分类
- **自动供应商检测** — 模型按名称模式自动分类：Anthropic、OpenAI、ZhipuAI、MiniMax、Google、Mistral、Meta、Alibaba、DeepSeek、Other
- **供应商列** — 模型使用表中新增带彩色指示点的供应商列
- **供应商标记** — 已检测模型列表显示供应商标记

### 🔧 Backend
- `POST /api/settings` — merge updates into config.json (custom_pricing, session_key, org_id)
- `GET /api/settings` — returns config with masked sensitive fields + detected models list
- `_model_provider()` — server-side provider classification function
- `_calc_cost()` now checks `custom_pricing` from config.json before built-in pricing
- `do_POST` and `do_OPTIONS` handlers added to HTTP server

### 🔧 后端
- `POST /api/settings` — 将更新合并到 config.json（custom_pricing、session_key、org_id）
- `GET /api/settings` — 返回脱敏的配置信息 + 已检测模型列表
- `_model_provider()` — 服务端供应商分类函数
- `_calc_cost()` 现在优先检查 config.json 中的 `custom_pricing`，再使用内置定价
- HTTP 服务器新增 `do_POST` 和 `do_OPTIONS` 处理器

### 🐛 Fixes
- Non-Anthropic models no longer use incorrect Sonnet pricing by default — users can set accurate rates via Settings

### 🐛 修复
- 非 Anthropic 模型不再默认使用错误的 Sonnet 定价 — 用户可通过设置页配置准确费率

---

## [0.3.0] — 2026-03-26

### 🚀 New Features

#### Session Chain & Detail
- **Left-right split layout** for session detail modal — chain panel on the left, conversation timeline on the right, independent scrolling
- **Session chain sorting** — sort by Time / Messages / Cost / Duration, CURRENT session always pinned to top
- **Last prompt preview** in chain items — see what each session was about at a glance
- **Duration display** per session (e.g., "2h30m", "15m", "24s")
- **Chain caching** — navigating between sessions in the same project reuses cached chain data, no re-fetch
- **Smooth session switching** — clicking a chain item fades out right panel → loads → fades in, left panel stays static with CSS-only active state toggle (zero DOM rebuild)

#### Conversation Timeline
- **Consecutive assistant folding** — multiple assistant turns between user messages collapse into a summary line showing total turns/tokens/cost/tools, expandable on click
- **Tool-only compact mode** — assistant events with no text content (just tool calls) render as a single-line inline badge instead of a full card
- **Empty event filtering** — user/assistant events with no content, no tools, and no tokens are hidden
- **Prompt prefix cleaning** — strips `-\n` and leading whitespace from user prompts for clean display

#### Remote Agent
- **`last_prompt` + `duration`** fields added to remote agent's session chain response
- **Session chain endpoint** (`/api/session-chain`) added to `agent.py`

### 🚀 新功能

#### 会话链与详情
- **左右分栏布局** — 会话详情弹窗中，链面板在左、对话时间线在右，独立滚动
- **会话链排序** — 按时间 / 消息数 / 成本 / 时长排序，当前会话始终置顶
- **最后提示词预览** — 链条目中可一眼看到每个会话的主题
- **时长显示** — 每个会话显示时长（如 "2h30m"、"15m"、"24s"）
- **链缓存** — 在同一项目的会话间导航时复用已缓存的链数据，无需重新获取
- **平滑会话切换** — 点击链条目时右面板淡出 → 加载 → 淡入，左面板保持静态，使用纯 CSS 激活状态切换（零 DOM 重建）

#### 对话时间线
- **连续助手回复折叠** — 用户消息之间的多个助手回复折叠为摘要行，显示总轮数/token/成本/工具，点击可展开
- **纯工具紧凑模式** — 无文本内容的助手事件（仅工具调用）渲染为单行内联标记而非完整卡片
- **空事件过滤** — 隐藏无内容、无工具、无 token 的用户/助手事件
- **提示词前缀清理** — 清除用户提示词中的 `-\n` 和前导空白以获得干净显示

#### 远程 Agent
- **`last_prompt` + `duration`** 字段已添加到远程 agent 的会话链响应中
- **会话链端点** (`/api/session-chain`) 已添加到 `agent.py`

### 🎨 UI Improvements

#### Session Detail Modal
- **Chat-bubble styling** — user messages in blue-tinted cards, assistant in green-tinted, with inner content area having its own background/border/padding
- **Content fade mask** — long messages show a gradient fade at the bottom instead of hard cutoff
- **Tool badges** — hover turns green with accent glow
- **File list** — proper background, row separators
- **Group fold animation** — `translateY` slide-in when expanding folded assistant groups
- **Floating scroll buttons** target the correct panel (`.modal-main-panel`)
- **Close button** repositioned for split layout

#### Sidebar Navigation
- **CSS-only active toggle** for chain items — `transition: all .3s cubic-bezier(.4,0,.2,1)` on background/border/shadow, no DOM rebuild flash
- **Chain sort buttons** with active highlight

#### General
- **Spinner animation** (`@keyframes spin`) for loading indicators
- **Mobile responsive** — modal split layout collapses to vertical on screens < 700px

### 🎨 UI 改进

#### 会话详情弹窗
- **聊天气泡样式** — 用户消息为蓝色调卡片，助手为绿色调，内容区域有独立的背景/边框/内边距
- **内容渐隐遮罩** — 长消息底部显示渐变淡出效果而非硬截断
- **工具标记** — 悬停时变绿并带主题色发光效果
- **文件列表** — 合适的背景色和行分隔线
- **分组展开动画** — 展开折叠的助手分组时使用 `translateY` 滑入效果
- **浮动滚动按钮** 指向正确面板 (`.modal-main-panel`)
- **关闭按钮** 为分栏布局重新定位

#### 侧边栏导航
- **纯 CSS 激活切换** — 链条目使用 `transition: all .3s cubic-bezier(.4,0,.2,1)` 控制背景/边框/阴影，无 DOM 重建闪烁
- **链排序按钮** 带激活高亮

#### 通用
- **加载动画** (`@keyframes spin`) 用于加载指示器
- **移动端响应式** — 弹窗分栏布局在 < 700px 屏幕上折叠为竖向排列

### 🔧 Backend
- Session chain/detail requests to remote agent use **direct fetch** (no cache) with **15s timeout** — prevents stale empty results and handles large session files
- Prompt cleaning in `api_session_chain`: strips `-\n \t` prefixes from user message content
- Fixed `last_prompt` field name mismatch between session dict and chain output

### 🔧 后端
- 会话链/详情请求使用**直接获取**（无缓存）和 **15 秒超时** 连接远程 agent — 防止陈旧的空结果，处理大型会话文件
- `api_session_chain` 中的提示词清理：清除用户消息内容的 `-\n \t` 前缀
- 修复了会话字典与链输出之间 `last_prompt` 字段名不匹配的问题

### 🐛 Fixes
- **Remote chain empty** — was caused by 5s timeout on large session files, increased to 15s
- **Remote chain caching stale empty** — switched from `_fetch_remote_cached` to direct `_fetch_remote` for per-session endpoints
- **Chain sort default** — initial render now sorts by time with CURRENT pinned, Time button highlighted
- **Null timestamp sort crash** — fallback to `'0'` for null `last_ts` in comparisons
- **Scroll buttons broken** — updated target from `.modal` to `.modal-main-panel` after layout change

### 🐛 修复
- **远程链为空** — 原因是大型会话文件的 5 秒超时，已增加到 15 秒
- **远程链缓存陈旧空数据** — 对逐会话端点从 `_fetch_remote_cached` 切换为直接 `_fetch_remote`
- **链排序默认值** — 初始渲染现在按时间排序并置顶当前会话，时间按钮高亮
- **空时间戳排序崩溃** — 比较时对 null `last_ts` 使用 `'0'` 作为兜底值
- **滚动按钮失效** — 布局更改后将目标从 `.modal` 更新为 `.modal-main-panel`

---

## [0.2.0] — 2026-03-25

### 🚀 New Features

#### Analytics & Intelligence
- **Per-call cost estimation** based on [official Anthropic pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) (Opus $5/$25, Sonnet $3/$15, Haiku $1/$5 per MTok)
- **Cost column** in Live Stream, System Logs, Model Usage, and Project tables
- **Burn rate severity** classification: Extreme / High / Moderate / Low / Idle
- **Cache efficiency grading**: Excellent (≥85%) / Good (≥60%) / Fair (≥30%) / Poor
- **Usage projection**: estimated $/day based on current consumption rate
- **Tool distribution** donut chart — Read / Edit / Bash / Write / Grep / Glob / Agent
- **Coding rhythm** analysis — activity distribution by time of day (morning/afternoon/evening/night)
- **Work mode** analysis — Exploration (Read/Grep) vs Building (Write/Edit) vs Execution (Bash/Agent)
- **Model DNA** stacked bar — token distribution by model family (Opus/Sonnet/Haiku)
- **Context window usage %** per model with color-coded progress bar
- **Day over Day** comparison (today vs yesterday) with flip-card toggle to Week over Week
- **Weekly trend comparison** — messages, tokens, cost, sessions with % change arrows

#### Session Management
- **Session detail modal** — click any session to view full conversation timeline
  - User prompts & assistant responses with tool call badges
  - File operations tracking (which files were read/edited most)
  - Stats summary: messages, duration, cost, tokens, models
  - Copy Session ID / `claude --resume` command buttons
  - Floating scroll-to-top/bottom buttons
- **Session chain tracking** — view all sessions in the same project, navigate between them
- **Remote session detail & chain** — works across local and remote servers

#### Data & Export
- **Data export** — CSV / JSON download with filter support (model, project, date range)
- **24H hourly trend** view — per-hour breakdown of messages, tokens, and cost
- **Monthly aggregation** view for long-term trends
- **Daily token trend** series in the main chart

#### Privacy & UX
- **Privacy mode** — one-click blur of project names, session content, file paths (preserves metrics)
- **Claude.ai quota tracking** — 5h + 7d rolling window utilization via Swift helper (bypasses Cloudflare)

### 🚀 新功能

#### 分析与智能
- **逐次调用成本估算** — 基于 [Anthropic 官方定价](https://docs.anthropic.com/en/docs/about-claude/pricing)（Opus $5/$25、Sonnet $3/$15、Haiku $1/$5 每 MTok）
- **成本列** — 在实时流、系统日志、模型使用和项目表格中显示
- **消耗速率等级** 分类：极端 / 高 / 中等 / 低 / 空闲
- **缓存效率评级**：优秀 (≥85%) / 良好 (≥60%) / 一般 (≥30%) / 差
- **用量预测**：基于当前消耗速率估算每日美元支出
- **工具分布** 环形图 — Read / Edit / Bash / Write / Grep / Glob / Agent
- **编码节奏** 分析 — 按时段（上午/下午/晚间/深夜）的活动分布
- **工作模式** 分析 — 探索型 (Read/Grep) vs 构建型 (Write/Edit) vs 执行型 (Bash/Agent)
- **模型 DNA** 堆叠柱状图 — 按模型家族（Opus/Sonnet/Haiku）的 token 分布
- **上下文窗口使用率** — 每个模型的使用百分比，带颜色编码进度条
- **逐日对比** — 今天 vs 昨天，可翻转切换到逐周对比
- **每周趋势对比** — 消息数、token、成本、会话数及百分比变化箭头

#### 会话管理
- **会话详情弹窗** — 点击任意会话查看完整对话时间线
  - 用户提示词和助手回复，带工具调用标记
  - 文件操作追踪（哪些文件被读取/编辑最多）
  - 统计摘要：消息数、时长、成本、token、模型
  - 复制会话 ID / `claude --resume` 命令按钮
  - 浮动的滚动到顶部/底部按钮
- **会话链追踪** — 查看同一项目中的所有会话，在它们之间导航
- **远程会话详情与链** — 跨本地和远程服务器工作

#### 数据与导出
- **数据导出** — 支持过滤条件的 CSV / JSON 下载（模型、项目、日期范围）
- **24 小时逐时趋势** 视图 — 按小时的消息、token 和成本分解
- **月度汇总** 视图用于长期趋势分析
- **每日 token 趋势** 序列在主图表中显示

#### 隐私与用户体验
- **隐私模式** — 一键模糊项目名、会话内容、文件路径（保留指标数据）
- **Claude.ai 配额追踪** — 通过 Swift 辅助工具（绕过 Cloudflare）获取 5 小时 + 7 天滚动窗口使用率

### 🎨 UI Improvements
- **HUD half-arc gauges** replacing circular rings — gradient arcs (green→cyan / blue→purple), SVG glow filters, animated scanning line, tick marks
- **Sliding nav indicator** pill with smooth cubic-bezier animation
- **Page transitions** with scale + fade effect
- **Chart tab crossfade** animation (Trend/Token/Heatmap)
- **Smooth theme transition** on all surfaces (cards, sidebar, buttons, tables)
- **Card flip animation** for day/week comparison toggle
- **Micro-interactions**: button press scale, stat value hover zoom, badge bounce, pill press, live dot glow pulse
- **CCDash logo** on loading screen (with breathing animation) and sidebar
- **Session detail modal** polish: backdrop blur, slide-in animation, timeline event hover, gradient fade on long content

### 🎨 UI 改进
- **HUD 半弧仪表盘** 取代圆环 — 渐变弧线（绿→青 / 蓝→紫），SVG 发光滤镜，动态扫描线，刻度标记
- **滑动导航指示器** 胶囊体带平滑 cubic-bezier 动画
- **页面切换** 缩放 + 淡入效果
- **图表标签交叉淡入** 动画（趋势/Token/热力图）
- **平滑主题切换** 覆盖所有表面（卡片、侧边栏、按钮、表格）
- **卡片翻转动画** 用于日/周对比切换
- **微交互**：按钮按压缩放、统计值悬停放大、标记弹跳、胶囊按压、实时点发光脉冲
- **CCDash 标志** 显示在加载屏幕（带呼吸动画）和侧边栏
- **会话详情弹窗** 优化：背景模糊、滑入动画、时间线事件悬停、长内容渐变淡出

### 🔧 Backend
- New API endpoints: `/api/tools`, `/api/rhythm`, `/api/hourly-trend`, `/api/session-detail`, `/api/session-chain`, `/api/export`, `/api/claude-usage`
- `MODEL_PRICING` table with all Claude model rates (Opus 4.6/4.5, Sonnet 4.6/4.5/4, Haiku 4.5)
- Burn rate calculation from recent 30-minute window
- RPM / TPM metrics from 5-minute sliding window
- Remote agent: TTFT/duration tracking via two-pass JSONL scan, cost calculation, session detail/chain endpoints
- Null guards on all API calls to prevent cascade failures
- Cache-busting headers for development
- `_fetch_remote` timeout reduced to 5s, all init calls parallelized

### 🔧 后端
- 新增 API 端点：`/api/tools`、`/api/rhythm`、`/api/hourly-trend`、`/api/session-detail`、`/api/session-chain`、`/api/export`、`/api/claude-usage`
- `MODEL_PRICING` 表包含所有 Claude 模型费率（Opus 4.6/4.5、Sonnet 4.6/4.5/4、Haiku 4.5）
- 消耗速率基于最近 30 分钟窗口计算
- RPM / TPM 指标基于 5 分钟滑动窗口
- 远程 agent：通过两遍 JSONL 扫描追踪 TTFT/时长，成本计算，会话详情/链端点
- 所有 API 调用添加空值守卫以防止级联故障
- 开发环境缓存清除头
- `_fetch_remote` 超时缩短至 5 秒，所有初始化调用并行化

### 🐛 Fixes
- **Cost calculation corrected** — was using old Opus 4.1 pricing ($15/$75), now uses Opus 4.6 ($5/$25)
- **Cost accumulation bug** — deep copy prevents remote data from mutating cached scan results
- **Relative time i18n** — frontend `relativeTime()` used instead of backend hardcoded Chinese
- **Project labels** — `(local)` / `(cloud)` rendered in current language
- **Heatmap date filtering** — `/api/hourly` now accepts `days` parameter
- **Language switch** now re-renders all charts and data tables
- **Remote logs/sessions** merged into main dashboard views

### 🐛 修复
- **成本计算修正** — 之前使用旧的 Opus 4.1 定价 ($15/$75)，现已更新为 Opus 4.6 ($5/$25)
- **成本累加 bug** — 深拷贝防止远程数据修改已缓存的扫描结果
- **相对时间国际化** — 使用前端 `relativeTime()` 替代后端硬编码的中文
- **项目标签** — `(local)` / `(cloud)` 使用当前语言渲染
- **热力图日期过滤** — `/api/hourly` 现在接受 `days` 参数
- **语言切换** 现在会重新渲染所有图表和数据表格
- **远程日志/会话** 合并到主仪表盘视图

---

## [0.1.0] — 2026-03-24

### 🎉 Initial Release

- Left sidebar + main content SPA layout
- 4 pages: Overview, Analytics, Live Stream, System Logs
- SVG circular gauge for 5h subscription usage
- 4 stat cards with sparkline trends (Messages, Tokens, Cache, Models)
- Daily trend area chart (Messages/Sessions/Tools) with 7D/14D/30D/60D/90D range
- Token distribution stacked bar chart by model
- Activity heatmap (day × hour)
- Model usage table with cache hit rate
- Cache analysis donut chart
- Project TOP 10 by token usage
- Live API call stream with auto-refresh
- System logs with pagination, filters (date range, model, project)
- Session browser with search
- Remote server aggregation via `agent.py`
- Dark / Light theme with Phosphor icons
- Chinese / English bilingual interface
- Zero dependencies — pure Python stdlib backend

### 🎉 首次发布

- 左侧边栏 + 主内容区单页应用布局
- 4 个页面：概览、分析、实时流、系统日志
- SVG 圆形仪表盘显示 5 小时订阅使用量
- 4 个统计卡片带迷你趋势图（消息数、Token、缓存、模型）
- 每日趋势面积图（消息/会话/工具），支持 7D/14D/30D/60D/90D 范围
- 按模型的 Token 分布堆叠柱状图
- 活动热力图（日 × 小时）
- 模型使用表格含缓存命中率
- 缓存分析环形图
- 按 Token 使用量的项目 TOP 10
- 实时 API 调用流，自动刷新
- 系统日志，带分页和过滤器（日期范围、模型、项目）
- 会话浏览器，支持搜索
- 通过 `agent.py` 聚合远程服务器数据
- 深色 / 浅色主题，使用 Phosphor 图标
- 中文 / 英文双语界面
- 零依赖 — 纯 Python 标准库后端

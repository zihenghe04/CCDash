# Changelog

All notable changes to CCDash will be documented in this file.

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

---

## [0.4.1] — 2026-03-26

### 🔧 Improvements
- **Remote agent source filtering** — `agent.py` supports `?source=claude|codex|all` on all endpoints
- **Fast source switching** — switching data source tabs skips remote calls entirely (uses local data only), making it instant instead of waiting 5+ seconds
- **Sessions source filtering** — session list, logs, and live stream all respect the active source tab
- **No more data pollution** — `source=claude` shows zero Codex entries, `source=codex` shows zero Claude entries, across all views (overview, charts, models, projects, sessions, live, logs)
- **Remote only on initial load** — remote aggregation only happens on `source=all` (the default), specific source views use pure local data

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

### 🎨 UI
- Source tabs with colored dots (green for Codex, accent for Claude)
- "CDX" badges on Codex entries in live stream and logs
- "CODEX" badges on Codex projects
- Provider column shows "OpenAI" for GPT/Codex models
- Data Sources section in Settings page showing detection status

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

### 🔧 Backend
- `POST /api/settings` — merge updates into config.json (custom_pricing, session_key, org_id)
- `GET /api/settings` — returns config with masked sensitive fields + detected models list
- `_model_provider()` — server-side provider classification function
- `_calc_cost()` now checks `custom_pricing` from config.json before built-in pricing
- `do_POST` and `do_OPTIONS` handlers added to HTTP server

### 🐛 Fixes
- Non-Anthropic models no longer use incorrect Sonnet pricing by default — users can set accurate rates via Settings

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

### 🔧 Backend
- Session chain/detail requests to remote agent use **direct fetch** (no cache) with **15s timeout** — prevents stale empty results and handles large session files
- Prompt cleaning in `api_session_chain`: strips `-\n \t` prefixes from user message content
- Fixed `last_prompt` field name mismatch between session dict and chain output

### 🐛 Fixes
- **Remote chain empty** — was caused by 5s timeout on large session files, increased to 15s
- **Remote chain caching stale empty** — switched from `_fetch_remote_cached` to direct `_fetch_remote` for per-session endpoints
- **Chain sort default** — initial render now sorts by time with CURRENT pinned, Time button highlighted
- **Null timestamp sort crash** — fallback to `'0'` for null `last_ts` in comparisons
- **Scroll buttons broken** — updated target from `.modal` to `.modal-main-panel` after layout change

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

### 🔧 Backend
- New API endpoints: `/api/tools`, `/api/rhythm`, `/api/hourly-trend`, `/api/session-detail`, `/api/session-chain`, `/api/export`, `/api/claude-usage`
- `MODEL_PRICING` table with all Claude model rates (Opus 4.6/4.5, Sonnet 4.6/4.5/4, Haiku 4.5)
- Burn rate calculation from recent 30-minute window
- RPM / TPM metrics from 5-minute sliding window
- Remote agent: TTFT/duration tracking via two-pass JSONL scan, cost calculation, session detail/chain endpoints
- Null guards on all API calls to prevent cascade failures
- Cache-busting headers for development
- `_fetch_remote` timeout reduced to 5s, all init calls parallelized

### 🐛 Fixes
- **Cost calculation corrected** — was using old Opus 4.1 pricing ($15/$75), now uses Opus 4.6 ($5/$25)
- **Cost accumulation bug** — deep copy prevents remote data from mutating cached scan results
- **Relative time i18n** — frontend `relativeTime()` used instead of backend hardcoded Chinese
- **Project labels** — `(local)` / `(cloud)` rendered in current language
- **Heatmap date filtering** — `/api/hourly` now accepts `days` parameter
- **Language switch** now re-renders all charts and data tables
- **Remote logs/sessions** merged into main dashboard views

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

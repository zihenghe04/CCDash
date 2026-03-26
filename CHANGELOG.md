# Changelog

All notable changes to CCDash will be documented in this file.

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

# CCDash Roadmap

> **Last updated**: 2026-04-13 · **Current release**: [v0.9.2](https://github.com/zihenghe04/CCDash/releases/tag/v0.9.2) · **Next target**: v0.10

This document tracks what has shipped, what's next, and what's parked. See [CHANGELOG.md](CHANGELOG.md) for detailed per-release notes.

**Iteration principles**

1. **Zero dependencies first** — Python stdlib + Vanilla JS. No `pip install`, no build step.
2. **Data already there** — prefer features that can be implemented from existing JSONL data.
3. **Incremental value** — every release must be useful on its own; no "wait for the whole feature set".
4. **Privacy by default** — nothing leaves the host unless the user explicitly configures it (webhooks are the only outbound call).
5. **User-driven** — [GitHub Issues](https://github.com/zihenghe04/CCDash/issues) are the primary signal for what to build next.

---

## ✅ Shipped

### Phase 1 — Analytics Deep Dive · [v0.6.x](https://github.com/zihenghe04/CCDash/releases/tag/v0.6.0)
- **v0.6.0** MCP Server Analytics — per-server call / session grouping, trend line, Analytics page donut
- **v0.6.1** Rate Limit Predictor — 5m/15m/30m/60m sliding windows, risk level, countdown
- **v0.6.2** Prompt Efficiency — output ratio, cache grade, interaction-mode classification

### Phase 2 — Smart Insights · [v0.7.x](https://github.com/zihenghe04/CCDash/releases/tag/v0.7.0)
- **v0.7.0** Cost Optimization Engine — rule-driven suggestions (model downgrade, cache, anomaly, peak hour)
- **v0.7.1** Token Budget Management — daily/weekly/monthly limits, progress bars, threshold alerts
- **v0.7.2** Comparison Reports — this week/month vs last, delta arrows, highlights

### Phase 3 — External Integration · [v0.8.0](https://github.com/zihenghe04/CCDash/releases/tag/v0.8.0)
- **v0.8.0** Git Integration — per-commit AI cost, AI-assisted %
- **v0.8.1** Webhook Notifications — Slack / Discord / generic HTTP, quota & budget triggers
- **v0.8.2** CLI Quick Command — `ccdash-cli.py` (status/top/models/budget/live), `--server` for remote

### Phase 4 — Advanced Features · [v0.9.0](https://github.com/zihenghe04/CCDash/releases/tag/v0.9.0)
- **v0.9.0** Multi-Account + Plugin System — per-account quota, plugin discovery
- **v0.9.1** Analytics tabs + multi-select session compare, many data-consistency fixes
- **v0.9.2** Session status column (#3) + API endpoint detection (#4) + macOS launchd auto-start (server + autossh tunnel)

### Dropped / revisited
- **Session Replay** was planned for v0.9.1 — dropped after review: the JSONL data is message-level, no file-diff or terminal output, so a "replay" would just be scrolling the existing timeline with a delay. Not worth the UI complexity. Revisit if richer event data becomes available.

---

## 🎯 Next up · v0.10 — Polish & Observability

Target: **2026 Q2**. Focus: make the existing surface area more reliable, discoverable, and developer-friendly — not more features. Priorities are based on user feedback and observed pain points.

### v0.10.0 — Observability mode
**Priority: HIGH** · Complexity: MEDIUM · Data: existing

Today CCDash is mostly a "look at the dashboard" tool. Many users run it headless on a server and want machine-readable outputs.

- `GET /metrics` Prometheus exposition endpoint — RPM / TPM / cost / quota / session counts, labelled by source/project/model
- `GET /api/healthz` and `/api/readyz` for container orchestration
- Structured access logs (JSONL) with opt-in to `/tmp/ccdash-access.jsonl` for Grafana/Loki pipelines
- Optional `CCDASH_LOG_LEVEL` env var (INFO/DEBUG/QUIET)

### v0.10.1 — First-run onboarding
**Priority: HIGH** · Complexity: LOW

Currently a new user sees "Session Key not configured" warnings, blank budget cards, and no plugins — all with no guidance. A dedicated onboarding flow will walk them through the useful optional setup.

- Landing modal on first run: detects missing session key / budget / webhook / remote, shows a checklist
- Inline "Set up" buttons that link to the correct Settings section
- "Skip for now" is always available; nothing is forced

### v0.10.2 — Data source filters v2
**Priority: MEDIUM** · Complexity: MEDIUM

Today source switching is all-or-nothing (all / claude / codex). Power users want more control.

- Multi-source selection (e.g. "Claude + Codex but not the cloud remote")
- Per-project toggle to exclude noisy / test projects from analytics
- Saved filter presets

### v0.10.3 — Performance for large histories
**Priority: MEDIUM** · Complexity: MEDIUM

At 1000+ session files the full scan takes 5–10 s. Not a problem yet, but it will be.

- Incremental scan — only re-parse JSONL files whose mtime changed
- Per-session result caching, invalidated on file touch
- Lazy loading for the session list (load 40 rows, fetch more on scroll)

---

## 🧪 v0.11 — Deeper session intelligence

Target: **2026 Q3**. Focus: squeeze more insight out of the data we already have.

### v0.11.0 — File operation heat tracking
**Priority: MEDIUM** · Complexity: MEDIUM · Data: already in JSONL

`tool_use` events already contain the file paths Claude touched. Expose them as a first-class view.

- "File heat" page: which files are read / edited / written most per project
- File ↔ session cross-linking (click a file → see the sessions that touched it)
- "Hottest files this week" widget on Overview

### v0.11.1 — Context compression tracking
**Priority: LOW** · Complexity: MEDIUM · Data: already in JSONL

Claude Code emits `system/compact` events when context is compressed. Surface them.

- Per-session context usage timeline (with compact events marked)
- Average compression ratio
- Warning when a project's compact-to-message ratio is unusually high

### v0.11.2 — Sankey token flow
**Priority: LOW** · Complexity: MEDIUM

Show where tokens actually go: **Project → Model → Tool** as a Sankey diagram. Eye-candy that also doubles as a debugging tool for "why is this project so expensive?"

---

## 🌐 v0.12 — Ecosystem adapters

Target: **2026 Q3/Q4**. Focus: open the tent — support more AI coding CLIs via the plugin system.

- **OpenCode** adapter (#v0.12.0)
- **Continue.dev** adapter
- **Aider** adapter
- **Cursor / Windsurf** (where local data is available)
- Plugin SDK docs + a "starter plugin" template repo

---

## 🚀 v1.0 — Stable Release

Target: **2026 Q4**. "Stable" means a user can rely on the feature set, the API shape, and the install story.

### Must have for v1.0
- **API stability guarantees** — documented `/api/*` contract, semver for breaking changes
- **Docker image** — `ghcr.io/zihenghe04/ccdash:1.0.0` with volume mount for `~/.claude`
- **Homebrew formula** — `brew install ccdash`
- **pipx installer** — `pipx install ccdash`
- **Full user guide** — installation, configuration, remote setup, CLI, plugin development
- **Windows support confirmed on more than just "it compiles"** — E2E tested on Win10/11
- **Automated tests** — minimum smoke tests for scanner, cost calc, source filtering, API endpoints
- **Performance target** — handle 5000 session files / 10 M messages without UI lag

### Stretch for v1.0
- PWA manifest (home-screen install on mobile)
- Accessibility pass (keyboard navigation, screen reader labels)
- i18n expansion beyond EN / ZH

---

## 🪣 Parking lot (considered but not scheduled)

Ideas that are *maybe* interesting but don't have a clear user need yet. Vote with 👍 on the corresponding GitHub issue to bump priority.

- **Grafana/Prometheus dashboards** — templates for users who already have a monitoring stack (partially subsumed by v0.10.0)
- **VS Code / JetBrains sidebar plugin** — show quota/cost right in the IDE
- **Team dashboard** — multi-user aggregation, requires a central store, authn/authz — **big scope, unclear demand**
- **AI-powered insights** — use Claude itself to summarize usage patterns. Rejected for v0.7, might revisit if free-tier API gets generous
- **Model benchmark tracking** — response quality metrics over time
- **Session tagging** — let users manually label sessions for filtering
- **Browser extension** — inline stats on claude.ai itself
- **Mobile-optimized view** — `/mobile` route with tiny payload
- **iOS/Android native app** — via a hosted CCDash API (would require central server)
- **Cost-estimate-before-run** — Claude Code hook that warns "this prompt will cost ~$X"

---

## 🙋 How to influence the roadmap

1. **Open an issue** describing your use case — not "please add X" but "I need to answer Y, how would that look?"
2. **👍 react** on existing issues — highest-voted issues jump the queue
3. **Send PRs** — even a one-line fix is welcome and usually ships same day
4. **Talk to me** — [@zihenghe04 on GitHub](https://github.com/zihenghe04)

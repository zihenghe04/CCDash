<div align="center">
  <img src="logo.png" width="140" height="140" alt="CCDash Logo" style="border-radius: 24px;">
  <h1>✨ CCDash</h1>
  <p><strong>See every token. Every session. Every dollar.</strong></p>
  <p><em>A real-time analytics dashboard for Claude Code — no API key, no signup, no build step.</em></p>

  <p>
    <img src="https://img.shields.io/badge/python-3.8+-blue?style=flat-square&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
    <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/zero-dependencies-orange?style=flat-square" alt="Zero Deps">
    <img src="https://img.shields.io/github/v/release/zihenghe04/CCDash?style=flat-square&color=blueviolet" alt="Latest Release">
  </p>

  <p>
    <a href="https://zihenghe04.github.io/CCDash/"><strong>🌐 Live Demo</strong></a> &bull;
    <a href="#-whats-new">What's New</a> &bull;
    <a href="#-why-ccdash">Why?</a> &bull;
    <a href="#-features">Features</a> &bull;
    <a href="#%EF%B8%8F-screenshots">Screenshots</a> &bull;
    <a href="#-quick-start">Quick Start</a> &bull;
    <a href="#-remote-monitoring">Remote</a> &bull;
    <a href="#%E4%B8%AD%E6%96%87%E6%96%87%E6%A1%A3">中文</a>
  </p>
</div>

---

## 🆕 What's New

### v0.9.2 · 2026-04-13

- 🟢 **Session status column** ([#3](https://github.com/zihenghe04/CCDash/issues/3)) — every session in the list now shows a live status badge: **Working** (pulsing, active within 1 min), **Idle** (within 10 min), or **Done**. Works for local **and** remote sessions.
- 🔌 **API endpoint detection** ([#4](https://github.com/zihenghe04/CCDash/issues/4)) — Settings now auto-detects whether Claude Code is pointed at the official API or a proxy / relay, with masked credentials (reads env vars, `~/.claude/settings.json`, `~/.claude.json`).
- 🍏 **macOS launchd auto-start** — one-command install (`./launchd/install.sh server`) for auto-start at login + auto-restart on crash. Optional `autossh` SSH-tunnel launcher for remote agents. Templates only, no hardcoded paths.
- 🪟 **Windows compatibility** (via [#6](https://github.com/zihenghe04/CCDash/pull/6)) — UTF-8 stdio wrapping, history file encoding fix, theme toggle re-renders dynamic components.

See the full [CHANGELOG](CHANGELOG.md) for earlier releases.

---

## 🤔 Why CCDash?

You're paying for a Claude subscription. But do you actually know:

- 💸 **How much would your usage cost** at API rates? (Spoiler: probably a lot more than $20/mo)
- 📊 **Which model eats the most tokens?** Opus? Sonnet? How much cache hit are you getting?
- ⏱️ **What's your average response time?** Is it getting slower?
- 🔥 **Are you about to hit the rate limit?** How much of your 5h/7d quota is used?
- 🪝 **Which session is running right now?** Which ones idle? Which are finished?

**No existing tool answers these for Claude Code CLI subscribers.** CCDash does — with zero API keys, zero build step, and just Python stdlib.

### How is this different?

| | CCDash | Claude.ai Settings | NewAPI / One API | Karma | Dragon-UI |
|---|:---:|:---:|:---:|:---:|:---:|
| Works with **subscriptions** (no API key) | ✅ | ✅ | ❌ | ✅ | ✅ |
| Per-call **cost estimation** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **RPM / TPM / burn rate** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **TTFT** & duration tracking | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Cache efficiency** grading | ✅ | ❌ | ❌ | ✅ | ✅ |
| **Session detail** timeline | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Session chain** tracking | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Tool / work mode** analytics | ✅ | ❌ | ❌ | ✅ | ✅ |
| **Coding rhythm** analysis | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Multi-server** aggregation | ✅ | ❌ | ✅ | ❌ | SSH |
| **5h + 7d quota** tracking | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Privacy mode** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Data export** (CSV/JSON) | ✅ | ❌ | ✅ | ❌ | ✅ |
| Day/week **comparison** | ✅ | ❌ | ❌ | ❌ | ✅ |
| Daily trend & heatmap | ✅ | ❌ | ✅ | ✅ | ✅ |
| **MCP server** analytics | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Rate limit predictor** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Cost optimization** insights | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Token budget** management | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Git integration** (AI cost/commit) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Webhook** alerts | ✅ | ❌ | ❌ | ❌ | ❌ |
| **CLI tool** (`ccdash-cli.py`) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Self-hosted / zero deps | ✅ | — | ❌ | ❌ | ❌ |

> **Note**: CCDash is a community project, not affiliated with Anthropic.

---

## 🚀 Features

Grouped by what you actually want to do:

### 👁 See what's happening right now

| | |
|---|---|
| 📈 **Real-time Overview** | HUD gauges for 5h & 7d quota · RPM / TPM / burn-rate severity · $/day projection · avg TTFT & duration · day/week comparison with flip-card toggle |
| 🟢 **Live session status** ·`v0.9.2` | Every session in the list shows **Working** / **Idle** / **Done** with a pulsing badge — works for local and remote sessions |
| 📡 **Live Stream** | Real-time API call feed · colored token indicators (↓input ↑output ⟲cache) · per-call cost · pause control |
| 🔌 **API endpoint detection** ·`v0.9.2` | Auto-detects whether Claude Code is on the official API or a **proxy / relay**, with masked credentials |

### 💰 Understand your cost

| | |
|---|---|
| 💰 **Cost Intelligence** | Per-call cost at [official pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) · daily trend · per-model & per-project breakdown · cache efficiency grading |
| 💡 **Smart Insights** | Model downgrade suggestions (Opus → Sonnet savings estimates), cache optimization, cost anomaly detection, peak-hour warning |
| 💰 **Token Budget** | Daily / weekly / monthly limits · progress bars on Overview · thresholds at 60% / 80% / 100% with pulse animation on overrun |
| 📊 **Comparison Reports** | Weekly & monthly reports · delta percentages with ↑↓ arrows · highlights (top model, cache rate, avg daily cost, most active day) |
| ⚡ **Rate Limit Predictor** | Risk level (Safe → Critical) · time-to-throttle countdown · multi-window burn rates (5m/15m/30m/60m) |

### 🔍 Dig into your sessions

| | |
|---|---|
| 📋 **Session detail** | Click any session → full conversation timeline · user/assistant messages with tool call badges · file operations · session chain (all sessions in the same project) · copy Session ID / `claude --resume` command · privacy mode |
| 🔀 **Multi-select compare** | Check multiple sessions → aggregated stats + model / tool breakdown |
| 🔗 **Git integration** | Per-commit AI cost · AI-assisted commit percentage · avg cost per commit · commit table |
| 🔍 **Deep analytics** | Model DNA stacked bar · tool distribution donut · **MCP server analytics** · coding rhythm · work mode · **prompt efficiency** (output ratio, cache grade, interaction mode) · activity heatmap · context window usage % |

### 🌐 Go beyond one machine

| | |
|---|---|
| 🌐 **Multi-Server aggregation** | Lightweight `agent.py` on any remote host · aggregate into one dashboard · remote session detail, chain, and **live status** · SSH tunnel friendly |
| 👥 **Multi-Account** | Configure multiple Claude accounts (personal / work) · per-account 5h / 7d quota tracking · Settings page real-time display |
| 🍏 **macOS launchd auto-start** ·`v0.9.2` | One-command install: `./launchd/install.sh server [tunnel]` · auto-restart on crash · autossh-backed SSH tunnel for remote agents · templates only, no hardcoded paths |
| 🔔 **Webhook alerts** | Slack / Discord / HTTP · background monitoring for quota > 80% and budget overruns · connectivity test · Slack/Discord format auto-detection |

### ⌨️ Work from the terminal

| | |
|---|---|
| ⌨️ **`ccdash-cli.py`** | Five commands — `status` · `top` · `models` · `budget` · `live` · colored output · `--server URL` for remote connections · zero dependencies |
| 📤 **Data export** | CSV or JSON export — respects active source and filters |

### 🎨 A UI that doesn't suck

Dark / Light theme with smooth transitions · Phosphor icons · HUD gauges with gradient glow · sliding nav indicator · page transitions · card flip animations · bilingual (EN / ZH) · Analytics **Core / Advanced** tabs to tame long pages · collapsible sections throughout

---





## 🎬 Demo
https://github.com/user-attachments/assets/4373ee6a-a8d2-4bba-beba-e730ca015b94


## 🖼️ Screenshots

<table>
  <tr>
    <td align="center"><strong>🌙 Overview — Dark</strong></td>
    <td align="center"><strong>☀️ Overview — Light</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/overview-dark.png" alt="Overview Dark" width="100%"></td>
    <td><img src="screenshot/overview-light.png" alt="Overview Light" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>📊 Analytics</strong></td>
    <td align="center"><strong>📡 Live Stream</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/analytics.png" alt="Analytics" width="100%"></td>
    <td><img src="screenshot/live.png" alt="Live Stream" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>📋 System Logs</strong></td>
    <td align="center"><strong>🔍 Session Detail</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/logs.png" alt="Logs" width="100%"></td>
    <td><img src="screenshot/logs2.png" alt="Session Detail" width="100%"></td>
  </tr>
</table>

---

## ⚡ Quick Start

### Prerequisites

- 🐍 Python 3.8+
- 🤖 Claude Code CLI installed and used (data lives in `~/.claude/`)

### 3 commands to go

```bash
git clone https://github.com/zihenghe04/CCDash.git
cd CCDash
python3 server.py
```

Open 👉 **http://localhost:8420**

That's it. No `pip install`, no `npm`, no Docker. Just Python.

---

## ⚙️ Configuration

Copy the template and edit:

```bash
cp config.example.json config.json
```

```json
{
  "remotes": [],
  "claude_session_key": "",
  "claude_org_id": "",
  "budget": { "daily": 20, "weekly": 100, "monthly": 400 },
  "webhooks": []
}
```

| Field | Required | Description |
|:------|:--------:|:------------|
| `remotes` | ❌ | Remote agent endpoints for multi-server monitoring |
| `claude_session_key` | ❌ | Enables 5h/7d subscription quota tracking |
| `claude_org_id` | ❌ | Your claude.ai organization ID |
| `budget` | ❌ | Daily / weekly / monthly cost limits in USD |
| `webhooks` | ❌ | Webhook endpoints for alerts (Slack / Discord / HTTP) |
| `accounts` | ❌ | Multi-account config (array of `{name, session_key, org_id}`) |

### 🔑 Getting Session Key (Optional)

To unlock real-time quota gauges:

1. Log in to [claude.ai](https://claude.ai)
2. Open DevTools (`F12`) → **Application** → **Cookies** → `claude.ai`
3. Copy the `sessionKey` value
4. Find your org ID in any API request URL: `organizations/{org_id}/...`

> 💡 The session key lasts weeks. CCDash will show a warning when it expires.

---

## 🌐 Remote Monitoring

Monitor multiple machines from one dashboard. `agent.py` is a lightweight, read-only companion that exposes the same JSONL scanning as `server.py` over HTTP:

```bash
# 📡 On remote server (same repo cloned):
python3 agent.py --port 8421 --token my_secret

# 🔒 On local machine: SSH tunnel
ssh -L 8421:127.0.0.1:8421 user@server -N -f
```

Add to your local `config.json`:

```json
{
  "remotes": [
    {
      "name": "GPU Server",
      "url": "http://127.0.0.1:8421",
      "token": "my_secret",
      "enabled": true
    }
  ]
}
```

Projects from remote servers are tagged with `CLOUD` badges in the dashboard, **including live session status** — a session currently running on the remote shows as **Working** in your local panel within seconds of activity.

> 🍏 macOS users: `./launchd/install.sh server tunnel` below sets up the SSH tunnel with `autossh` auto-reconnect and auto-start at login. No manual `ssh -L` needed.

---

## 🍏 macOS Auto-Start (launchd)

Run CCDash in the background with auto-restart on crash and auto-start at login — no more "did I remember to start it?".

```bash
# Install server auto-start
./launchd/install.sh server

# Install server + SSH tunnel (prompts for remote host/port)
./launchd/install.sh server tunnel

# Uninstall
./launchd/install.sh uninstall
```

What it does:

- `launchd/install.sh server` — generates `~/Library/LaunchAgents/com.ccdash.server.plist` from the template, writes your repo path and `python3`, and loads it. Server starts at login and respawns within 5 seconds if it crashes.
- `launchd/install.sh tunnel` — installs an `autossh` tunnel (`brew install autossh` required) that keeps `127.0.0.1:<local>` forwarded to `remote:<port>`, auto-reconnecting on dropouts. Interactively asks for user/host/port — nothing is hardcoded.

Logs go to `/tmp/ccdash.log` and `/tmp/ccdash-tunnel.log`. The plist templates are in `launchd/*.template` with placeholder variables only — no private info ever hits the repo.

Manual control:

```bash
launchctl list | grep ccdash                              # status
launchctl kickstart -k gui/$(id -u)/com.ccdash.server     # restart server
tail -f /tmp/ccdash.log                                   # tail logs
```

---

## ⌨️ CLI Tool

Check usage without leaving the terminal:

```bash
python3 ccdash-cli.py status        # Today's overview + quota gauge
python3 ccdash-cli.py top           # Project TOP 5
python3 ccdash-cli.py models        # Model cost breakdown
python3 ccdash-cli.py budget        # Budget progress bars
python3 ccdash-cli.py live          # Recent API calls
```

Connect to a remote CCDash instance:

```bash
python3 ccdash-cli.py --server http://myserver:8420 status
```

> Requires a running `server.py`. Zero dependencies — just Python stdlib.

---

## 🔔 Webhook Notifications

Get alerts when quota is running low or budget is exceeded.

### Setup in Dashboard

1. Go to **Settings** → **Webhook Notifications**
2. Paste your webhook URL (Slack / Discord / any HTTP endpoint)
3. Select format and click **Save**
4. Click **Test** to verify

### Supported Formats

| Platform | URL Pattern | Auto-detected |
|:---------|:-----------|:-------------:|
| Slack | `https://hooks.slack.com/services/...` | ✅ |
| Discord | `https://discord.com/api/webhooks/...` | ✅ |
| Generic | Any HTTPS endpoint | — |

### Or configure in `config.json`

```json
{
  "webhooks": [
    {
      "url": "https://hooks.slack.com/services/T.../B.../xxx",
      "format": "slack",
      "enabled": true,
      "events": ["all"]
    }
  ]
}
```

### Trigger Events

| Event | Condition |
|:------|:---------|
| `quota_warning` | 5h quota usage > 80% |
| `budget_exceeded` | Daily cost exceeds budget limit |

> Background check runs every 5 minutes when webhooks are configured.

---

## 🏗️ Architecture

```
~/.claude/projects/  ←── Claude Code writes JSONL session files here
        │
        ▼
   ┌─────────┐     ┌───────────┐
   │ server.py│────▶│  web UI   │  ← http://localhost:8420
   └────┬────┘     └───────────┘
        │
        ├── Scans JSONL files for token usage & session data
        ├── Calculates cost per call using official pricing
        ├── (Optional) Calls claude.ai API for quota data
        └── (Optional) Aggregates remote agent.py data
```

### Tech Stack

| Layer | Technology | Why |
|:------|:-----------|:----|
| Backend | Python stdlib | Zero install, runs everywhere |
| Frontend | Vanilla JS | No build step, instant load |
| Charts | [ApexCharts](https://apexcharts.com/) | Beautiful, interactive |
| Icons | [Phosphor](https://phosphoricons.com/) | Clean, consistent |
| Quota | Swift (macOS) | Bypasses Cloudflare for claude.ai API |

---

## 📁 Project Structure

```
CCDash/
├── 🐍 server.py            # Dashboard backend (Python stdlib)
├── 📡 agent.py             # Remote monitoring agent
├── ⌨️ ccdash-cli.py        # CLI quick-check tool
├── 🍎 fetch-usage.swift    # macOS quota fetcher
├── 🔧 config.example.json  # Config template
├── 🚀 start.sh             # One-click launcher
├── 🌐 web/
│   ├── index.html          # SPA shell
│   ├── style.css           # Dark slate + emerald theme
│   └── app.js              # All frontend logic
├── 📊 docs/                # GitHub Pages demo site
├── 🗺️ ROADMAP.md           # Iteration roadmap
├── 🖼️ screenshot/
├── 📄 LICENSE              # MIT
└── 📖 README.md
```

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

## 🤝 Contributing

Contributions welcome! Feel free to open issues or PRs.

## 📄 License

[MIT](LICENSE) — Use it however you want.

---

<div align="center">

# 中文文档

</div>

## ✨ CCDash 是什么？

**每个 Token 去哪了。每个会话干了什么。每一分钱花在哪。**

CCDash 是一个**自托管的实时分析面板**，用于监控 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 的使用情况。直接读取本地 JSONL 文件——**无需 API Key**、无需构建步骤、无需 Docker，只要 Python。

> 📌 社区项目，与 Anthropic 无关联。

### 🆕 v0.9.2 最新更新

- 🟢 **会话状态列** ([#3](https://github.com/zihenghe04/CCDash/issues/3)) — 会话列表每行显示实时状态徽章：**工作中**（1 分钟内活跃，脉冲效果）/ **等待中**（10 分钟内）/ **已结束**。本地和**远程会话**都支持。
- 🔌 **API 端点自动检测** ([#4](https://github.com/zihenghe04/CCDash/issues/4)) — 设置页自动检测 Claude Code 连的是**官方 API** 还是**中转站/代理**，凭据自动掩码（读环境变量 → `~/.claude/settings.json` → `~/.claude.json`）。
- 🍏 **macOS launchd 开机自启** — 一条命令安装：`./launchd/install.sh server [tunnel]`。崩溃自动重启，可选 autossh 隧道自启。模板无任何硬编码路径/IP。
- 🪟 **Windows 兼容性修复**（合并 [#6](https://github.com/zihenghe04/CCDash/pull/6)）— UTF-8 stdio 包装、history.jsonl 编码修复、主题切换动态组件重渲染。

### 为什么需要 CCDash？

你在用 Claude 订阅，但你知道吗：

- 💸 你的使用量如果按 API 计费要花多少钱？
- 📊 哪个模型消耗了最多的 Token？缓存命中率如何？
- ⏱️ 平均响应时间是多少？是否在变慢？
- 🔥 离限速还有多远？5 小时 / 7 天额度用了多少？
- 🟢 **当前哪些会话还在跑？哪些已空闲？哪些结束了？**

**目前没有任何工具为 Claude Code 订阅用户提供这些数据。** CCDash 填补了这个空白。

---

## 🖼️ 界面预览

<table>
  <tr>
    <td align="center"><strong>🌙 概览 · 暗色</strong></td>
    <td align="center"><strong>☀️ 概览 · 亮色</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/overview-dark.png" width="100%"></td>
    <td><img src="screenshot/overview-light.png" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>📊 深度分析</strong></td>
    <td align="center"><strong>📡 实时监控</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/analytics.png" width="100%"></td>
    <td><img src="screenshot/live.png" width="100%"></td>
  </tr>
  <tr>
    <td align="center"><strong>📋 日志</strong></td>
    <td align="center"><strong>🔍 会话详情</strong></td>
  </tr>
  <tr>
    <td><img src="screenshot/logs.png" width="100%"></td>
    <td><img src="screenshot/logs2.png" width="100%"></td>
  </tr>
</table>

---

## 🚀 快速开始

```bash
git clone https://github.com/zihenghe04/CCDash.git
cd CCDash
python3 server.py
```

打开 👉 **http://localhost:8420**

无需 `pip install`，无需 `npm`，无需 Docker。只要有 Python 就行。

---

## ⚙️ 配置说明

```bash
cp config.example.json config.json
```

| 字段 | 必填 | 说明 |
|:-----|:----:|:-----|
| `remotes` | ❌ | 远程 Agent 端点，用于多服务器聚合 |
| `claude_session_key` | ❌ | claude.ai Session Key，启用额度追踪 |
| `claude_org_id` | ❌ | claude.ai 组织 ID |
| `budget` | ❌ | 每日/每周/每月成本上限（USD） |
| `webhooks` | ❌ | Webhook 告警端点（Slack/Discord/HTTP） |
| `accounts` | ❌ | 多账户配置（name/session_key/org_id 数组） |

### 🔑 获取 Session Key（可选）

1. 登录 [claude.ai](https://claude.ai)
2. 按 `F12` 打开开发者工具 → **Application** → **Cookies**
3. 复制 `sessionKey` 值
4. 在网络请求中找到 `organizations/{org_id}/` 中的组织 ID

> 💡 Session Key 一般能持续数周。过期后面板会显示警告。

---

## 🌐 远程监控

在远程服务器部署 Agent，一个面板查看所有机器：

```bash
# 📡 远程服务器
python3 agent.py --port 8421 --token your_secret

# 🔒 本地 SSH 隧道
ssh -L 8421:127.0.0.1:8421 user@server -N -f
```

在 `config.json` 中添加：

```json
{
  "remotes": [{
    "name": "云服务器",
    "url": "http://127.0.0.1:8421",
    "token": "your_secret",
    "enabled": true
  }]
}
```

远程项目在面板中会显示 `CLOUD` 标签，**包括实时会话状态** —— 远程正在跑的会话几秒内就会在本地面板上变成**工作中**。

> 🍏 macOS 用户：下面 `./launchd/install.sh server tunnel` 一条命令把 SSH 隧道也交给 autossh 自动重连 + 开机自启，不用手动 `ssh -L`。

---

## 🍏 macOS 开机自启（launchd）

后台运行 CCDash，崩溃自动重启，登录自动启动：

```bash
# 只装 server 自启
./launchd/install.sh server

# server + SSH 隧道（会交互式询问远程主机/端口）
./launchd/install.sh server tunnel

# 卸载
./launchd/install.sh uninstall
```

安装器会从 `launchd/*.template` 生成真正的 plist，写入 `~/Library/LaunchAgents/`，其中仓库路径和 `python3` 会被脚本自动填充；SSH 隧道的主机/端口/用户在执行时交互式输入——**仓库里不会留下任何隐私信息**。

常用命令：

```bash
launchctl list | grep ccdash                              # 查看状态
launchctl kickstart -k gui/$(id -u)/com.ccdash.server     # 重启 server
tail -f /tmp/ccdash.log                                   # 查看日志
```

日志输出：`/tmp/ccdash.log`（server）、`/tmp/ccdash-tunnel.log`（隧道）。

---

## ⌨️ CLI 命令行工具

不离开终端即可查看用量：

```bash
python3 ccdash-cli.py status        # 今日概览 + 额度仪表
python3 ccdash-cli.py top           # 项目 TOP 5
python3 ccdash-cli.py models        # 模型成本明细
python3 ccdash-cli.py budget        # 预算进度条
python3 ccdash-cli.py live          # 最近 API 调用
```

连接远程 CCDash：

```bash
python3 ccdash-cli.py --server http://myserver:8420 status
```

> 需要 `server.py` 运行中。零依赖，只需 Python。

---

## 🔔 Webhook 通知

额度不足或预算超标时自动告警。

在面板 **设置** → **Webhook 通知** 中配置，或在 `config.json` 中添加：

```json
{
  "webhooks": [
    {
      "url": "https://hooks.slack.com/services/T.../B.../xxx",
      "format": "slack",
      "enabled": true,
      "events": ["all"]
    }
  ]
}
```

支持 Slack、Discord 和通用 HTTP Webhook。后台每 5 分钟检查一次触发条件（额度 >80%、每日预算超标）。

---

## 🚀 全部功能一览

按使用场景分组：

### 👁 看到正在发生的一切

| | |
|---|---|
| 📈 **实时概览** | HUD 仪表盘（5h/7d 额度）· RPM / TPM / 消耗速率 · 成本预估（$/day）· 平均首字 & 耗时 · 日/周环比卡片翻转 |
| 🟢 **会话实时状态** ·`v0.9.2` | 会话列表每行显示 **工作中** / **等待中** / **已结束** 徽章（带脉冲动画）· 本地 + 远程都支持 |
| 📡 **实时流** | 实时 API 调用流 · 彩色 Token 指示器（↓input ↑output ⟲cache）· 单次调用成本 · 暂停控制 |
| 🔌 **API 端点检测** ·`v0.9.2` | 自动检测 Claude Code 连的是**官方** 还是 **中转站 / 代理**，凭据掩码 |

### 💰 看懂成本

| | |
|---|---|
| 💰 **成本追踪** | 基于[官方定价](https://docs.anthropic.com/en/docs/about-claude/pricing)逐次计费 · 每日趋势 · 按模型/项目拆分 · 缓存效率评级 |
| 💡 **智能优化** | 模型降级建议（Opus → Sonnet 节省估算）· 缓存优化 · 成本异常检测 · 高峰时段提醒 |
| 💰 **Token 预算** | 每日 / 每周 / 每月上限 · 概览页实时进度条 · 60% / 80% / 100% 三档预警 · 超标脉冲动画 |
| 📊 **对比报告** | 周报 & 月报 · 环比增减箭头 · 亮点（最活跃模型、缓存命中率、日均成本、最活跃日）|
| ⚡ **限速预测** | 风险等级（安全→紧急）· 剩余可用时间倒计时 · 多窗口消耗速率（5m / 15m / 30m / 60m） |

### 🔍 深入每个会话

| | |
|---|---|
| 📋 **会话详情** | 点击任意会话 → 完整对话时间轴 · 用户/助手消息带工具调用徽章 · 文件操作追踪 · 会话链（同项目下所有会话）· 复制 Session ID / `claude --resume` 命令 · 隐私模式 |
| 🔀 **多选对比** | 勾选多个会话 → 合并统计 + 模型 / 工具分布图表 |
| 🔗 **Git 关联** | 每 commit AI 成本 · AI 辅助提交占比 · 平均每 commit 成本 · 提交表 |
| 🔍 **深度分析** | 模型 DNA 堆叠条 · 工具分布环图 · **MCP 服务器分析** · 编码节奏 · 工作模式 · **Prompt 效率**（输出比率 / 缓存评级 / 交互模式）· 活跃热力图 · 上下文窗口使用率 |

### 🌐 跨机器使用

| | |
|---|---|
| 🌐 **多服务器聚合** | 远程部署轻量级 `agent.py` · 所有数据汇总到一个面板 · 远程会话详情、会话链、**实时状态**一起同步 · SSH 隧道友好 |
| 👥 **多账户** | 配置多个 Claude 账户（个人 / 工作）· 分账户 5h / 7d 额度追踪 · 设置页实时显示 |
| 🍏 **macOS launchd 自启** ·`v0.9.2` | 一条命令：`./launchd/install.sh server [tunnel]` · 崩溃自动重启 · autossh 隧道自启 · 模板无任何硬编码 |
| 🔔 **Webhook 告警** | Slack / Discord / HTTP · 后台监控额度 >80% 和预算超标 · 连通性测试 · Slack/Discord 格式自动识别 |

### ⌨️ 终端玩家

| | |
|---|---|
| ⌨️ **`ccdash-cli.py`** | 五个命令：`status` · `top` · `models` · `budget` · `live` · 彩色输出 · `--server URL` 连接远程 · 零依赖 |
| 📤 **数据导出** | CSV / JSON 导出，尊重当前数据源和过滤条件 |

### 🎨 不糟糕的 UI

暗色 / 亮色主题平滑切换 · Phosphor 图标 · HUD 渐变发光仪表盘 · 滑动导航指示器 · 页面过渡 · 卡片翻转动画 · 中英双语 · 分析页 **Core / Advanced** 标签页拆分长页面 · 各区块可折叠

---

## 📄 许可证

[MIT](LICENSE) — 随便用。

## Star History

<a href="https://www.star-history.com/?repos=zihenghe04%2FCCDash&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=zihenghe04/CCDash&type=date&theme=dark&legend=bottom-right" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=zihenghe04/CCDash&type=date&legend=bottom-right" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=zihenghe04/CCDash&type=date&legend=bottom-right" />
 </picture>
</a>


<div align="center">
  <br>
  <p><sub>Built with ☕ and curiosity</sub></p>
</div>

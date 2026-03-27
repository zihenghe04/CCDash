# CCDash Roadmap / 迭代路线图

> Last updated: 2026-03-27 · Current version: **v0.5.1**

---

## Phase 1: Analytics Deep Dive (v0.6.x)
> Focus: 挖掘现有数据的深层价值，零新依赖

### v0.6.0 — MCP Server Analytics / MCP 工具分析
**Priority: HIGH** · Complexity: LOW · Data: already in JSONL

JSONL 中已有 `tool_use` 事件（包含工具名），但目前只做了简单的调用次数统计。MCP 生态正在爆发，用户迫切需要了解每个 MCP Server 的消耗情况。

**Features:**
- MCP Server 调用频次排行（按 server 分组，如 `mcp__playwright__*` → Playwright）
- 每个 MCP Server 的 token 消耗（触发该工具的 assistant 响应的 token 开销）
- MCP 调用成功率（通过 `tool_result` 中是否有 error 判断）
- MCP 使用趋势图（每日调用量变化）
- 新增 Analytics 页面 "MCP Tools" 标签页：堆叠柱状图 + 明细表

**Backend:**
- `GET /api/mcp-stats` — MCP server 级别的聚合统计
- `GET /api/mcp-trend` — MCP 使用每日趋势

**UI:** Analytics 页新增标签页，复用现有 donut + bar chart 组件

---

### v0.6.1 — Rate Limit Predictor / 限速预测器
**Priority: HIGH** · Complexity: MEDIUM · Data: existing burn rate

用户最大的痛点之一："我还能用多久才触发限速？" 目前只有 burn rate 指标，但没有预测能力。

**Features:**
- 基于过去 30min 的 burn rate，预测触发 5h/7d 限速的剩余时间
- "安全使用速率"建议：在剩余时间内均匀分配 quota 的理想 RPM
- 限速风险等级：🟢 Safe → 🟡 Caution → 🔴 Danger → ⚫ Throttled
- 概览页新增预测卡片，显示倒计时 + 建议
- 历史限速事件记录（检测 quota 突然重置的时间点）

**Backend:**
- `GET /api/rate-prediction` — 预测数据（预计触发时间、安全速率、风险等级）
- 基于滑动窗口的 token 消耗速率建模

**UI:** 概览页 HUD 仪表盘区域新增预测信息；新增限速风险指示灯

---

### v0.6.2 — Prompt Efficiency Analysis / Prompt 效率分析
**Priority: MEDIUM** · Complexity: MEDIUM · Data: existing JSONL

帮助用户理解自己的 AI 使用效率，找到改进空间。

**Features:**
- 有效输出率：output_tokens / total_tokens（越高越好）
- 缓存效率评级：Excellent (>80%) / Good (>50%) / Fair (>20%) / Poor
- 会话效率排行：哪些 session 的 "token 性价比" 最高/最低
- 交互模式分类：
  - **Exploration** — 短对话、多轮提问（高 input/output ratio）
  - **Building** — 长代码生成（高 output、多 tool_use）
  - **Debugging** — 反复修改（多轮、高 cache_read）
  - **Review** — 大量代码阅读（高 cache_creation）
- 每种模式的 token 消耗对比
- 效率趋势：你的 prompt 效率是在提高还是下降？

**Backend:**
- `GET /api/efficiency` — 效率指标 + 模式分类
- 扩展现有扫描器，增加 per-session 效率计算

**UI:** Analytics 页新增 "Efficiency" 标签页

---

## Phase 2: Smart Insights (v0.7.x)
> Focus: 智能分析与主动建议，从"展示数据"升级为"理解数据"

### v0.7.0 — Cost Optimization Engine / 智能成本优化
**Priority: HIGH** · Complexity: MEDIUM-HIGH

从被动展示成本到主动优化建议。

**Features:**
- **模型降级建议**：检测使用 Opus 完成简单任务的 session（output < 200 tokens 且无复杂工具调用），建议用 Sonnet
- **缓存优化建议**：检测低缓存命中率的 session，分析原因（频繁切换项目、prompt 过短等）
- **时段优化建议**：避开高峰时段以减少限速风险
- **成本异常检测**：某天成本异常飙升时自动标记并分析原因
- **周度优化报告**：汇总本周的优化建议和潜在节省金额
- 概览页新增 "Insights" 卡片，展示 top 3 优化建议

**Backend:**
- `GET /api/insights` — 优化建议列表（按影响金额排序）
- 规则引擎：基于统计阈值的建议生成
- 不依赖 LLM，纯规则驱动（保持零依赖特性）

**UI:**
- 概览页 Insights 卡片（可折叠，显示 top 3）
- Settings 页可配置建议灵敏度

---

### v0.7.1 — Token Budget Management / Token 预算管理
**Priority: HIGH** · Complexity: MEDIUM

为重度用户和团队提供成本控制手段。

**Features:**
- 设定 daily / weekly / monthly token 或 cost 预算上限
- 实时预算消耗进度条（概览页）
- 预算预警阈值：60% / 80% / 100% 三档
- 超标时：
  - 面板内弹出警告 banner
  - 可选 Webhook 通知（为 v0.8.0 做准备）
- 预算历史：每日/每周实际 vs 预算对比折线图
- 支持按项目设定独立预算

**Backend:**
- `GET/POST /api/budget` — 预算 CRUD
- `GET /api/budget-status` — 当前预算消耗状态
- 预算配置持久化到 `config.json`

**UI:**
- Settings 页新增 Budget 配置区
- 概览页新增预算进度条
- 超标时全局 banner 警告

---

### v0.7.2 — Comparison Reports / 对比报表
**Priority: MEDIUM** · Complexity: MEDIUM

自动化的周度/月度使用报告。

**Features:**
- **周报**：本周 vs 上周全维度对比（消息、token、成本、效率、模型分布）
- **月报**：本月 vs 上月 + 月度趋势
- 关键指标变化高亮（↑↓ 箭头 + 百分比变化）
- 可导出为 PDF（基于浏览器 print 样式）或 Markdown
- 报表页面：卡片式布局，自动生成摘要文本
- "本月亮点"：最活跃的项目、最耗 token 的 session、最佳缓存命中率等

**Backend:**
- `GET /api/report?type=weekly` / `GET /api/report?type=monthly`
- 聚合现有 daily 数据生成报表

**UI:** 新增 "Reports" 页面（侧边栏新 tab），或作为 Analytics 的子页面

---

## Phase 3: External Integration (v0.8.x)
> Focus: 与外部工具打通，构建完整工作流

### v0.8.0 — Git Integration / Git 关联分析
**Priority: HIGH** · Complexity: MEDIUM

将 AI 使用与代码产出关联，量化 AI 辅助的价值。

**Features:**
- 扫描项目目录下的 `.git`，关联 Claude session 与 git commit
- **Per-commit AI 成本**：每个 commit 时间窗口内的 Claude 消耗
- **Per-PR AI 成本**：PR 中所有 commit 的累计 AI 消耗
- **AI 参与度指标**：有 AI 辅助的 commit 占比
- **代码产出效率**：每 $1 AI 成本产出多少行代码变更
- 项目详情页增加 Git Timeline（commit + Claude session 交错展示）

**Backend:**
- `GET /api/git-stats?project=xxx` — 项目的 git 关联统计
- 调用 `git log` 获取 commit 历史，按时间窗口匹配 session
- 不依赖 GitHub API（纯本地 git）

**UI:** 项目详情页新增 Git 关联面板

---

### v0.8.1 — Webhook & Notifications / 通知系统
**Priority: HIGH** · Complexity: MEDIUM

覆盖用户不在面板前的场景。

**Features:**
- **Webhook 支持**：配置 URL + 事件类型，POST JSON payload
- **内置模板**：
  - Slack Incoming Webhook
  - Discord Webhook
  - 飞书/企业微信 Bot
  - Generic HTTP POST
- **触发事件**：
  - 限速触发 / 限速解除
  - 预算超标（60%/80%/100%）
  - 每日摘要（每天 23:00 自动发送）
  - 异常消耗告警
- **通知历史**：记录每条通知的发送时间和状态
- Settings 页配置通知规则

**Backend:**
- `POST /api/webhooks` — Webhook CRUD
- `GET /api/notification-history` — 通知历史
- 后台定时线程检查触发条件

**注意**：Webhook 发送需要网络请求，这是首次引入对外网络调用（之前只有 LiteLLM pricing fetch）

---

### v0.8.2 — CLI Quick Command / 命令行快查
**Priority: MEDIUM** · Complexity: LOW

终端用户不离开命令行即可查看用量。

**Features:**
- 独立 Python 脚本 `ccdash` 或 `ccdash-cli.py`
- 命令：
  ```
  ccdash status    — 今日概览（调用数、成本、quota）
  ccdash top       — 项目 TOP 5
  ccdash models    — 模型消耗排行
  ccdash budget    — 预算进度
  ccdash live      — 实时调用流（类似 tail -f）
  ```
- 彩色终端输出（ANSI escape codes）
- 直接读取本地数据（不依赖 server.py 运行）
- 也可连接 server.py API（`ccdash --server http://localhost:8420 status`）
- 可作为 Claude Code hook 集成（每次对话结束后显示本次消耗）

**Implementation:** 单文件 `ccdash-cli.py`，零依赖

---

## Phase 4: Advanced Features (v0.9.x)
> Focus: 高级功能，面向专业用户和团队

### v0.9.0 — Multi-Account Support / 多账户
**Priority: MEDIUM** · Complexity: HIGH

支持同时监控多个 Claude 账户（个人 + 公司）。

**Features:**
- 配置多个 session_key + org_id
- 每个账户独立的 quota 追踪
- 聚合视图：所有账户的总消耗
- 分账户视图：切换查看单个账户
- 账户别名（"Personal", "Work", "Team"）

**Architecture change:**
- `config.json` 支持 `accounts[]` 数组
- quota fetcher 支持并行查询多账户
- 前端增加账户切换器

---

### v0.9.1 — Session Replay / 会话回放
**Priority: MEDIUM** · Complexity: HIGH

像录屏一样回放 coding session，适合教学和复盘。

**Features:**
- 选择一个 session，进入回放模式
- 按时间轴逐步展示：用户输入 → AI 响应 → 工具调用 → 文件变更
- 可调节播放速度（1x / 2x / 4x）
- 暂停、跳转到任意时间点
- 标注关键节点（首次 pass、错误发生、修复完成）
- 可导出为 GIF 或视频

**Implementation:** 纯前端实现，基于 session_detail 数据的时序展示

---

### v0.9.2 — Plugin System / 插件系统
**Priority: MEDIUM** · Complexity: HIGH

开放生态，让社区贡献数据源适配器。

**Features:**
- Python 插件接口：
  ```python
  class DataSourcePlugin:
      name: str
      def scan(self) -> ScanResult: ...
      def get_sessions(self) -> list[Session]: ...
  ```
- 内置插件：Claude Code, Codex CLI
- 社区插件：Cursor, Windsurf, Aider, Continue.dev, OpenCode
- 插件发现：`plugins/` 目录自动加载
- 插件配置通过 Settings 页管理
- 插件 SDK 文档

---

## Phase 5: v1.0 & Beyond
> Focus: 稳定化 + 生态建设

### v1.0.0 — Stable Release
- API 稳定性保证
- 完整文档（用户指南 + API 文档 + 插件开发指南）
- PWA 支持（manifest.json + service worker，移动端可用）
- Docker 镜像发布
- Homebrew formula / pip install 支持
- 性能优化（大数据量场景：1000+ session files）

### Future Ideas (Post v1.0)
- **Grafana / Prometheus 导出** — `/metrics` 端点
- **VS Code / JetBrains 侧边栏插件** — IDE 内查看用量
- **Team Dashboard** — 多用户聚合视图（需要中心化部署）
- **AI 驱动洞察** — 用 Claude 自动分析使用模式并生成建议
- **Sankey Token 流向图** — 项目 → 模型 → 工具的 token 流向
- **文件操作热力图** — 哪些文件被 AI 读写最多

---

## Timeline Estimate / 时间线估算

```
2026 Q1 (已完成)
  ├── v0.1.0  Core dashboard
  ├── v0.2.0  Multi-CLI (Codex)
  ├── v0.3.0  Session detail & chain
  ├── v0.4.0  Data source switching
  ├── v0.5.0  Web & Desktop conversations
  └── v0.5.1  Today's model breakdown + Demo site

2026 Q2 (planned)
  ├── v0.6.0  MCP Server Analytics          ← 1-2 days
  ├── v0.6.1  Rate Limit Predictor          ← 1-2 days
  ├── v0.6.2  Prompt Efficiency Analysis    ← 2-3 days
  ├── v0.7.0  Cost Optimization Engine      ← 3-4 days
  ├── v0.7.1  Token Budget Management       ← 2-3 days
  └── v0.7.2  Comparison Reports            ← 2-3 days

2026 Q3 (planned)
  ├── v0.8.0  Git Integration               ← 3-4 days
  ├── v0.8.1  Webhook & Notifications       ← 2-3 days
  └── v0.8.2  CLI Quick Command             ← 1-2 days

2026 Q4 (planned)
  ├── v0.9.0  Multi-Account                 ← 3-5 days
  ├── v0.9.1  Session Replay                ← 4-5 days
  ├── v0.9.2  Plugin System                 ← 5-7 days
  └── v1.0.0  Stable Release               ← polish + docs
```

---

## Principles / 迭代原则

1. **Zero dependencies first** — 尽量保持纯 Python stdlib + Vanilla JS 的零依赖特性
2. **Data already there** — 优先做能用现有 JSONL 数据实现的功能
3. **Incremental value** — 每个版本都是可用的，不做 "等全部完成才有价值" 的功能
4. **Privacy by default** — 所有新功能默认不发送数据到外部（Webhook 除外，且需用户显式配置）
5. **Community driven** — 在 GitHub Issues 中征集需求优先级

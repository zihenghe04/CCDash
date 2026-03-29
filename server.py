#!/usr/bin/env python3
"""Claude Usage Dashboard — 订阅用量全局监控后端"""

import json
import os
import time
import datetime
import threading
import urllib.parse
import copy
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

import urllib.request
import urllib.error
import subprocess

PORT = 8420
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
USAGE_CACHE_FILE = CLAUDE_DIR / ".statusline-usage-cache"
CONFIG_FILE = CLAUDE_DIR / "dashboard" / "config.json"
DASHBOARD_DIR = CLAUDE_DIR / "dashboard"

# Codex CLI paths
CODEX_DIR = Path.home() / ".codex"
CODEX_SESSIONS_DIR = CODEX_DIR / "sessions"
CODEX_ARCHIVED_DIR = CODEX_DIR / "archived_sessions"
CODEX_CONFIG_FILE = CODEX_DIR / "config.toml"

# ============================================================
# 缓存
# ============================================================
_scan_cache = {"data": None, "time": 0, "file_mtimes": {}}
_scan_lock = threading.Lock()
SCAN_TTL = 300  # 5 minutes

_codex_cache = {"data": None, "time": 0}
_codex_lock = threading.Lock()
CODEX_TTL = 300

_live_cache = {"data": None, "time": 0}
LIVE_TTL = 10

_history_cache = {"data": None, "time": 0, "mtime": 0}
HISTORY_TTL = 60

_remote_cache = {}  # {url: {"data": ..., "time": ...}}
REMOTE_TTL = 15

_codex_logs_cache = {"data": None, "time": 0}

_claude_usage_cache = {"data": None, "time": 0}
CLAUDE_USAGE_TTL = 60

_web_conv_cache = {"data": None, "time": 0}
WEB_CONV_TTL = 120


# ============================================================
# 远程 Agent 聚合
# ============================================================
def _load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {"remotes": []}


def _fetch_remote(url, token=None, timeout=15):
    """从远程 Agent 获取 JSON 数据"""
    try:
        req = urllib.request.Request(url)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [Remote] 获取失败 {url}: {e}")
        return None


def _fetch_remote_cached(base_url, path, token=None, force=False):
    """带缓存的远程请求"""
    full_url = base_url.rstrip("/") + path
    now = time.time()
    if not force:
        cached = _remote_cache.get(full_url)
        if cached and (now - cached["time"]) < REMOTE_TTL:
            return cached["data"]
    data = _fetch_remote(full_url, token)
    if data:
        _remote_cache[full_url] = {"data": data, "time": now}
    return data


def _clear_all_caches():
    """手动刷新时清除所有缓存"""
    _remote_cache.clear()
    _live_cache.update(data=None, time=0)
    _history_cache.update(data=None, time=0, mtime=0)
    _codex_cache.update(data=None, time=0)
    _codex_logs_cache.update(data=None, time=0)
    _web_conv_cache.update(data=None, time=0)


def _get_active_remotes():
    """获取已启用的远程 Agent 列表"""
    config = _load_config()
    return [r for r in config.get("remotes", []) if r.get("enabled", False)]


def _merge_overview(local, remote_data_list):
    """合并 overview 数据"""
    result = dict(local)
    for rd in remote_data_list:
        if not rd:
            continue
        result["total_messages"] += rd.get("total_messages", 0)
        result["total_sessions"] += rd.get("total_sessions", 0)
        result["total_tokens"] += rd.get("total_tokens", 0)
        result["total_projects"] += rd.get("total_projects", 0)
        result["today_messages"] += rd.get("today_messages", 0)
        result["today_sessions"] += rd.get("today_sessions", 0)
    return result


def _merge_models(local_models, remote_data_list):
    """合并 models 数据"""
    merged = {}
    for model, v in local_models.items():
        merged[model] = dict(v)
    for rd in remote_data_list:
        if not rd or "models" not in rd:
            continue
        for model, v in rd["models"].items():
            if model not in merged:
                merged[model] = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0}
            for k in ("input", "output", "cache_read", "cache_create", "calls"):
                merged[model][k] += v.get(k, 0)
    return merged


def _merge_daily(local_activity, local_tokens, remote_data_list):
    """合并 daily 数据"""
    # 建立按日期的索引
    act_map = {a["date"]: dict(a) for a in local_activity}
    tok_map = {t["date"]: dict(t) for t in local_tokens}

    for rd in remote_data_list:
        if not rd:
            continue
        for ra in rd.get("activity", []):
            d = ra["date"]
            if d in act_map:
                act_map[d]["messages"] += ra.get("messages", 0)
                act_map[d]["sessions"] += ra.get("sessions", 0)
                act_map[d]["tools"] += ra.get("tools", 0)
            else:
                act_map[d] = dict(ra)
        for rt in rd.get("tokens", []):
            d = rt["date"]
            if d in tok_map:
                existing = tok_map[d].get("byModel", {})
                for model, vals in rt.get("byModel", {}).items():
                    if model not in existing:
                        existing[model] = dict(vals)
                    else:
                        for k in ("input", "output", "cache_read", "cache_create"):
                            existing[model][k] = existing[model].get(k, 0) + vals.get(k, 0)
                tok_map[d]["byModel"] = existing
            else:
                tok_map[d] = dict(rt)

    dates = sorted(set(list(act_map.keys()) + list(tok_map.keys())))
    activity = [act_map.get(d, {"date": d, "messages": 0, "sessions": 0, "tools": 0}) for d in dates]
    tokens = [tok_map.get(d, {"date": d, "byModel": {}}) for d in dates]
    return activity, tokens


def _merge_projects(local_projects, remote_data_list):
    """合并 projects 数据"""
    merged = {}
    for p in local_projects:
        key = p["name"] + " (local)"
        merged[key] = dict(p)
        merged[key]["name"] = key
        merged[key]["source"] = "local"
    for rd in remote_data_list:
        if not rd:
            continue
        remote_name = rd.get("_remote_name", "cloud")
        for p in rd.get("projects", []):
            key = p["name"] + f" ({remote_name})"
            if key in merged:
                merged[key]["messages"] += p.get("messages", 0)
                merged[key]["tokens_total"] += p.get("tokens_total", 0)
            else:
                merged[key] = dict(p)
                merged[key]["name"] = key
                # Estimate cost for remote projects if missing
                if "cost_usd" not in merged[key]:
                    merged[key]["cost_usd"] = round(p.get("tokens_total", 0) * 3.0 / 1_000_000, 4)
    result = sorted(merged.values(), key=lambda x: -x.get("tokens_total", 0))
    return result[:20]


def _merge_live(local_live, remote_data_list):
    """合并 live 数据"""
    calls = list(local_live.get("calls", []))
    totals = dict(local_live.get("totals", {}))
    for rd in remote_data_list:
        if not rd:
            continue
        for c in rd.get("calls", []):
            c["project"] = c.get("project", "") + " (cloud)"
            calls.append(c)
        for k in ("input", "output", "cache_read", "cache_create", "calls"):
            totals[k] = totals.get(k, 0) + rd.get("totals", {}).get(k, 0)
    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"calls": calls, "totals": totals}


# ============================================================
# 工具函数
# ============================================================
def friendly_project_name(dir_name: str) -> str:
    """"-Users-john-Desktop-MyProject" → "SEU-Thesis-LaTeX" """
    parts = dir_name.strip("-").split("-")
    # Extract meaningful name
    # Skip common path, Desktop, Documents 等路径前缀
    skip = {"users", "user", "home", "desktop", "documents", "downloads", "projects", "workspace"}
    meaningful = [p for p in parts if p.lower() not in skip and len(p) > 1]
    if meaningful:
        return "-".join(meaningful[-3:])  # 取最后3段
    return dir_name


def parse_iso_ts(ts_str: str) -> datetime.datetime:
    """解析 ISO 8601 时间戳"""
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(ts_str)
    except Exception:
        return None


def ts_to_date(ts_str: str) -> str:
    """ISO 时间戳 → 日期字符串 YYYY-MM-DD"""
    dt = parse_iso_ts(ts_str)
    return dt.strftime("%Y-%m-%d") if dt else ""


def ms_to_date(ms: int) -> str:
    """毫秒时间戳 → 日期字符串"""
    try:
        return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""


def ms_to_hour_dow(ms: int):
    """毫秒时间戳 → (hour 0-23, day_of_week 0=Mon..6=Sun)"""
    try:
        dt = datetime.datetime.fromtimestamp(ms / 1000)
        return dt.hour, dt.weekday()
    except Exception:
        return None, None


# ============================================================
# Dynamic pricing from LiteLLM (2594 models, 24h cache)
# ============================================================
LITELLM_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
_litellm_cache = {"data": None, "time": 0}
LITELLM_TTL = 86400  # 24 hours

def _fetch_litellm_pricing():
    """Fetch model pricing from LiteLLM GitHub (cached 24h)"""
    now = time.time()
    if _litellm_cache["data"] and (now - _litellm_cache["time"]) < LITELLM_TTL:
        return _litellm_cache["data"]
    try:
        req = urllib.request.Request(LITELLM_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            # Convert to our format: per_token → per_million
            pricing = {}
            for model_name, info in raw.items():
                if not isinstance(info, dict):
                    continue
                inp = info.get("input_cost_per_token", 0)
                out = info.get("output_cost_per_token", 0)
                cr = info.get("cache_read_input_token_cost", 0)
                cw = info.get("cache_creation_input_token_cost", 0)
                ctx = info.get("max_input_tokens") or info.get("max_tokens", 0)
                if inp or out:
                    pricing[model_name] = {
                        "input": round(inp * 1e6, 4),
                        "output": round(out * 1e6, 4),
                        "cache_read": round(cr * 1e6, 4),
                        "cache_create": round(cw * 1e6, 4),
                        "context_window": ctx,
                    }
            _litellm_cache["data"] = pricing
            _litellm_cache["time"] = now
            print(f"  [LiteLLM] 获取定价成功: {len(pricing)} 模型")
            return pricing
    except Exception as e:
        print(f"  [LiteLLM] 获取定价失败: {e}")
        return {}

def _get_model_pricing(model_name):
    """Get pricing for a model: custom → LiteLLM → hardcoded → default"""
    # 1. Check user custom pricing
    config = _load_config()
    custom = config.get("custom_pricing", {}).get(model_name)
    if custom:
        return custom
    # 2. Check LiteLLM dynamic pricing
    litellm = _fetch_litellm_pricing()
    if model_name in litellm:
        return litellm[model_name]
    # 3. Try partial match (e.g., "claude-opus-4-6" might be logged differently)
    for k, v in litellm.items():
        if model_name in k or k in model_name:
            return v
    # 4. Fall back to hardcoded
    if model_name in MODEL_PRICING:
        return MODEL_PRICING[model_name]
    return DEFAULT_PRICING

# Hardcoded fallback (used when LiteLLM is unreachable)
MODEL_PRICING = {
    # Opus 4.6 / 4.5: $5 input, $25 output, cache_write(5m)=$6.25, cache_read=$0.50
    "claude-opus-4-6":            {"input": 5.0,  "output": 25.0,  "cache_read": 0.50,  "cache_create": 6.25},
    "claude-opus-4-5-20251101":   {"input": 5.0,  "output": 25.0,  "cache_read": 0.50,  "cache_create": 6.25},
    # Opus 4.1 / 4.0 (legacy): $15 input, $75 output
    "claude-opus-4-1-20250805":   {"input": 15.0, "output": 75.0,  "cache_read": 1.50,  "cache_create": 18.75},
    "claude-opus-4-20250514":     {"input": 15.0, "output": 75.0,  "cache_read": 1.50,  "cache_create": 18.75},
    # Sonnet 4.6 / 4.5 / 4: $3 input, $15 output
    "claude-sonnet-4-6":          {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-sonnet-4-5":          {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-sonnet-4-5-20250929": {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-sonnet-4-20250514":   {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    # Haiku 4.5: $1 input, $5 output
    "claude-haiku-4-5-20251001":  {"input": 1.0,  "output": 5.0,   "cache_read": 0.10,  "cache_create": 1.25},
    # GPT/Codex models (OpenAI official pricing: https://developers.openai.com/api/docs/pricing)
    "gpt-5.3-codex":              {"input": 1.75, "output": 14.0,  "cache_read": 0.175, "cache_create": 0},
    "gpt-5.3-chat-latest":        {"input": 1.75, "output": 14.0,  "cache_read": 0.175, "cache_create": 0},
    "gpt-5.4":                    {"input": 2.50, "output": 15.0,  "cache_read": 0.25,  "cache_create": 0},
    "gpt-5.4-mini":               {"input": 0.75, "output": 4.50,  "cache_read": 0.075, "cache_create": 0},
    "gpt-5.4-nano":               {"input": 0.20, "output": 1.25,  "cache_read": 0.02,  "cache_create": 0},
    "gpt-5.4-pro":                {"input": 30.0, "output": 180.0, "cache_read": 30.0,  "cache_create": 0},
    "gpt-5.2-codex":              {"input": 1.75, "output": 14.0,  "cache_read": 0.175, "cache_create": 0},
    "gpt-5-mini":                 {"input": 0.75, "output": 4.50,  "cache_read": 0.075, "cache_create": 0},
    "gpt-4o":                     {"input": 2.50, "output": 10.0,  "cache_read": 1.25,  "cache_create": 0},
    "gpt-4o-mini":                {"input": 0.15, "output": 0.60,  "cache_read": 0.075, "cache_create": 0},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_create": 3.75}

CONTEXT_WINDOWS = {
    "claude-opus-4-6": 1000000,
    "claude-opus-4-5-20251101": 200000,
    "claude-sonnet-4-6": 1000000,
    "claude-sonnet-4-5-20250929": 200000,
    "claude-sonnet-4-5": 200000,
    "claude-sonnet-4-20250514": 200000,
    "claude-haiku-4-5-20251001": 200000,
    "claude-opus-4-1-20250805": 200000,
    "claude-opus-4-20250514": 200000,
    "gpt-5.3-codex": 258400,
    "gpt-5.4": 258400,
    "gpt-4o": 128000,
}
DEFAULT_CONTEXT_WINDOW = 200000

def _calc_cost(model, inp, out, cache_read, cache_create):
    """Calculate equivalent API cost in USD using: custom → LiteLLM → hardcoded → default"""
    p = _get_model_pricing(model)
    # cache_create pricing: use cache_create if present and non-None, else cache_write, else default
    cc_price = p.get("cache_create") if p.get("cache_create") is not None else p.get("cache_write", 3.75)
    return (inp * p.get("input", 3.0) + out * p.get("output", 15.0) +
            cache_read * p.get("cache_read", 0.3) +
            cache_create * cc_price) / 1_000_000


def _model_provider(model_name):
    """Classify model by provider"""
    m = model_name.lower()
    if m.startswith('claude') or 'anthropic' in m:
        return 'Anthropic'
    elif m.startswith('gpt') or 'openai' in m or 'codex' in m:
        return 'OpenAI'
    elif 'glm' in m or 'zhipu' in m:
        return 'ZhipuAI'
    elif 'minimax' in m:
        return 'MiniMax'
    elif 'gemini' in m or 'google' in m:
        return 'Google'
    elif 'mistral' in m:
        return 'Mistral'
    elif 'llama' in m or 'meta' in m:
        return 'Meta'
    elif 'qwen' in m or 'alibaba' in m:
        return 'Alibaba'
    elif 'deepseek' in m:
        return 'DeepSeek'
    else:
        return 'Other'


# ============================================================
# 全局 JSONL 扫描器（核心）
# ============================================================
def _scan_all_projects(force=False):
    """扫描 ~/.claude/projects/ 下所有 JSONL 文件，提取 usage 数据"""
    now = time.time()
    with _scan_lock:
        if not force and _scan_cache["data"] and (now - _scan_cache["time"]) < SCAN_TTL:
            return _scan_cache["data"]

    print(f"  [Scanner] 开始全量扫描 {PROJECTS_DIR}...")
    t0 = time.time()

    # 聚合结构
    daily = {}       # date -> {messages, sessions: set, tools, tokens: {model: {in,out,cr,cc}}}
    models = {}      # model -> {in, out, cr, cc, calls}
    projects = {}    # project_dir_name -> {messages, tokens_total, sessions: set, friendly_name, models: {model: {in,out,cr,cc}}}
    tools_stats = {} # tool_name -> {"calls": int, "sessions": set()}
    mcp_stats = {}   # mcp_server_name -> {"calls": int, "sessions": set(), "tools": {tool_name: calls}}
    daily_tools = {} # date -> {tool_name: calls}
    session_efficiency = {}  # session_id -> {"input": int, "output": int, "cache_read": int, "cache_create": int, "calls": int, "tool_calls": int, "project": str}
    session_entrypoints = {}  # session_id -> entrypoint (cli, claude-desktop, sdk-ts, etc.)
    total_messages = 0
    total_sessions = set()
    total_tokens = 0

    if not PROJECTS_DIR.exists():
        print("  [Scanner] projects 目录不存在")
        result = {"daily": {}, "models": {}, "projects": {}, "total_messages": 0,
                  "total_sessions": 0, "total_tokens": 0}
        with _scan_lock:
            _scan_cache["data"] = result
            _scan_cache["time"] = time.time()
        return result

    file_count = 0
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        proj_name = project_dir.name
        friendly = friendly_project_name(proj_name)

        for jsonl_file in project_dir.glob("*.jsonl"):
            file_count += 1
            session_id = jsonl_file.stem
            file_session_dates = set()

            try:
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            evt = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        evt_type = evt.get("type", "")
                        ts = evt.get("timestamp", "")

                        # Track entrypoint per session (majority wins —
                        # session may be resumed from different entrypoints)
                        ep = evt.get("entrypoint", "")
                        if ep:
                            ep_counts = session_entrypoints.setdefault(session_id, {})
                            ep_counts[ep] = ep_counts.get(ep, 0) + 1

                        if evt_type == "user" and "message" in evt:
                            date = ts_to_date(ts) if isinstance(ts, str) else ""
                            if not date:
                                continue
                            total_messages += 1
                            file_session_dates.add(date)

                            daily.setdefault(date, {
                                "messages": 0, "sessions": set(), "tools": 0,
                                "tokens": {}
                            })
                            daily[date]["messages"] += 1
                            daily[date]["sessions"].add(session_id)

                            projects.setdefault(proj_name, {
                                "messages": 0, "tokens_total": 0,
                                "sessions": set(), "friendly_name": friendly
                            })
                            projects[proj_name]["messages"] += 1
                            projects[proj_name]["sessions"].add(session_id)

                        elif evt_type == "assistant" and "message" in evt:
                            msg = evt.get("message", {})
                            if not isinstance(msg, dict):
                                continue
                            usage = msg.get("usage", {})
                            model = msg.get("model", "unknown")
                            date = ts_to_date(ts) if isinstance(ts, str) else ""

                            inp = usage.get("input_tokens", 0) or 0
                            out = usage.get("output_tokens", 0) or 0
                            cr = usage.get("cache_read_input_tokens", 0) or 0
                            cc = usage.get("cache_creation_input_tokens", 0) or 0
                            tok_sum = inp + out + cr + cc
                            total_tokens += tok_sum

                            # 检查 content 中是否有 tool_use
                            content = msg.get("content", [])
                            if isinstance(content, list):
                                tool_count = 0
                                for b in content:
                                    if isinstance(b, dict) and b.get("type") == "tool_use":
                                        tool_count += 1
                                        tool_name = b.get("name", "unknown")
                                        if tool_name:
                                            ts_entry = tools_stats.setdefault(tool_name, {"calls": 0, "sessions": set()})
                                            ts_entry["calls"] += 1
                                            ts_entry["sessions"].add(session_id)
                                            # MCP server grouping: mcp__servername__action -> servername
                                            if tool_name.startswith("mcp__"):
                                                parts = tool_name.split("__")
                                                if len(parts) >= 3:
                                                    server_name = parts[1]
                                                    mcp_entry = mcp_stats.setdefault(server_name, {"calls": 0, "sessions": set(), "tools": {}})
                                                    mcp_entry["calls"] += 1
                                                    mcp_entry["sessions"].add(session_id)
                                                    mcp_entry["tools"][tool_name] = mcp_entry["tools"].get(tool_name, 0) + 1
                                            # Daily tool trend
                                            if date:
                                                dt_entry = daily_tools.setdefault(date, {})
                                                dt_entry[tool_name] = dt_entry.get(tool_name, 0) + 1
                                if tool_count and date:
                                    daily.setdefault(date, {
                                        "messages": 0, "sessions": set(), "tools": 0,
                                        "tokens": {}
                                    })
                                    daily[date]["tools"] += tool_count

                            # Session efficiency tracking
                            se = session_efficiency.setdefault(session_id, {
                                "input": 0, "output": 0, "cache_read": 0,
                                "cache_create": 0, "calls": 0, "tool_calls": 0,
                                "project": friendly
                            })
                            se["input"] += inp
                            se["output"] += out
                            se["cache_read"] += cr
                            se["cache_create"] += cc
                            se["calls"] += 1
                            se["tool_calls"] += (tool_count if isinstance(content, list) else 0)

                            if date:
                                daily.setdefault(date, {
                                    "messages": 0, "sessions": set(), "tools": 0,
                                    "tokens": {}
                                })
                                t_model = daily[date]["tokens"].setdefault(model, {
                                    "input": 0, "output": 0, "cache_read": 0, "cache_create": 0
                                })
                                t_model["input"] += inp
                                t_model["output"] += out
                                t_model["cache_read"] += cr
                                t_model["cache_create"] += cc

                            models.setdefault(model, {
                                "input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0
                            })
                            models[model]["input"] += inp
                            models[model]["output"] += out
                            models[model]["cache_read"] += cr
                            models[model]["cache_create"] += cc
                            models[model]["calls"] += 1

                            if proj_name in projects:
                                projects[proj_name]["tokens_total"] += tok_sum
                                pm = projects[proj_name].setdefault("models", {})
                                pm_entry = pm.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0})
                                pm_entry["input"] += inp
                                pm_entry["output"] += out
                                pm_entry["cache_read"] += cr
                                pm_entry["cache_create"] += cc

            except Exception as e:
                # 跳过损坏的文件
                continue

            total_sessions.add(session_id)

    # 转换 set → count
    for d in daily.values():
        d["sessions"] = len(d.pop("sessions", set()))
    for p in projects.values():
        p["sessions"] = len(p.pop("sessions", set()))
    for ts_entry in tools_stats.values():
        ts_entry["sessions"] = len(ts_entry.pop("sessions", set()))
    for mc_entry in mcp_stats.values():
        mc_entry["sessions"] = len(mc_entry.pop("sessions", set()))
    # Resolve entrypoint counts → majority entrypoint per session
    for sid in session_entrypoints:
        counts = session_entrypoints[sid]
        if isinstance(counts, dict):
            session_entrypoints[sid] = max(counts, key=counts.get)

    elapsed = time.time() - t0
    print(f"  [Scanner] 扫描完成: {file_count} 文件, {total_messages} 消息, "
          f"{len(total_sessions)} 会话, {total_tokens} tokens ({elapsed:.1f}s)")

    # 计算缓存命中率
    total_input = sum(m["input"] for m in models.values())
    total_output = sum(m["output"] for m in models.values())
    total_cache_read = sum(m["cache_read"] for m in models.values())
    total_cache_create = sum(m["cache_create"] for m in models.values())
    total_all_input = total_input + total_cache_read + total_cache_create
    cache_hit_rate = (total_cache_read / total_all_input * 100) if total_all_input > 0 else 0

    result = {
        "daily": daily,
        "models": models,
        "projects": projects,
        "tools_stats": tools_stats,
        "mcp_stats": mcp_stats,
        "daily_tools": daily_tools,
        "session_efficiency": session_efficiency,
        "session_entrypoints": session_entrypoints,
        "total_messages": total_messages,
        "total_sessions": len(total_sessions),
        "total_tokens": total_tokens,
        "total_input": total_input,
        "total_output": total_output,
        "total_cache_read": total_cache_read,
        "total_cache_create": total_cache_create,
        "cache_hit_rate": round(cache_hit_rate, 1),
    }

    with _scan_lock:
        _scan_cache["data"] = result
        _scan_cache["time"] = time.time()

    return result


# ============================================================
# Codex CLI 数据源检测与配置
# ============================================================
def _codex_enabled():
    """Check if Codex data source is enabled"""
    config = _load_config()
    ds = config.get("data_sources", {})
    codex_cfg = ds.get("codex_cli", {})
    if "enabled" in codex_cfg:
        return codex_cfg["enabled"]
    # Auto-detect: check if ~/.codex/ exists and has session files
    return CODEX_SESSIONS_DIR.exists() or CODEX_ARCHIVED_DIR.exists()


def _read_codex_model():
    """Read model name from ~/.codex/config.toml"""
    try:
        import re
        with open(CODEX_CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        # Find top-level 'model = "..."' before any [section]
        # Split on first section header
        top_level = content.split("[")[0] if "[" in content else content
        m = re.search(r'^model\s*=\s*"([^"]+)"', top_level, re.MULTILINE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "codex-unknown"


# ============================================================
# Codex CLI JSONL 扫描器
# ============================================================
def _scan_codex(force=False):
    """Scan ~/.codex/sessions/ and ~/.codex/archived_sessions/ for Codex usage data"""
    now = time.time()
    with _codex_lock:
        if not force and _codex_cache["data"] and (now - _codex_cache["time"]) < CODEX_TTL:
            return _codex_cache["data"]

    if not _codex_enabled():
        return None

    print(f"  [Codex Scanner] 开始扫描 Codex 数据...")
    t0 = time.time()

    default_model = _read_codex_model()

    daily = {}
    models = {}
    projects = {}
    tools_stats = {}
    total_messages = 0
    total_sessions = set()
    total_tokens = 0

    # Collect all rollout JSONL files
    session_files = []
    for search_dir in [CODEX_SESSIONS_DIR, CODEX_ARCHIVED_DIR]:
        if not search_dir.exists():
            continue
        for jsonl_file in search_dir.rglob("rollout-*.jsonl"):
            session_files.append(jsonl_file)

    file_count = 0
    for jsonl_file in session_files:
        file_count += 1
        try:
            events = []
            with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            if not events:
                continue

            # Extract session metadata
            session_id = ""
            cwd = ""
            model = default_model
            first_ts = ""
            last_ts = ""
            user_messages = 0
            tool_calls_in_session = {}

            # Find the LAST token_count event with non-null info and total_token_usage
            last_token_usage = None
            model_context_window = 200000

            for evt in events:
                evt_type = evt.get("type", "")
                ts = evt.get("timestamp", "")

                if ts:
                    if not first_ts:
                        first_ts = ts
                    last_ts = ts

                if evt_type == "session_meta":
                    payload = evt.get("payload", {})
                    session_id = payload.get("id", "") or ""
                    cwd = payload.get("cwd", "") or ""

                elif evt_type == "turn_context":
                    payload = evt.get("payload", {})
                    m = payload.get("model", "")
                    if m:
                        model = m

                elif evt_type == "event_msg":
                    payload = evt.get("payload", {})
                    sub_type = payload.get("type", "")

                    if sub_type == "user_message":
                        user_messages += 1

                    elif sub_type == "token_count":
                        info = payload.get("info")
                        if info and isinstance(info, dict):
                            tu = info.get("total_token_usage")
                            if tu and isinstance(tu, dict):
                                last_token_usage = tu
                            mcw = info.get("model_context_window")
                            if mcw:
                                model_context_window = mcw

                elif evt_type == "response_item":
                    payload = evt.get("payload", {})
                    if payload.get("type") == "function_call":
                        tool_name = payload.get("name", "unknown")
                        if tool_name:
                            tool_calls_in_session[tool_name] = tool_calls_in_session.get(tool_name, 0) + 1

            if not session_id:
                # Derive from filename
                session_id = jsonl_file.stem.replace("rollout-", "")

            # Extract token usage from the LAST cumulative token_count event
            inp = 0
            out = 0
            cache_read = 0
            cache_create = 0
            reasoning_tokens = 0

            if last_token_usage:
                inp = last_token_usage.get("input_tokens", 0) or 0
                cache_read = last_token_usage.get("cached_input_tokens", 0) or 0
                out = last_token_usage.get("output_tokens", 0) or 0
                reasoning_tokens = last_token_usage.get("reasoning_output_tokens", 0) or 0

            tok_sum = inp + out + cache_read + cache_create
            total_tokens += tok_sum
            total_messages += user_messages

            # Project from cwd
            proj_name = cwd or "codex-unknown"
            friendly = cwd.rstrip("/").split("/")[-1] if cwd else "codex"

            # Date from first timestamp
            date = ts_to_date(first_ts) if first_ts else ""

            if date and user_messages > 0:
                daily.setdefault(date, {
                    "messages": 0, "sessions": set(), "tools": 0, "tokens": {}
                })
                daily[date]["messages"] += user_messages
                daily[date]["sessions"].add(session_id)

                # Tools
                total_tool_calls = sum(tool_calls_in_session.values())
                if total_tool_calls:
                    daily[date]["tools"] += total_tool_calls

                # Token data
                if tok_sum > 0:
                    t_model = daily[date]["tokens"].setdefault(model, {
                        "input": 0, "output": 0, "cache_read": 0, "cache_create": 0
                    })
                    t_model["input"] += inp
                    t_model["output"] += out
                    t_model["cache_read"] += cache_read
                    t_model["cache_create"] += cache_create

            # Models aggregate
            if tok_sum > 0 or user_messages > 0:
                models.setdefault(model, {
                    "input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0,
                    "context_window": model_context_window
                })
                models[model]["input"] += inp
                models[model]["output"] += out
                models[model]["cache_read"] += cache_read
                models[model]["cache_create"] += cache_create
                models[model]["calls"] += 1

            # Projects aggregate
            projects.setdefault(proj_name, {
                "messages": 0, "tokens_total": 0,
                "sessions": set(), "friendly_name": friendly,
                "source": "codex"
            })
            projects[proj_name]["messages"] += user_messages
            projects[proj_name]["tokens_total"] += tok_sum
            projects[proj_name]["sessions"].add(session_id)
            pm = projects[proj_name].setdefault("models", {})
            if tok_sum > 0:
                pm_entry = pm.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0})
                pm_entry["input"] += inp
                pm_entry["output"] += out
                pm_entry["cache_read"] += cache_read
                pm_entry["cache_create"] += cache_create

            # Tools
            for tool_name, count in tool_calls_in_session.items():
                ts_entry = tools_stats.setdefault(tool_name, {"calls": 0, "sessions": set()})
                ts_entry["calls"] += count
                ts_entry["sessions"].add(session_id)

            total_sessions.add(session_id)

        except Exception as e:
            continue

    # Convert sets to counts
    for d in daily.values():
        d["sessions"] = len(d.pop("sessions", set()))
    for p in projects.values():
        p["sessions"] = len(p.pop("sessions", set()))
    for ts_entry in tools_stats.values():
        ts_entry["sessions"] = len(ts_entry.pop("sessions", set()))

    elapsed = time.time() - t0
    print(f"  [Codex Scanner] 扫描完成: {file_count} 文件, {total_messages} 消息, "
          f"{len(total_sessions)} 会话, {total_tokens} tokens ({elapsed:.1f}s)")

    total_input = sum(m["input"] for m in models.values())
    total_output = sum(m["output"] for m in models.values())
    total_cache_read = sum(m["cache_read"] for m in models.values())
    total_cache_create = sum(m["cache_create"] for m in models.values())

    result = {
        "daily": daily,
        "models": models,
        "projects": projects,
        "tools_stats": tools_stats,
        "total_messages": total_messages,
        "total_sessions": len(total_sessions),
        "total_tokens": total_tokens,
        "total_input": total_input,
        "total_output": total_output,
        "total_cache_read": total_cache_read,
        "total_cache_create": total_cache_create,
        "source": "codex",
    }

    with _codex_lock:
        _codex_cache["data"] = result
        _codex_cache["time"] = time.time()

    return result


def _merge_codex_into_scan(claude_scan, codex_scan):
    """Merge Codex scan data into Claude scan data"""
    if not codex_scan:
        return claude_scan

    result = dict(claude_scan)

    # Merge totals
    result["total_messages"] += codex_scan.get("total_messages", 0)
    result["total_sessions"] += codex_scan.get("total_sessions", 0)
    result["total_tokens"] += codex_scan.get("total_tokens", 0)
    result["total_input"] = result.get("total_input", 0) + codex_scan.get("total_input", 0)
    result["total_output"] = result.get("total_output", 0) + codex_scan.get("total_output", 0)
    result["total_cache_read"] = result.get("total_cache_read", 0) + codex_scan.get("total_cache_read", 0)
    result["total_cache_create"] = result.get("total_cache_create", 0) + codex_scan.get("total_cache_create", 0)

    # Merge models
    merged_models = dict(result.get("models", {}))
    for model, v in codex_scan.get("models", {}).items():
        if model not in merged_models:
            merged_models[model] = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0}
        for k in ("input", "output", "cache_read", "cache_create", "calls"):
            merged_models[model][k] += v.get(k, 0)
        if "context_window" in v:
            merged_models[model]["context_window"] = v["context_window"]
    result["models"] = merged_models

    # Merge daily
    merged_daily = dict(result.get("daily", {}))
    for date, d in codex_scan.get("daily", {}).items():
        if date not in merged_daily:
            merged_daily[date] = {"messages": 0, "sessions": 0, "tools": 0, "tokens": {}}
        merged_daily[date]["messages"] += d.get("messages", 0)
        merged_daily[date]["sessions"] += d.get("sessions", 0)
        merged_daily[date]["tools"] += d.get("tools", 0)
        for model, tdata in d.get("tokens", {}).items():
            t_model = merged_daily[date].setdefault("tokens", {}).setdefault(model, {
                "input": 0, "output": 0, "cache_read": 0, "cache_create": 0
            })
            for k in ("input", "output", "cache_read", "cache_create"):
                t_model[k] += tdata.get(k, 0)
    result["daily"] = merged_daily

    # Merge projects (keep codex projects separate with source tag)
    merged_projects = dict(result.get("projects", {}))
    for proj_name, p in codex_scan.get("projects", {}).items():
        key = "codex:" + proj_name
        merged_projects[key] = dict(p)
        merged_projects[key]["source"] = "codex"
    result["projects"] = merged_projects

    # Merge tools
    merged_tools = dict(result.get("tools_stats", {}))
    for tool_name, t in codex_scan.get("tools_stats", {}).items():
        if tool_name not in merged_tools:
            merged_tools[tool_name] = {"calls": 0, "sessions": 0}
        merged_tools[tool_name]["calls"] += t.get("calls", 0)
        merged_tools[tool_name]["sessions"] += t.get("sessions", 0)
    result["tools_stats"] = merged_tools

    # Recalculate cache hit rate
    total_all_input = result["total_input"] + result["total_cache_read"] + result["total_cache_create"]
    result["cache_hit_rate"] = round(result["total_cache_read"] / total_all_input * 100, 1) if total_all_input > 0 else 0

    return result


def _find_codex_session_file(session_id):
    """Find a Codex session JSONL file by session ID"""
    for search_dir in [CODEX_SESSIONS_DIR, CODEX_ARCHIVED_DIR]:
        if not search_dir.exists():
            continue
        for jsonl_file in search_dir.rglob("rollout-*.jsonl"):
            # Check if session_id appears in filename
            if session_id in jsonl_file.name:
                return jsonl_file
            # Check inside file
            try:
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f):
                        if i > 5:
                            break
                        line = line.strip()
                        if not line:
                            continue
                        evt = json.loads(line)
                        if evt.get("type") == "session_meta":
                            if evt.get("payload", {}).get("id") == session_id:
                                return jsonl_file
            except Exception:
                continue
    return None


def _parse_codex_session(jsonl_path):
    """Parse a Codex session JSONL file into the same event timeline format as Claude"""
    events_out = []
    models_seen = set()
    tools_summary = {}
    total_cost = 0.0
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_create = 0
    msg_count = 0
    first_ts = None
    last_ts = None
    session_id = ""
    model = _read_codex_model()

    try:
        raw_events = []
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        last_token_usage = None

        for evt in raw_events:
            evt_type = evt.get("type", "")
            ts = evt.get("timestamp", "")

            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

            if evt_type == "session_meta":
                session_id = evt.get("payload", {}).get("id", "")

            elif evt_type == "turn_context":
                m = evt.get("payload", {}).get("model", "")
                if m:
                    model = m
                    models_seen.add(m)

            elif evt_type == "event_msg":
                payload = evt.get("payload", {})
                sub_type = payload.get("type", "")

                if sub_type == "user_message":
                    msg_count += 1
                    content = payload.get("message", "")
                    events_out.append({
                        "type": "user",
                        "timestamp": ts,
                        "content": (content or "")[:500],
                    })

                elif sub_type == "token_count":
                    info = payload.get("info")
                    if info and isinstance(info, dict):
                        tu = info.get("total_token_usage")
                        if tu:
                            last_token_usage = tu

            elif evt_type == "response_item":
                payload = evt.get("payload", {})
                if payload.get("type") == "message":
                    # Assistant message
                    content_blocks = payload.get("content", [])
                    text_parts = []
                    if isinstance(content_blocks, list):
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "output_text":
                                text_parts.append(block.get("text", ""))
                    content_text = " ".join(text_parts)
                    if content_text.strip():
                        events_out.append({
                            "type": "assistant",
                            "timestamp": ts,
                            "content": content_text,
                            "model": model,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "cost_usd": 0,
                            "tools_used": [],
                        })

                elif payload.get("type") == "function_call":
                    tool_name = payload.get("name", "unknown")
                    tools_summary[tool_name] = tools_summary.get(tool_name, 0) + 1
                    events_out.append({
                        "type": "assistant",
                        "timestamp": ts,
                        "content": "",
                        "model": model,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cost_usd": 0,
                        "tools_used": [tool_name],
                    })

        # Apply cumulative token usage from last token_count
        if last_token_usage:
            total_input = last_token_usage.get("input_tokens", 0) or 0
            total_cache_read = last_token_usage.get("cached_input_tokens", 0) or 0
            total_output = last_token_usage.get("output_tokens", 0) or 0
            total_cost = _calc_cost(model, total_input, total_output, total_cache_read, 0)

    except Exception as e:
        return {"error": str(e)}

    duration_ms = 0
    if first_ts and last_ts:
        dt_first = parse_iso_ts(first_ts)
        dt_last = parse_iso_ts(last_ts)
        if dt_first and dt_last:
            duration_ms = int((dt_last - dt_first).total_seconds() * 1000)

    return {
        "session_id": session_id or jsonl_path.stem,
        "events": events_out,
        "source": "codex",
        "stats": {
            "messages": msg_count,
            "duration_ms": duration_ms,
            "total_cost": round(total_cost, 4),
            "total_input": total_input,
            "total_output": total_output,
            "total_cache_read": total_cache_read,
            "total_cache_create": total_cache_create,
            "models": list(models_seen) if models_seen else [model],
            "tools_summary": tools_summary,
            "files_touched": {},
        }
    }


# ============================================================
# History 解析
# ============================================================
def _load_history():
    """解析 history.jsonl"""
    now = time.time()
    try:
        mtime = HISTORY_FILE.stat().st_mtime
    except Exception:
        return []

    if _history_cache["data"] and (now - _history_cache["time"]) < HISTORY_TTL and _history_cache["mtime"] == mtime:
        return _history_cache["data"]

    entries = []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    _history_cache["data"] = entries
    _history_cache["time"] = now
    _history_cache["mtime"] = mtime
    return entries


# ============================================================
# Live（今日）扫描
# ============================================================
def _scan_today():
    """扫描今日修改的 JSONL 文件，提取 API 调用"""
    now = time.time()
    if _live_cache["data"] and (now - _live_cache["time"]) < LIVE_TTL:
        return _live_cache["data"]

    today = datetime.date.today()
    today_str = today.isoformat()
    calls = []
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0, "duration_ms": 0}

    if not PROJECTS_DIR.exists():
        return {"calls": calls, "totals": totals}

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                mtime = datetime.date.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime != today:
                    continue
            except Exception:
                continue

            proj_friendly = friendly_project_name(project_dir.name)
            try:
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            evt = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if evt.get("type") != "assistant" or "message" not in evt:
                            continue

                        ts = evt.get("timestamp", "")
                        if not ts or not ts.startswith(today_str):
                            continue

                        msg = evt.get("message", {})
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage", {})
                        model = msg.get("model", "unknown")

                        inp = usage.get("input_tokens", 0) or 0
                        out = usage.get("output_tokens", 0) or 0
                        cr = usage.get("cache_read_input_tokens", 0) or 0
                        cc = usage.get("cache_creation_input_tokens", 0) or 0

                        if inp == 0 and out == 0:
                            continue  # 跳过空事件

                        row_cost = round(_calc_cost(model, inp, out, cr, cc), 6)
                        calls.append({
                            "timestamp": ts,
                            "model": model,
                            "project": proj_friendly,
                            "input_tokens": inp,
                            "output_tokens": out,
                            "cache_read": cr,
                            "cache_create": cc,
                            "cost_usd": row_cost,
                            "source": "claude",
                            "entrypoint": evt.get("entrypoint", "cli"),
                        })
                        totals["input"] += inp
                        totals["output"] += out
                        totals["cache_read"] += cr
                        totals["cache_create"] += cc
                        totals["calls"] += 1
                        totals["cost"] = totals.get("cost", 0) + row_cost
            except Exception:
                continue

    calls.sort(key=lambda x: x["timestamp"], reverse=True)
    result = {"calls": calls, "totals": totals}
    _live_cache["data"] = result
    _live_cache["time"] = time.time()
    return result


def _scan_codex_today():
    """Scan today's Codex session files for live view"""
    if not _codex_enabled():
        return None

    today = datetime.date.today()
    today_str = today.isoformat()
    calls = []
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0, "cost": 0}
    default_model = _read_codex_model()

    for search_dir in [CODEX_SESSIONS_DIR, CODEX_ARCHIVED_DIR]:
        if not search_dir.exists():
            continue
        for jsonl_file in search_dir.rglob("rollout-*.jsonl"):
            try:
                mtime = datetime.date.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime != today:
                    continue
            except Exception:
                continue

            try:
                events = []
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

                model = default_model
                cwd = ""
                last_token_usage = None
                first_ts = ""

                for evt in events:
                    ts = evt.get("timestamp", "")
                    if ts and not first_ts:
                        first_ts = ts

                    if evt.get("type") == "session_meta":
                        cwd = evt.get("payload", {}).get("cwd", "")
                    elif evt.get("type") == "turn_context":
                        m = evt.get("payload", {}).get("model", "")
                        if m:
                            model = m
                    elif evt.get("type") == "event_msg":
                        payload = evt.get("payload", {})
                        if payload.get("type") == "token_count":
                            info = payload.get("info")
                            if info and isinstance(info, dict):
                                tu = info.get("total_token_usage")
                                if tu:
                                    last_token_usage = tu

                if not first_ts or not first_ts.startswith(today_str):
                    continue

                if last_token_usage:
                    inp = last_token_usage.get("input_tokens", 0) or 0
                    out = last_token_usage.get("output_tokens", 0) or 0
                    cr = last_token_usage.get("cached_input_tokens", 0) or 0
                    if inp == 0 and out == 0:
                        continue

                    proj_friendly = cwd.rstrip("/").split("/")[-1] if cwd else "codex"
                    row_cost = round(_calc_cost(model, inp, out, cr, 0), 6)
                    calls.append({
                        "timestamp": first_ts,
                        "model": model,
                        "project": proj_friendly + " (codex)",
                        "input_tokens": inp,
                        "output_tokens": out,
                        "cache_read": cr,
                        "cache_create": 0,
                        "cost_usd": row_cost,
                        "source": "codex",
                    })
                    totals["input"] += inp
                    totals["output"] += out
                    totals["cache_read"] += cr
                    totals["calls"] += 1
                    totals["cost"] += row_cost
            except Exception:
                continue

    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"calls": calls, "totals": totals} if calls else None


# ============================================================
# Logs 查询（支持过滤、分页）
# ============================================================
_logs_cache = {"data": None, "time": 0}
LOGS_TTL = 30


def _relative_time(ts_str):
    """生成相对时间字符串"""
    try:
        dt = parse_iso_ts(ts_str)
        if not dt:
            return ts_str
        now = datetime.datetime.now(datetime.timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        diff = (now - dt).total_seconds()
        if diff < 60:
            return f"{int(diff)} 秒前"
        elif diff < 3600:
            return f"{int(diff // 60)} 分钟前"
        elif diff < 86400:
            return f"{int(diff // 3600)} 小时前"
        else:
            return f"{int(diff // 86400)} 天前"
    except Exception:
        return ts_str


def _parse_iso(ts_str):
    """ISO 时间戳 → datetime（用于计算时间差）"""
    try:
        s = ts_str
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


def _scan_all_logs(force=False):
    """扫描所有 JSONL 文件，构建完整的调用日志列表
    耗时数据来源：
    - system/turn_duration 事件的 durationMs（官方数据）
    - user → assistant 时间戳差（作为 TTFT 近似）
    """
    now = time.time()
    if not force and _logs_cache["data"] and (now - _logs_cache["time"]) < LOGS_TTL:
        return _logs_cache["data"]

    calls = []
    if not PROJECTS_DIR.exists():
        return calls

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        proj_friendly = friendly_project_name(project_dir.name)
        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                # 收集所有事件
                events = []
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

                # 两遍处理：
                # 1) 收集 turn_duration 事件，按 parentUuid 索引
                turn_durations = {}  # parentUuid → durationMs
                for evt in events:
                    if evt.get("type") == "system" and evt.get("subtype") == "turn_duration":
                        parent = evt.get("parentUuid", "")
                        if parent:
                            turn_durations[parent] = evt.get("durationMs", 0)

                # 2) 处理 user/assistant 事件
                last_user_ts = None
                last_user_uuid = None

                for evt in events:
                    t = evt.get("type", "")
                    ts = evt.get("timestamp", "")

                    if t == "user":
                        last_user_ts = _parse_iso(ts)
                        last_user_uuid = evt.get("uuid", "")

                    elif t == "assistant" and "message" in evt:
                        msg = evt.get("message", {})
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage", {})
                        model = msg.get("model", "unknown")
                        inp = usage.get("input_tokens", 0) or 0
                        out = usage.get("output_tokens", 0) or 0
                        cr = usage.get("cache_read_input_tokens", 0) or 0
                        cc = usage.get("cache_creation_input_tokens", 0) or 0

                        if inp == 0 and out == 0:
                            continue

                        # TTFT: user → 第一个 assistant 的时间差
                        ttft_ms = None
                        assistant_dt = _parse_iso(ts)
                        if last_user_ts and assistant_dt:
                            ttft_ms = int((assistant_dt - last_user_ts).total_seconds() * 1000)
                            if ttft_ms < 0:
                                ttft_ms = None

                        # 总耗时: 优先用官方 turn_duration
                        duration_ms = None
                        evt_uuid = evt.get("uuid", "")
                        parent_uuid = evt.get("parentUuid", "")
                        # turn_duration 的 parentUuid 指向触发它的 assistant 消息
                        if evt_uuid in turn_durations:
                            duration_ms = turn_durations[evt_uuid]
                        elif parent_uuid in turn_durations:
                            duration_ms = turn_durations[parent_uuid]
                        # 回退：用时间戳差
                        if duration_ms is None and last_user_ts and assistant_dt:
                            duration_ms = int((assistant_dt - last_user_ts).total_seconds() * 1000)
                            if duration_ms < 0:
                                duration_ms = None

                        calls.append({
                            "timestamp": ts,
                            "model": model,
                            "project": proj_friendly,
                            "input_tokens": inp,
                            "output_tokens": out,
                            "cache_read": cr,
                            "cache_create": cc,
                            "status": 200,
                            "ttft_ms": ttft_ms,
                            "duration_ms": duration_ms,
                            "cost_usd": round(_calc_cost(model, inp, out, cr, cc), 6),
                            "source": "claude",
                            "entrypoint": evt.get("entrypoint", "cli"),
                        })
            except Exception:
                continue

    calls.sort(key=lambda x: x["timestamp"], reverse=True)
    _logs_cache["data"] = calls
    _logs_cache["time"] = time.time()
    return calls


# _codex_logs_cache defined near top with other caches
CODEX_LOGS_TTL = 30


def _scan_codex_logs():
    """Scan Codex session files to produce log entries matching Claude format"""
    now = time.time()
    if _codex_logs_cache["data"] is not None and (now - _codex_logs_cache["time"]) < CODEX_LOGS_TTL:
        return _codex_logs_cache["data"]

    if not _codex_enabled():
        return []

    calls = []
    default_model = _read_codex_model()

    for search_dir in [CODEX_SESSIONS_DIR, CODEX_ARCHIVED_DIR]:
        if not search_dir.exists():
            continue
        for jsonl_file in search_dir.rglob("rollout-*.jsonl"):
            try:
                events = []
                with open(jsonl_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

                model = default_model
                cwd = ""
                first_ts = ""
                last_ts = ""
                last_token_usage = None

                for evt in events:
                    ts = evt.get("timestamp", "")
                    if ts:
                        if not first_ts:
                            first_ts = ts
                        last_ts = ts

                    if evt.get("type") == "session_meta":
                        cwd = evt.get("payload", {}).get("cwd", "")
                    elif evt.get("type") == "turn_context":
                        m = evt.get("payload", {}).get("model", "")
                        if m:
                            model = m
                    elif evt.get("type") == "event_msg":
                        payload = evt.get("payload", {})
                        if payload.get("type") == "token_count":
                            info = payload.get("info")
                            if info and isinstance(info, dict):
                                tu = info.get("total_token_usage")
                                if tu:
                                    last_token_usage = tu

                if not last_token_usage:
                    continue

                inp = last_token_usage.get("input_tokens", 0) or 0
                out = last_token_usage.get("output_tokens", 0) or 0
                cr = last_token_usage.get("cached_input_tokens", 0) or 0
                if inp == 0 and out == 0:
                    continue

                proj_friendly = cwd.rstrip("/").split("/")[-1] if cwd else "codex"
                row_cost = round(_calc_cost(model, inp, out, cr, 0), 6)

                # Duration from first to last timestamp
                duration_ms = None
                if first_ts and last_ts:
                    t1 = _parse_iso(first_ts)
                    t2 = _parse_iso(last_ts)
                    if t1 and t2:
                        duration_ms = int((t2 - t1).total_seconds() * 1000)

                calls.append({
                    "timestamp": first_ts,
                    "model": model,
                    "project": proj_friendly + " (codex)",
                    "input_tokens": inp,
                    "output_tokens": out,
                    "cache_read": cr,
                    "cache_create": 0,
                    "status": 200,
                    "ttft_ms": None,
                    "duration_ms": duration_ms,
                    "cost_usd": row_cost,
                    "source": "codex",
                })
            except Exception:
                continue

    calls.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    _codex_logs_cache["data"] = calls
    _codex_logs_cache["time"] = time.time()
    return calls


# ============================================================
# Claude.ai Usage API
# ============================================================
def _fetch_claude_usage():
    """Fetch usage data from claude.ai via Swift script (bypasses Cloudflare)"""
    now = time.time()
    if _claude_usage_cache["data"] and (now - _claude_usage_cache["time"]) < CLAUDE_USAGE_TTL:
        return _claude_usage_cache["data"]

    swift_path = DASHBOARD_DIR / "fetch-usage.swift"
    if not swift_path.exists():
        return {"error": "swift_script_missing", "stale": True}

    try:
        result = subprocess.run(
            ["swift", str(swift_path)],
            capture_output=True, text=True, timeout=15,
            cwd=str(DASHBOARD_DIR)
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            _claude_usage_cache["data"] = data
            _claude_usage_cache["time"] = now
            return data
        else:
            err = result.stderr.strip() or result.stdout.strip() or "unknown"
            print(f"  [Claude Usage] Swift error: {err}")
            return {"error": err, "stale": True}
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "stale": True}
    except Exception as e:
        print(f"  [Claude Usage] Failed: {e}")
        return {"error": str(e), "stale": True}


# ============================================================
# Claude.ai Web Conversations
# ============================================================
def _fetch_web_conversations():
    """Fetch conversation list from claude.ai via Swift script (cached)"""
    now = time.time()
    if _web_conv_cache["data"] and (now - _web_conv_cache["time"]) < WEB_CONV_TTL:
        return _web_conv_cache["data"]

    swift_path = DASHBOARD_DIR / "fetch-web-conversations.swift"
    if not swift_path.exists():
        return {"error": "swift_script_missing"}

    # Check if session_key is configured
    config = _load_config()
    if not config.get("claude_session_key") or not config.get("claude_org_id"):
        return {"error": "not_configured"}

    try:
        result = subprocess.run(
            ["swift", str(swift_path), "list"],
            capture_output=True, text=True, timeout=20,
            cwd=str(DASHBOARD_DIR)
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            if isinstance(data, dict) and data.get("error"):
                return data
            # data is a list of conversations from the API
            conversations = []
            if isinstance(data, list):
                for c in data:
                    conversations.append({
                        "uuid": c.get("uuid", ""),
                        "name": c.get("name", ""),
                        "model": c.get("model") or c.get("default_model") or "",
                        "created_at": c.get("created_at", ""),
                        "updated_at": c.get("updated_at", ""),
                        "summary": c.get("summary", ""),
                        "message_count": c.get("message_count"),
                    })
            result_data = conversations
            _web_conv_cache["data"] = result_data
            _web_conv_cache["time"] = now
            return result_data
        else:
            err = result.stderr.strip() or result.stdout.strip() or "unknown"
            print(f"  [Web Conv] Swift error: {err}")
            return {"error": err}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        print(f"  [Web Conv] Failed: {e}")
        return {"error": str(e)}


def _fetch_web_conversation_detail(uuid):
    """Fetch a single conversation with messages from claude.ai"""
    swift_path = DASHBOARD_DIR / "fetch-web-conversations.swift"
    if not swift_path.exists():
        return {"error": "swift_script_missing"}

    config = _load_config()
    if not config.get("claude_session_key") or not config.get("claude_org_id"):
        return {"error": "not_configured"}

    # Validate UUID
    import re as re_mod
    if not re_mod.match(r'^[0-9a-fA-F-]+$', uuid):
        return {"error": "invalid_uuid"}

    try:
        result = subprocess.run(
            ["swift", str(swift_path), "detail", uuid],
            capture_output=True, text=True, timeout=20,
            cwd=str(DASHBOARD_DIR)
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            if isinstance(data, dict) and data.get("error"):
                return data

            # Parse the conversation detail
            messages = []
            chat_messages = data.get("chat_messages", [])
            for i, msg in enumerate(chat_messages):
                sender = msg.get("sender", "")
                text = ""
                # Extract text from content blocks
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                    text = "\n".join(text_parts)
                elif isinstance(content, str):
                    text = content
                # Also check for top-level text field
                if not text and msg.get("text"):
                    text = msg["text"]

                messages.append({
                    "sender": sender,
                    "text": text,
                    "created_at": msg.get("created_at", ""),
                    "updated_at": msg.get("updated_at", ""),
                    "uuid": msg.get("uuid", ""),
                    "index": i,
                })

            return {
                "name": data.get("name", ""),
                "model": data.get("model") or data.get("default_model") or "",
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(messages),
                "messages": messages,
            }
        else:
            err = result.stderr.strip() or result.stdout.strip() or "unknown"
            return {"error": err}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# HTTP Handler
# ============================================================
class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CLAUDE_DIR / "dashboard"), **kwargs)

    def log_message(self, format, *args):
        print(f"  [{self.command}] {format % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        routes = {
            "/api/status": self.api_status,
            "/api/overview": self.api_overview,
            "/api/daily": self.api_daily,
            "/api/models": self.api_models,
            "/api/projects": self.api_projects,
            "/api/sessions": self.api_sessions,
            "/api/session-detail": self.api_session_detail,
            "/api/hourly": self.api_hourly,
            "/api/live": self.api_live,
            "/api/logs": self.api_logs,
            "/api/claude-usage": self.api_claude_usage,
            "/api/tools": self.api_tools,
            "/api/export": self.api_export,
            "/api/rhythm": self.api_rhythm,
            "/api/session-chain": self.api_session_chain,
            "/api/hourly-trend": self.api_hourly_trend,
            "/api/web-conversations": self.api_web_conversations,
            "/api/web-conversation-detail": self.api_web_conversation_detail,
            "/api/today-breakdown": self.api_today_breakdown,
            "/api/mcp-stats": self.api_mcp_stats,
            "/api/mcp-trend": self.api_mcp_trend,
            "/api/rate-prediction": self.api_rate_prediction,
            "/api/efficiency": self.api_efficiency,
            "/api/insights": self.api_insights,
            "/api/budget": self.api_budget_get,
            "/api/report": self.api_report,
            "/api/git-stats": self.api_git_stats,
            "/api/accounts": self.api_accounts,
            "/api/plugins": self.api_plugins,
            "/api/settings": self.api_settings_get,
        }

        handler = routes.get(path)
        if handler:
            try:
                handler(params)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            # 静态文件（index.html 等）— 禁用缓存确保最新版本
            if path == "/":
                self.path = "/index.html"
            # Strip query params for file serving
            self.path = path
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

    def end_headers(self):
        # Disable caching for development
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/settings":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8")) if body else {}
                self.api_settings_post(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/budget":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8")) if body else {}
                self.api_budget_post(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/plugin-toggle":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8")) if body else {}
                plugin_name = data.get("name", "")
                enabled = data.get("enabled", False)
                if not plugin_name:
                    self.send_json({"error": "name required"}, 400)
                else:
                    config = _load_config()
                    plugins_cfg = config.setdefault("plugins", {})
                    plugins_cfg.setdefault(plugin_name, {})["enabled"] = enabled
                    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    self.send_json({"ok": True, "name": plugin_name, "enabled": enabled})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/webhooks":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8")) if body else {}
                self.api_webhooks_post(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            self.send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # --- API 实现 ---

    def api_status(self, params):
        """实时使用率 + 今日统计"""
        data = {
            "utilization": 0,
            "resets_at": "",
            "profile_name": "Unknown",
            "timestamp": 0,
            "stale": True,
            "today_messages": 0,
            "today_sessions": 0,
        }

        # 解析 .statusline-usage-cache
        try:
            with open(USAGE_CACHE_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k == "UTILIZATION":
                            data["utilization"] = int(v)
                        elif k == "RESETS_AT":
                            data["resets_at"] = v
                        elif k == "PROFILE_NAME":
                            data["profile_name"] = v
                        elif k == "TIMESTAMP":
                            data["timestamp"] = int(v)
                            data["stale"] = (time.time() - int(v)) > 300
        except Exception:
            pass

        # 今日统计（从 history.jsonl 快速统计）
        today_str = datetime.date.today().isoformat()
        history = _load_history()
        today_sessions = set()
        today_msgs = 0
        for entry in history:
            ts = entry.get("timestamp", 0)
            if ms_to_date(ts) == today_str:
                today_msgs += 1
                today_sessions.add(entry.get("sessionId", ""))
        data["today_messages"] = today_msgs
        data["today_sessions"] = len(today_sessions)

        self.send_json(data)

    def api_overview(self, params):
        """概览卡片（聚合本地 + 远程 + Codex）"""
        force = "refresh" in params
        source = params.get("source", ["all"])[0]
        if force:
            _clear_all_caches()
        # Always scan all sources, then filter — keeps cache stable
        scan = copy.deepcopy(_scan_all_projects(force=force))
        codex_scan = _scan_codex(force=force) if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        # Tag models with source for filtering
        claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
        for m in scan.get("models", {}):
            scan["models"][m]["source"] = "claude" if m in claude_models else "codex"
        # Filter by source if needed
        if source == "codex":
            scan["models"] = {m:v for m,v in scan.get("models",{}).items() if v.get("source") == "codex"}
        elif source == "claude":
            scan["models"] = {m:v for m,v in scan.get("models",{}).items() if v.get("source") == "claude"}
        # Recalculate totals from filtered models
        if source != "all":
            scan["total_input"] = sum(v.get("input",0) for v in scan["models"].values())
            scan["total_output"] = sum(v.get("output",0) for v in scan["models"].values())
            scan["total_cache_read"] = sum(v.get("cache_read",0) for v in scan["models"].values())
            scan["total_cache_create"] = sum(v.get("cache_create",0) for v in scan["models"].values())
            scan["total_tokens"] = scan["total_input"] + scan["total_output"] + scan["total_cache_read"] + scan["total_cache_create"]
            tai = scan["total_input"] + scan["total_cache_read"] + scan["total_cache_create"]
            scan["cache_hit_rate"] = round(scan["total_cache_read"] / tai * 100, 1) if tai > 0 else 0
        today_str = datetime.date.today().isoformat()
        today_data = scan["daily"].get(today_str, {})

        # Compute RPM, TPM, avg_duration from recent logs (filtered by source)
        try:
            logs = _scan_all_logs()
            if source != "all":
                logs = [c for c in logs if c.get("source", "claude") == source]
            now = datetime.datetime.now(datetime.timezone.utc)
            recent_5m = [c for c in logs if c.get("timestamp") and
                         (now - parse_iso_ts(c["timestamp"])).total_seconds() < 300]
            rpm = round(len(recent_5m) / 5, 1) if recent_5m else 0
            tpm_val = sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) +
                         c.get("cache_read", 0) + c.get("cache_create", 0) for c in recent_5m)
            tpm = round(tpm_val / 5) if recent_5m else 0
            durations = [c["duration_ms"] for c in logs[:100] if c.get("duration_ms")]
            avg_duration = round(sum(durations) / len(durations)) if durations else 0
            avg_ttft = 0
            ttfts = [c["ttft_ms"] for c in logs[:100] if c.get("ttft_ms")]
            avg_ttft = round(sum(ttfts) / len(ttfts)) if ttfts else 0
        except Exception:
            rpm, tpm, avg_duration, avg_ttft = 0, 0, 0, 0

        # Burn rate: tokens per minute over last 30 minutes
        burn_rate_tpm = 0
        burn_rate_cost_per_hour = 0.0
        estimated_5h_depletion = 0
        try:
            recent_30m = [c for c in logs if c.get("timestamp") and
                          (now - parse_iso_ts(c["timestamp"])).total_seconds() < 1800]
            if recent_30m:
                total_tok_30m = sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) +
                                   c.get("cache_read", 0) + c.get("cache_create", 0)
                                   for c in recent_30m)
                burn_rate_tpm = round(total_tok_30m / 30)
                total_cost_30m = sum(c.get("cost_usd", 0) for c in recent_30m)
                burn_rate_cost_per_hour = round(total_cost_30m * 2, 4)  # 30m -> 1h
                # Estimate minutes until 5h quota depletes
                # Use current utilization from status cache
                cur_util = 0
                try:
                    with open(USAGE_CACHE_FILE, "r") as uf:
                        for uline in uf:
                            uline = uline.strip()
                            if uline.startswith("UTILIZATION="):
                                cur_util = int(uline.split("=", 1)[1])
                except Exception:
                    pass
                remaining_pct = max(0, 100 - cur_util)
                if burn_rate_tpm > 0 and remaining_pct > 0:
                    # Very rough: remaining % of 5h window at current rate
                    # 5h = 300 min, if burn_rate_tpm is the consumption rate
                    estimated_5h_depletion = round(remaining_pct / 100 * 300)
                elif remaining_pct <= 0:
                    estimated_5h_depletion = 0
                else:
                    estimated_5h_depletion = 300  # full window remaining, no activity
        except Exception:
            pass

        local = {
            "total_messages": scan["total_messages"],
            "total_sessions": scan["total_sessions"],
            "total_tokens": scan["total_tokens"],
            "total_input": scan.get("total_input", 0),
            "total_output": scan.get("total_output", 0),
            "total_cache_read": scan.get("total_cache_read", 0),
            "total_cache_create": scan.get("total_cache_create", 0),
            "cache_hit_rate": scan.get("cache_hit_rate", 0),
            "total_projects": len(scan["projects"]),
            "total_models": len(scan["models"]),
            "today_messages": today_data.get("messages", 0) if source == "all" else len([c for c in logs if c.get("timestamp","").startswith(today_str)]),
            "today_sessions": today_data.get("sessions", 0),
            "today_tools": today_data.get("tools", 0),
            "rpm": rpm,
            "tpm": tpm,
            "avg_duration_ms": avg_duration,
            "avg_ttft_ms": avg_ttft,
            "burn_rate_tokens_per_min": burn_rate_tpm,
            "burn_rate_cost_per_hour": burn_rate_cost_per_hour,
            "estimated_5h_depletion": estimated_5h_depletion,
        }

        # Calculate total cost across all models
        total_cost = 0.0
        for m_name, m_data in scan.get("models", {}).items():
            total_cost += _calc_cost(
                m_name,
                m_data.get("input", 0),
                m_data.get("output", 0),
                m_data.get("cache_read", 0),
                m_data.get("cache_create", 0),
            )
        local["total_cost_usd"] = round(total_cost, 4)

        # 聚合远程 (always aggregate, remote uses 60s cache so switching is fast)
        remotes = _get_active_remotes()
        remote_overviews = []
        for r in remotes:
            remote_path = "/api/overview" + (f"?source={source}" if source != "all" else "")
            rd = _fetch_remote_cached(r["url"], remote_path, r.get("token"))
            if rd:
                remote_overviews.append(rd)
        result = _merge_overview(local, remote_overviews) if remote_overviews else local
        result["remote_count"] = len(remote_overviews)

        # Cost already computed from local models scan above.
        # For remote cost, approximate from merged overview totals (avoids slow extra API call).
        # Remote tokens are added to result by _merge_overview already.
        # The local cost is accurate per-model; we keep it as-is since models API has per-model cost.

        self.send_json(result)

    def api_daily(self, params):
        """每日趋势"""
        days = int(params.get("days", ["30"])[0])
        source = params.get("source", ["all"])[0]
        # Always scan all, then filter
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        daily = scan["daily"]

        # Filter daily tokens by source
        if source != "all":
            claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
            for date_key, d_data in daily.items():
                if "tokens" in d_data:
                    if source == "claude":
                        d_data["tokens"] = {m:v for m,v in d_data["tokens"].items() if m in claude_models}
                    elif source == "codex":
                        d_data["tokens"] = {m:v for m,v in d_data["tokens"].items() if m not in claude_models}

        # 按日期排序，取最近 N 天
        sorted_dates = sorted(daily.keys())[-days:]

        activity = []
        tokens = []
        for date in sorted_dates:
            d = daily[date]
            activity.append({
                "date": date,
                "messages": d["messages"],
                "sessions": d["sessions"],
                "tools": d["tools"],
            })
            tokens.append({
                "date": date,
                "byModel": d.get("tokens", {}),
            })

        # 聚合远程
        remotes = _get_active_remotes()
        remote_daily = [_fetch_remote_cached(r["url"], f"/api/daily?days={days}" + (f"&source={source}" if source != "all" else ""), r.get("token")) for r in remotes]
        remote_daily = [rd for rd in remote_daily if rd]
        if remote_daily:
            activity, tokens = _merge_daily(activity, tokens, remote_daily)
            activity = activity[-days:]
            tokens = tokens[-days:]

        # Weekly comparison: this week vs last week
        today = datetime.date.today()
        dow = today.weekday()  # 0=Mon
        this_week_start = (today - datetime.timedelta(days=dow)).isoformat()
        last_week_start = (today - datetime.timedelta(days=dow + 7)).isoformat()
        last_week_end = (today - datetime.timedelta(days=dow + 1)).isoformat()

        this_week = {"messages": 0, "tokens": 0, "cost": 0.0, "sessions": 0}
        last_week = {"messages": 0, "tokens": 0, "cost": 0.0, "sessions": 0}

        all_daily = scan["daily"]
        for date_str, d_data in all_daily.items():
            if date_str >= this_week_start:
                this_week["messages"] += d_data.get("messages", 0)
                this_week["sessions"] += d_data.get("sessions", 0)
                for m_name, t_data in d_data.get("tokens", {}).items():
                    tok = (t_data.get("input", 0) + t_data.get("output", 0) +
                           t_data.get("cache_read", 0) + t_data.get("cache_create", 0))
                    this_week["tokens"] += tok
                    this_week["cost"] += _calc_cost(
                        m_name, t_data.get("input", 0), t_data.get("output", 0),
                        t_data.get("cache_read", 0), t_data.get("cache_create", 0))
            elif last_week_start <= date_str <= last_week_end:
                last_week["messages"] += d_data.get("messages", 0)
                last_week["sessions"] += d_data.get("sessions", 0)
                for m_name, t_data in d_data.get("tokens", {}).items():
                    tok = (t_data.get("input", 0) + t_data.get("output", 0) +
                           t_data.get("cache_read", 0) + t_data.get("cache_create", 0))
                    last_week["tokens"] += tok
                    last_week["cost"] += _calc_cost(
                        m_name, t_data.get("input", 0), t_data.get("output", 0),
                        t_data.get("cache_read", 0), t_data.get("cache_create", 0))

        this_week["cost"] = round(this_week["cost"], 2)
        last_week["cost"] = round(last_week["cost"], 2)

        change_pct = {}
        for k in ("messages", "tokens", "cost", "sessions"):
            if last_week[k] > 0:
                change_pct[k] = round((this_week[k] - last_week[k]) / last_week[k] * 100, 1)
            else:
                change_pct[k] = 100.0 if this_week[k] > 0 else 0.0

        weekly_comparison = {
            "this_week": this_week,
            "last_week": last_week,
            "change_pct": change_pct,
        }

        # Daily comparison: today vs yesterday
        today_str = today.isoformat()
        yesterday_str = (today - datetime.timedelta(days=1)).isoformat()
        today_d = {"messages": 0, "tokens": 0, "cost": 0.0, "sessions": 0}
        yest_d = {"messages": 0, "tokens": 0, "cost": 0.0, "sessions": 0}
        for ds, target in [(today_str, today_d), (yesterday_str, yest_d)]:
            dd = all_daily.get(ds, {})
            target["messages"] = dd.get("messages", 0)
            target["sessions"] = dd.get("sessions", 0)
            for mn, td in dd.get("tokens", {}).items():
                target["tokens"] += (td.get("input",0)+td.get("output",0)+td.get("cache_read",0)+td.get("cache_create",0))
                target["cost"] += _calc_cost(mn, td.get("input",0), td.get("output",0), td.get("cache_read",0), td.get("cache_create",0))
        today_d["cost"] = round(today_d["cost"], 2)
        yest_d["cost"] = round(yest_d["cost"], 2)
        daily_change = {}
        for k in ("messages", "tokens", "cost", "sessions"):
            if yest_d[k] > 0:
                daily_change[k] = round((today_d[k] - yest_d[k]) / yest_d[k] * 100, 1)
            else:
                daily_change[k] = 100.0 if today_d[k] > 0 else 0.0
        daily_comparison = {"today": today_d, "yesterday": yest_d, "change_pct": daily_change}

        self.send_json({"activity": activity, "tokens": tokens, "weekly_comparison": weekly_comparison, "daily_comparison": daily_comparison})

    def api_models(self, params):
        """模型用量明细（聚合远程 + Codex）"""
        source = params.get("source", ["all"])[0]
        # Always scan all, then filter
        claude_model_names = set(_scan_all_projects(force=False).get("models", {}).keys())
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        models = scan["models"]
        # Tag source
        for m in models:
            models[m]["source"] = "claude" if m in claude_model_names else "codex"
        # Filter by source
        if source == "claude":
            models = {m:v for m,v in models.items() if v.get("source") == "claude"}
        elif source == "codex":
            models = {m:v for m,v in models.items() if v.get("source") == "codex"}
        remotes = _get_active_remotes()
        remote_models = [_fetch_remote_cached(r["url"], "/api/models" + (f"?source={source}" if source != "all" else ""), r.get("token")) for r in remotes]
        models = _merge_models(models, [rd for rd in remote_models if rd])
        # Add cost per model + context window usage
        for m_name, m_data in models.items():
            m_data["cost_usd"] = round(_calc_cost(
                m_name, m_data.get("input", 0), m_data.get("output", 0),
                m_data.get("cache_read", 0), m_data.get("cache_create", 0)
            ), 4)
            # Context window usage
            # Check hardcoded → LiteLLM → default
            ctx_win = CONTEXT_WINDOWS.get(m_name)
            if not ctx_win:
                lp = _get_model_pricing(m_name)
                ctx_win = lp.get("context_window", DEFAULT_CONTEXT_WINDOW) or DEFAULT_CONTEXT_WINDOW
            m_data["context_window"] = ctx_win
            calls = m_data.get("calls", 0)
            if calls > 0:
                avg_input_per_call = (m_data.get("input", 0) + m_data.get("cache_read", 0) +
                                     m_data.get("cache_create", 0)) / calls
                m_data["avg_context_usage_pct"] = round(avg_input_per_call / ctx_win * 100, 1)
            else:
                m_data["avg_context_usage_pct"] = 0
            m_data["provider"] = _model_provider(m_name)
        self.send_json({"models": models})

    def api_projects(self, params):
        """项目用量分布（含 Codex）"""
        source = params.get("source", ["all"])[0]
        if source == "codex":
            codex_scan = _scan_codex()
            scan = codex_scan if codex_scan else {"projects": {}, "models": {}}
            scan.setdefault("projects", {})
            scan.setdefault("models", {})
        else:
            scan = copy.deepcopy(_scan_all_projects())
            if source != "claude":
                codex_scan = _scan_codex()
                if codex_scan:
                    scan = _merge_codex_into_scan(scan, codex_scan)
        # 按 token 总量排序
        sorted_projects = sorted(
            scan["projects"].items(),
            key=lambda x: x[1]["tokens_total"],
            reverse=True
        )
        result = []
        for proj_dir, info in sorted_projects[:20]:
            # Calculate per-project cost from its model breakdown
            proj_cost = 0.0
            for pm_name, pm_data in info.get("models", {}).items():
                proj_cost += _calc_cost(
                    pm_name,
                    pm_data.get("input", 0), pm_data.get("output", 0),
                    pm_data.get("cache_read", 0), pm_data.get("cache_create", 0)
                )
            result.append({
                "dir_name": proj_dir,
                "name": info["friendly_name"],
                "messages": info["messages"],
                "sessions": info["sessions"],
                "tokens_total": info["tokens_total"],
                "cost_usd": round(proj_cost, 4),
                "source": info.get("source", "claude"),
            })
        # 聚合远程
        remotes = _get_active_remotes()
        remote_proj = []
        for r in remotes:
            rd = _fetch_remote_cached(r["url"], "/api/projects" + (f"?source={source}" if source != "all" else ""), r.get("token"))
            if rd:
                rd["_remote_name"] = r.get("name", "cloud")
                remote_proj.append(rd)
        if remote_proj:
            result = _merge_projects(result, remote_proj)
        self.send_json({"projects": result})

    def api_today_breakdown(self, params):
        """Today's usage broken down by model"""
        source = params.get("source", ["all"])[0]
        today_str = datetime.date.today().isoformat()

        # Gather today's log entries from Claude Code logs
        claude_logs = _scan_all_logs()
        today_logs = [c for c in claude_logs if c.get("timestamp", "").startswith(today_str)]

        # Include Codex logs if enabled
        if _codex_enabled():
            codex_logs = _scan_codex_logs()
            codex_today = [c for c in codex_logs if c.get("timestamp", "").startswith(today_str)]
            today_logs.extend(codex_today)

        # Filter by source
        if source == "claude":
            today_logs = [c for c in today_logs if c.get("source", "claude") == "claude"]
        elif source == "codex":
            today_logs = [c for c in today_logs if c.get("source", "claude") == "codex"]

        # Group by model
        model_map = {}  # model -> aggregated stats
        for c in today_logs:
            model = c.get("model", "unknown")
            if model not in model_map:
                model_map[model] = {
                    "model": model,
                    "provider": _model_provider(model),
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read": 0,
                    "cache_create": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "source": c.get("source", "claude"),
                }
            entry = model_map[model]
            entry["calls"] += 1
            inp = c.get("input_tokens", 0) or 0
            out = c.get("output_tokens", 0) or 0
            cr = c.get("cache_read", 0) or 0
            cc = c.get("cache_create", 0) or 0
            entry["input_tokens"] += inp
            entry["output_tokens"] += out
            entry["cache_read"] += cr
            entry["cache_create"] += cc
            entry["total_tokens"] += inp + out + cr + cc
            entry["cost_usd"] += c.get("cost_usd", 0) or _calc_cost(model, inp, out, cr, cc)

        # Round costs
        for entry in model_map.values():
            entry["cost_usd"] = round(entry["cost_usd"], 4)

        # Sort by cost descending
        models_list = sorted(model_map.values(), key=lambda x: -x["cost_usd"])

        total_cost = round(sum(e["cost_usd"] for e in models_list), 4)
        total_calls = sum(e["calls"] for e in models_list)
        total_tokens = sum(e["total_tokens"] for e in models_list)

        self.send_json({
            "date": today_str,
            "models": models_list,
            "total_cost": total_cost,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
        })

    def api_sessions(self, params):
        """会话列表（支持搜索、项目过滤、日期范围、数据源过滤）"""
        limit = int(params.get("limit", ["50"])[0])
        project_filter = params.get("project", [""])[0]
        search_query = params.get("q", [""])[0].lower()
        source = params.get("source", ["all"])[0]
        # 日期范围: "1d", "7d", "30d", 或 "2026-03-20,2026-03-24"
        date_range = params.get("range", [""])[0]

        history = _load_history() if source != "codex" else []

        # Get session entrypoints from scan cache
        scan_data = _scan_all_projects()
        ep_map = scan_data.get("session_entrypoints", {}) if scan_data else {}

        # 按时间倒序
        entries = sorted(history, key=lambda x: x.get("timestamp", 0), reverse=True)

        # 日期范围过滤
        if date_range:
            now_ms = time.time() * 1000
            if date_range.endswith("d"):
                days = int(date_range[:-1])
                cutoff = now_ms - days * 86400 * 1000
                entries = [e for e in entries if e.get("timestamp", 0) >= cutoff]
            elif date_range.endswith("h"):
                hours = int(date_range[:-1])
                cutoff = now_ms - hours * 3600 * 1000
                entries = [e for e in entries if e.get("timestamp", 0) >= cutoff]
            elif "," in date_range:
                start_str, end_str = date_range.split(",", 1)
                entries = [e for e in entries
                           if ms_to_date(e.get("timestamp", 0)) >= start_str
                           and ms_to_date(e.get("timestamp", 0)) <= end_str]

        # 筛选项目
        if project_filter:
            entries = [e for e in entries if project_filter in e.get("project", "")]

        # 搜索过滤
        if search_query:
            entries = [e for e in entries if
                       search_query in (e.get("display", "") or "").lower() or
                       search_query in (e.get("sessionId", "") or "").lower() or
                       search_query in (e.get("project", "") or "").lower()]

        # 去重 sessionId
        seen = set()
        unique_sessions = []
        for entry in entries:
            sid = entry.get("sessionId", "")
            if sid in seen:
                continue
            seen.add(sid)

            project_path = entry.get("project", "")
            project_short = project_path.split("/")[-1] if project_path else "~"

            unique_sessions.append({
                "sessionId": sid,
                "timestamp": entry.get("timestamp", 0),
                "project": project_path,
                "projectShort": project_short,
                "firstPrompt": entry.get("display", "")[:100],
                "source": "claude",
                "entrypoint": ep_map.get(sid, "cli"),
            })
            if len(unique_sessions) >= limit:
                break

        # Add desktop/SDK sessions that are NOT in history.jsonl
        # (Desktop App sessions don't write to history.jsonl)
        if source != "codex":
            desktop_eps = {"claude-desktop", "sdk-ts", "sdk-cli", "local-agent"}
            # Pre-build session→project map to avoid O(n*m) dir scans
            session_project_map = {}  # sid -> (proj_dir_path, friendly_name)
            if PROJECTS_DIR.exists():
                for proj_dir in PROJECTS_DIR.iterdir():
                    if not proj_dir.is_dir():
                        continue
                    fname = friendly_project_name(proj_dir.name)
                    for jf in proj_dir.glob("*.jsonl"):
                        session_project_map[jf.stem] = (proj_dir / jf.name, fname)

            for sid, ep_val in ep_map.items():
                if ep_val in desktop_eps and sid not in seen:
                    seen.add(sid)
                    sf_path, proj_short = session_project_map.get(sid, (None, "~"))
                    ts = 0
                    first_prompt = ""
                    if sf_path and sf_path.exists():
                        try:
                            with open(sf_path, "r", encoding="utf-8", errors="replace") as sf_f:
                                for sline in sf_f:
                                    try:
                                        sevt = json.loads(sline.strip())
                                        if sevt.get("timestamp") and ts == 0:
                                            ts_str = sevt["timestamp"]
                                            if isinstance(ts_str, str):
                                                ts = int(datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp() * 1000)
                                        if sevt.get("type") == "user" and not first_prompt:
                                            msg = sevt.get("message", "")
                                            if isinstance(msg, dict):
                                                msg = str(msg.get("content", ""))
                                            first_prompt = (msg or "")[:100]
                                        if ts and first_prompt:
                                            break
                                    except Exception:
                                        continue
                        except Exception:
                            pass
                    unique_sessions.append({
                        "sessionId": sid,
                        "timestamp": ts,
                        "project": proj_short,
                        "projectShort": proj_short,
                        "firstPrompt": first_prompt,
                        "source": "claude",
                        "entrypoint": ep_val,
                    })

        # Sort all sessions by timestamp descending, then trim
        unique_sessions.sort(key=lambda s: s.get("timestamp", 0), reverse=True)
        unique_sessions = unique_sessions[:limit]

        # 收集所有项目路径用于筛选
        all_projects = list(set(e.get("project", "") for e in history if e.get("project")))
        all_projects.sort()

        # Merge remote sessions (only for source=all)
        for r in _get_active_remotes():
            rd = _fetch_remote_cached(r["url"], "/api/sessions?limit=20", r.get("token"))
            if rd and rd.get("sessions"):
                rname = r.get("name", "cloud")
                for s in rd["sessions"]:
                    ps = s.get("projectShort", "?")
                    if rname not in ps:
                        s["projectShort"] = ps + f" ({rname})"
                    if "source" not in s:
                        s["source"] = "claude"  # Default remote sessions to claude
                    unique_sessions.append(s)

        # Merge Codex sessions (skip if source=claude)
        if source != "claude" and _codex_enabled():
            try:
                # Read Codex history.jsonl
                codex_hist = CODEX_DIR / "history.jsonl"
                codex_index = CODEX_DIR / "session_index.jsonl"
                # Build index of thread names
                thread_names = {}
                if codex_index.exists():
                    with open(codex_index, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            try:
                                e = json.loads(line.strip())
                                thread_names[e.get("id", "")] = e.get("thread_name", "")
                            except: pass
                # Read history for session list
                codex_sessions = {}
                if codex_hist.exists():
                    with open(codex_hist, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            try:
                                e = json.loads(line.strip())
                                sid = e.get("session_id", "")
                                if not sid or sid in seen: continue
                                ts_sec = e.get("ts", 0)
                                if sid not in codex_sessions:
                                    codex_sessions[sid] = {
                                        "sessionId": sid,
                                        "timestamp": ts_sec * 1000,
                                        "project": "Codex CLI",
                                        "projectShort": "Codex CLI",
                                        "firstPrompt": e.get("text", "")[:100],
                                        "source": "codex",
                                    }
                            except: pass
                # Also add sessions from index that might not be in history
                for sid, name in thread_names.items():
                    if sid not in seen and sid not in codex_sessions:
                        codex_sessions[sid] = {
                            "sessionId": sid,
                            "timestamp": 0,
                            "project": "Codex CLI",
                            "projectShort": "Codex CLI",
                            "firstPrompt": name[:100],
                            "source": "codex",
                        }
                for s in codex_sessions.values():
                    # Use thread_name if available
                    if s["sessionId"] in thread_names and not s["firstPrompt"]:
                        s["firstPrompt"] = thread_names[s["sessionId"]][:100]
                    unique_sessions.append(s)
                    seen.add(s["sessionId"])
            except Exception:
                pass

        # Re-sort by timestamp after merge
        unique_sessions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        unique_sessions = unique_sessions[:limit]

        self.send_json({
            "sessions": unique_sessions,
            "projects": all_projects,
        })

    def api_session_detail(self, params):
        """Session detail: parse JSONL file for a given session ID and return conversation timeline"""
        session_id = params.get("id", [""])[0]
        if not session_id:
            self.send_json({"error": "missing session id"}, 400)
            return

        # Find the JSONL file: try filename match, then scan for sessionId
        jsonl_path = None
        if PROJECTS_DIR.exists():
            for project_dir in PROJECTS_DIR.iterdir():
                if not project_dir.is_dir():
                    continue
                candidate = project_dir / (session_id + ".jsonl")
                if candidate.exists():
                    jsonl_path = candidate
                    break
            # Fallback: scan first lines of files
            if not jsonl_path:
                for project_dir in PROJECTS_DIR.iterdir():
                    if not project_dir.is_dir():
                        continue
                    for jf in project_dir.glob("*.jsonl"):
                        try:
                            with open(jf, "r", encoding="utf-8", errors="replace") as f:
                                for i, line in enumerate(f):
                                    if i > 10:
                                        break
                                    if not line.strip():
                                        continue
                                    evt = json.loads(line.strip())
                                    if evt.get("sessionId") == session_id:
                                        jsonl_path = jf
                                        break
                            if jsonl_path:
                                break
                        except Exception:
                            continue
                    if jsonl_path:
                        break

        if not jsonl_path:
            # Try Codex sessions
            codex_path = _find_codex_session_file(session_id)
            if codex_path:
                result = _parse_codex_session(codex_path)
                self.send_json(result)
                return
            # Try remote
            for r in _get_active_remotes():
                rd = _fetch_remote(r["url"].rstrip("/") + f"/api/session-detail?id={session_id}", r.get("token"), timeout=15)
                if rd and not rd.get("error"):
                    self.send_json(rd)
                    return
            self.send_json({"error": "session not found"}, 404)
            return

        # Parse the JSONL file
        events_out = []
        models_seen = set()
        tools_summary = {}
        files_touched = {}
        total_cost = 0.0
        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_create = 0
        msg_count = 0
        first_ts = None
        last_ts = None

        try:
            raw_events = []
            with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            for evt in raw_events:
                evt_type = evt.get("type", "")
                ts = evt.get("timestamp", "")

                if ts:
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts

                if evt_type == "user" and "message" in evt:
                    msg_count += 1
                    msg = evt.get("message", {})
                    content = ""
                    if isinstance(msg, dict):
                        raw_content = msg.get("content", "")
                        if isinstance(raw_content, str):
                            content = raw_content
                        elif isinstance(raw_content, list):
                            # Array of content blocks
                            text_parts = []
                            for block in raw_content:
                                if isinstance(block, dict):
                                    if block.get("type") == "text":
                                        text_parts.append(block.get("text", ""))
                                elif isinstance(block, str):
                                    text_parts.append(block)
                            content = " ".join(text_parts)
                    events_out.append({
                        "type": "user",
                        "timestamp": ts,
                        "content": content,
                    })

                elif evt_type == "assistant" and "message" in evt:
                    msg_count += 1
                    msg = evt.get("message", {})
                    if not isinstance(msg, dict):
                        continue

                    usage = msg.get("usage", {})
                    model = msg.get("model", "unknown")
                    models_seen.add(model)

                    inp = usage.get("input_tokens", 0) or 0
                    out = usage.get("output_tokens", 0) or 0
                    cr = usage.get("cache_read_input_tokens", 0) or 0
                    cc = usage.get("cache_creation_input_tokens", 0) or 0
                    cost = _calc_cost(model, inp, out, cr, cc)
                    total_cost += cost
                    total_input += inp
                    total_output += out
                    total_cache_read += cr
                    total_cache_create += cc

                    # Extract text content and tool_use blocks
                    content_blocks = msg.get("content", [])
                    text_parts = []
                    tools_used = []

                    if isinstance(content_blocks, list):
                        for block in content_blocks:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif block.get("type") == "tool_use":
                                    tool_name = block.get("name", "unknown")
                                    tools_used.append(tool_name)
                                    tools_summary[tool_name] = tools_summary.get(tool_name, 0) + 1

                                    # Track file paths for Read/Edit/Write/Glob
                                    tool_input = block.get("input", {})
                                    if isinstance(tool_input, dict):
                                        file_path = tool_input.get("file_path") or tool_input.get("path") or ""
                                        if file_path and tool_name in ("Read", "Edit", "Write", "Glob"):
                                            ft = files_touched.setdefault(file_path, {"read": 0, "edit": 0})
                                            if tool_name == "Read" or tool_name == "Glob":
                                                ft["read"] += 1
                                            else:
                                                ft["edit"] += 1
                            elif isinstance(block, str):
                                text_parts.append(block)
                    elif isinstance(content_blocks, str):
                        text_parts.append(content_blocks)

                    content_text = " ".join(text_parts)

                    events_out.append({
                        "type": "assistant",
                        "timestamp": ts,
                        "content": content_text,
                        "model": model,
                        "input_tokens": inp,
                        "output_tokens": out,
                        "cost_usd": round(cost, 6),
                        "tools_used": tools_used,
                    })

        except Exception as e:
            self.send_json({"error": str(e)}, 500)
            return

        # Calculate duration
        duration_ms = 0
        if first_ts and last_ts:
            dt_first = parse_iso_ts(first_ts)
            dt_last = parse_iso_ts(last_ts)
            if dt_first and dt_last:
                duration_ms = int((dt_last - dt_first).total_seconds() * 1000)

        # Keep only top 20 files
        top_files = dict(sorted(files_touched.items(),
                                key=lambda x: x[1]["read"] + x[1]["edit"],
                                reverse=True)[:20])

        self.send_json({
            "session_id": session_id,
            "events": events_out,
            "stats": {
                "messages": msg_count,
                "duration_ms": duration_ms,
                "total_cost": round(total_cost, 4),
                "total_input": total_input,
                "total_output": total_output,
                "total_cache_read": total_cache_read,
                "total_cache_create": total_cache_create,
                "models": list(models_seen),
                "tools_summary": tools_summary,
                "files_touched": top_files,
            }
        })

    def api_hourly(self, params):
        """小时 × 星期 热力图（聚合远程），支持 days 参数过滤"""
        days = int(params.get("days", [0])[0] or 0)
        history = _load_history()
        heatmap = [[0] * 24 for _ in range(7)]

        # 计算截止时间（毫秒）
        cutoff_ms = 0
        if days > 0:
            cutoff_ms = (time.time() - days * 86400) * 1000

        for entry in history:
            ts = entry.get("timestamp", 0)
            if cutoff_ms and ts < cutoff_ms:
                continue
            hour, dow = ms_to_hour_dow(ts)
            if hour is not None and dow is not None:
                heatmap[dow][hour] += 1

        # 聚合远程
        for r in _get_active_remotes():
            remote_path = f"/api/hourly?days={days}" if days else "/api/hourly"
            rd = _fetch_remote_cached(r["url"], remote_path, r.get("token"))
            if rd and "heatmap" in rd:
                for dow in range(7):
                    for h in range(24):
                        heatmap[dow][h] += rd["heatmap"][dow][h]

        self.send_json({"heatmap": heatmap})

    def api_live(self, params):
        """今日实时调用（聚合远程 + Codex）"""
        source = params.get("source", ["all"])[0]
        if source == "codex":
            # Only Codex live data
            codex_today = _scan_codex_today()
            data = codex_today if codex_today else {"calls": [], "totals": {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0, "cost": 0}}
        else:
            data = _scan_today()
            # Merge Codex today data (unless source=claude)
            if source != "claude":
                codex_today = _scan_codex_today()
                if codex_today:
                    data["calls"] = data.get("calls", []) + codex_today.get("calls", [])
                    data["calls"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                    for k in ("input", "output", "cache_read", "cache_create", "calls"):
                        data["totals"][k] = data["totals"].get(k, 0) + codex_today.get("totals", {}).get(k, 0)
                    data["totals"]["cost"] = data["totals"].get("cost", 0) + codex_today.get("totals", {}).get("cost", 0)
        remotes = _get_active_remotes()
        remote_live = [_fetch_remote_cached(r["url"], "/api/live" + (f"?source={source}" if source != "all" else ""), r.get("token")) for r in remotes]
        remote_live = [rd for rd in remote_live if rd]
        if remote_live:
            data = _merge_live(data, remote_live)
        self.send_json(data)

    def api_logs(self, params):
        """带过滤与分页的用量日志（聚合远程 + Codex）"""
        limit = int(params.get("limit", ["50"])[0])
        offset = int(params.get("offset", ["0"])[0])
        model_filter = params.get("model", [""])[0]
        project_filter = params.get("project", [""])[0]
        start = params.get("start", [""])[0]
        end = params.get("end", [""])[0]
        source = params.get("source", ["all"])[0]

        if source == "codex":
            all_logs = list(_scan_codex_logs() or [])
        else:
            all_logs = list(_scan_all_logs())  # copy to avoid mutating cache
            # Merge Codex logs (unless source=claude)
            if source != "claude":
                codex_logs = _scan_codex_logs()
                if codex_logs:
                    all_logs.extend(codex_logs)

        # Merge remote logs
        for r in _get_active_remotes():
            rd = _fetch_remote_cached(r["url"], "/api/logs?limit=200" + (f"&source={source}" if source != "all" else ""), r.get("token"))
            if rd and rd.get("logs"):
                rname = r.get("name", "cloud")
                for c in rd["logs"]:
                    c["project"] = c.get("project", "") + f" ({rname})"
                    if "source" not in c:
                        c["source"] = "claude"
                all_logs.extend(rd["logs"])
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        filtered = all_logs
        if model_filter:
            filtered = [c for c in filtered if model_filter in c["model"]]
        if project_filter:
            filtered = [c for c in filtered if project_filter in c["project"]]
        if start:
            filtered = [c for c in filtered if c["timestamp"] >= start]
        if end:
            filtered = [c for c in filtered if c["timestamp"] <= end]

        total = len(filtered)
        page = filtered[offset:offset + limit]

        # Add relative time to each entry
        for entry in page:
            entry["relative_time"] = _relative_time(entry["timestamp"])

        self.send_json({
            "logs": page,
            "total": total,
            "limit": limit,
            "offset": offset,
        })


    def api_tools(self, params):
        """Tool usage statistics (Claude + Codex)"""
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex()
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        tools = scan.get("tools_stats", {})
        total_calls = sum(t.get("calls", 0) for t in tools.values())
        self.send_json({
            "tools": tools,
            "total_calls": total_calls,
        })

    def api_export(self, params):
        """Export logs data as CSV or JSON"""
        fmt = params.get("format", ["json"])[0]
        model_filter = params.get("model", [""])[0]
        project_filter = params.get("project", [""])[0]
        start = params.get("start", [""])[0]
        end = params.get("end", [""])[0]

        all_logs = _scan_all_logs()

        filtered = all_logs
        if model_filter:
            filtered = [c for c in filtered if model_filter in c["model"]]
        if project_filter:
            filtered = [c for c in filtered if project_filter in c["project"]]
        if start:
            filtered = [c for c in filtered if c["timestamp"] >= start]
        if end:
            filtered = [c for c in filtered if c["timestamp"] <= end]

        if fmt == "csv":
            import io
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["timestamp", "model", "project", "input_tokens", "output_tokens",
                             "cache_read", "cache_create", "cost_usd", "ttft_ms", "duration_ms", "status"])
            for c in filtered:
                writer.writerow([
                    c.get("timestamp", ""), c.get("model", ""), c.get("project", ""),
                    c.get("input_tokens", 0), c.get("output_tokens", 0),
                    c.get("cache_read", 0), c.get("cache_create", 0),
                    c.get("cost_usd", 0), c.get("ttft_ms", ""), c.get("duration_ms", ""),
                    c.get("status", 200),
                ])
            body = output.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=claude_logs.csv")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json({"logs": filtered, "total": len(filtered)})

    def api_session_chain(self, params):
        """Detect session resume chains — sessions linked by parentUuid or leaf_uuid"""
        session_id = params.get("id", [""])[0]
        if not session_id:
            self.send_json({"error": "missing id"}, 400)
            return

        # Find all sessions in the same project directory
        target_dir = None
        if PROJECTS_DIR.exists():
            for pd in PROJECTS_DIR.iterdir():
                if not pd.is_dir():
                    continue
                candidate = pd / (session_id + ".jsonl")
                if candidate.exists():
                    target_dir = pd
                    break
                # Fallback scan
                for jf in pd.glob("*.jsonl"):
                    try:
                        with open(jf, "r", encoding="utf-8", errors="replace") as f:
                            for i, line in enumerate(f):
                                if i > 5:
                                    break
                                if not line.strip():
                                    continue
                                evt = json.loads(line.strip())
                                if evt.get("sessionId") == session_id:
                                    target_dir = pd
                                    break
                        if target_dir:
                            break
                    except Exception:
                        continue
                if target_dir:
                    break

        if not target_dir:
            # Try Codex sessions — group by cwd
            codex_path = _find_codex_session_file(session_id)
            if codex_path:
                # Find the cwd of this session
                target_cwd = None
                try:
                    with open(codex_path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            try:
                                evt = json.loads(line.strip())
                                if evt.get("type") == "session_meta":
                                    target_cwd = evt["payload"].get("cwd", "")
                                    break
                            except: pass
                except: pass

                # Scan all Codex sessions with same cwd
                chain = []
                all_codex_files = []
                for d in [CODEX_SESSIONS_DIR, CODEX_ARCHIVED_DIR]:
                    if d.exists():
                        all_codex_files.extend(d.rglob("rollout-*.jsonl"))

                codex_model = _read_codex_model()

                for jf in all_codex_files:
                    try:
                        sid = cwd = first_ts = last_ts = last_prompt = model = ""
                        msg_count = total_cost = 0.0
                        last_usage = None
                        with open(jf, "r", encoding="utf-8", errors="replace") as f:
                            for line in f:
                                try:
                                    evt = json.loads(line.strip())
                                except: continue
                                ts = evt.get("timestamp", "")
                                if ts and not first_ts: first_ts = ts
                                if ts: last_ts = ts
                                etype = evt.get("type", "")
                                payload = evt.get("payload", {})
                                if not isinstance(payload, dict): continue
                                if etype == "session_meta":
                                    sid = payload.get("id", jf.stem)
                                    cwd = payload.get("cwd", "")
                                elif etype == "turn_context":
                                    m = payload.get("model", "")
                                    if m: model = m
                                elif etype == "event_msg":
                                    if payload.get("type") == "user_message":
                                        msg_count += 1
                                        msg = payload.get("message", "").lstrip("-\n \t").strip()
                                        if msg: last_prompt = msg[:80]
                                    elif payload.get("type") == "token_count":
                                        info = payload.get("info")
                                        if isinstance(info, dict):
                                            last_usage = info.get("total_token_usage", {})

                        if not sid: sid = jf.stem
                        if not model: model = codex_model
                        if target_cwd and cwd != target_cwd: continue

                        u = last_usage or {}
                        inp = u.get("input_tokens", 0) or 0
                        out = u.get("output_tokens", 0) or 0
                        cr = u.get("cached_input_tokens", 0) or 0
                        total_cost = _calc_cost(model, inp, out, cr, 0)

                        dur_str = ""
                        if first_ts and last_ts:
                            try:
                                t1 = parse_iso_ts(first_ts)
                                t2 = parse_iso_ts(last_ts)
                                if t1 and t2:
                                    secs = int((t2-t1).total_seconds())
                                    dur_str = f"{secs//3600}h{(secs%3600)//60}m" if secs>=3600 else f"{secs//60}m" if secs>=60 else f"{secs}s"
                            except: pass

                        chain.append({
                            "session_id": sid, "first_ts": first_ts, "last_ts": last_ts,
                            "messages": msg_count, "cost_usd": round(total_cost, 4),
                            "model": model, "last_prompt": last_prompt, "duration": dur_str,
                            "is_current": sid == session_id,
                        })
                    except: continue

                chain.sort(key=lambda x: x.get("last_ts") or "0", reverse=True)
                for i, s in enumerate(chain): s["index"] = i + 1
                proj_name = target_cwd.rstrip("/").split("/")[-1] if target_cwd else "Codex"
                self.send_json({"chain": chain[:30], "total": len(chain), "project": proj_name + " (Codex)"})
                return
            # Try remote (no cache, longer timeout for large sessions)
            for r in _get_active_remotes():
                rd = _fetch_remote(r["url"].rstrip("/") + f"/api/session-chain?id={session_id}", r.get("token"), timeout=15)
                if rd and rd.get("chain"):
                    self.send_json(rd)
                    return
            self.send_json({"chain": [], "total": 0})
            return

        # Collect all sessions in this project with metadata
        sessions = []
        for jf in sorted(target_dir.glob("*.jsonl")):
            try:
                sid = jf.stem
                first_ts = None
                last_ts = None
                msg_count = 0
                total_cost = 0.0
                model = ""
                first_prompt = ""
                leaf_uuids = set()
                parent_refs = set()

                with open(jf, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            evt = json.loads(line)
                        except:
                            continue
                        ts = evt.get("timestamp", "")
                        if ts and not first_ts:
                            first_ts = ts
                        if ts:
                            last_ts = ts
                        if evt.get("type") == "user":
                            msg_count += 1
                            # Always update to get the LAST prompt
                            um = evt.get("message", {})
                            if isinstance(um, dict):
                                c = um.get("content", "")
                                if isinstance(c, str) and c.strip():
                                    # Clean common prefixes: "-\n", "- ", leading dashes/newlines
                                    cleaned = c.lstrip("-\n \t").strip()
                                    if cleaned:
                                        first_prompt = cleaned[:80]
                                elif isinstance(c, list):
                                    for blk in c:
                                        if isinstance(blk, dict) and blk.get("type") == "text":
                                            cleaned = blk.get("text", "").lstrip("-\n \t").strip()
                                            if cleaned:
                                                first_prompt = cleaned[:80]
                                                break
                        elif evt.get("type") == "assistant" and "message" in evt:
                            msg = evt["message"]
                            if isinstance(msg, dict):
                                usage = msg.get("usage", {})
                                m = msg.get("model", "")
                                if m:
                                    model = m
                                inp = usage.get("input_tokens", 0) or 0
                                out = usage.get("output_tokens", 0) or 0
                                cr = usage.get("cache_read_input_tokens", 0) or 0
                                cc = usage.get("cache_creation_input_tokens", 0) or 0
                                total_cost += _calc_cost(m, inp, out, cr, cc)
                        # Track UUIDs for chain detection
                        uuid = evt.get("uuid", "")
                        if uuid:
                            leaf_uuids.add(uuid)
                        parent = evt.get("parentUuid", "")
                        if parent:
                            parent_refs.add(parent)

                # Calculate duration
                dur_str = ""
                if first_ts and last_ts:
                    try:
                        t1 = parse_iso_ts(first_ts)
                        t2 = parse_iso_ts(last_ts)
                        if t1 and t2:
                            secs = int((t2 - t1).total_seconds())
                            if secs >= 3600:
                                dur_str = f"{secs//3600}h{(secs%3600)//60}m"
                            elif secs >= 60:
                                dur_str = f"{secs//60}m"
                            else:
                                dur_str = f"{secs}s"
                    except Exception:
                        pass

                sessions.append({
                    "session_id": sid,
                    "first_ts": first_ts,
                    "last_ts": last_ts,
                    "messages": msg_count,
                    "cost_usd": round(total_cost, 4),
                    "model": model,
                    "last_prompt": first_prompt,
                    "duration": dur_str,
                    "is_current": sid == session_id,
                    "_leaf_uuids": leaf_uuids,
                    "_parent_refs": parent_refs,
                })
            except Exception:
                continue

        # Sort by first timestamp
        sessions.sort(key=lambda x: x.get("first_ts") or "", reverse=True)

        # Build chain output (strip internal fields)
        chain = []
        for i, s in enumerate(sessions[:30]):
            chain.append({
                "session_id": s["session_id"],
                "first_ts": s["first_ts"],
                "last_ts": s["last_ts"],
                "messages": s["messages"],
                "cost_usd": s["cost_usd"],
                "model": s["model"],
                "last_prompt": s.get("last_prompt", ""),
                "duration": s.get("duration", ""),
                "is_current": s["is_current"],
                "index": i + 1,
            })

        self.send_json({"chain": chain, "total": len(chain), "project": friendly_project_name(target_dir.name)})

    def api_hourly_trend(self, params):
        """Last 24 hours broken down by hour — for the 24H trend view"""
        logs = _scan_all_logs()
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff = now - datetime.timedelta(hours=24)

        hourly = {}  # "HH:00" -> {messages, tokens, cost, sessions}
        for c in logs:
            try:
                ts = parse_iso_ts(c.get("timestamp", ""))
                if not ts or ts < cutoff:
                    continue
                hour_key = ts.strftime("%H:00")
                if hour_key not in hourly:
                    hourly[hour_key] = {"messages": 0, "tokens": 0, "cost": 0.0}
                hourly[hour_key]["messages"] += 1
                hourly[hour_key]["tokens"] += c.get("input_tokens", 0) + c.get("output_tokens", 0)
                hourly[hour_key]["cost"] += c.get("cost_usd", 0)
            except Exception:
                continue

        # Build ordered 24-hour array
        result = []
        for h in range(24):
            key = f"{h:02d}:00"
            d = hourly.get(key, {"messages": 0, "tokens": 0, "cost": 0.0})
            result.append({"hour": key, "messages": d["messages"], "tokens": d["tokens"], "cost": round(d["cost"], 4)})

        self.send_json({"hours": result})

    def api_claude_usage(self, params):
        """Claude.ai weekly usage from official API"""
        data = _fetch_claude_usage()
        self.send_json(data)

    def api_web_conversations(self, params):
        """List claude.ai web conversations"""
        data = _fetch_web_conversations()
        self.send_json(data)

    def api_web_conversation_detail(self, params):
        """Get a single web conversation with messages"""
        conv_id = params.get("id", [""])[0]
        if not conv_id:
            self.send_json({"error": "missing id parameter"}, 400)
            return
        data = _fetch_web_conversation_detail(conv_id)
        self.send_json(data)

    def api_settings_get(self, params):
        """GET /api/settings — return config with masked secrets + detected models"""
        config = _load_config()

        # Mask sensitive fields
        def _mask(val):
            if not val or not isinstance(val, str):
                return ""
            if len(val) <= 14:
                return "***"
            return val[:10] + "***" + val[-4:]

        # Collect detected models from scan cache
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex()
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        detected_models = sorted(scan.get("models", {}).keys())

        # Data sources status
        data_sources = {
            "claude_code": {
                "enabled": True,
                "detected": PROJECTS_DIR.exists(),
                "path": str(CLAUDE_DIR),
            },
            "codex_cli": {
                "enabled": _codex_enabled(),
                "detected": CODEX_SESSIONS_DIR.exists() or CODEX_ARCHIVED_DIR.exists(),
                "path": str(CODEX_DIR),
                "model": _read_codex_model() if _codex_enabled() else "",
            },
        }

        self.send_json({
            "remotes": config.get("remotes", []),
            "claude_session_key": _mask(config.get("claude_session_key", "")),
            "claude_org_id": _mask(config.get("claude_org_id", "")),
            "custom_pricing": config.get("custom_pricing", {}),
            "detected_models": detected_models,
            "data_sources": data_sources,
        })

    def api_settings_post(self, data):
        """POST /api/settings — merge into config.json"""
        config = _load_config()

        # Update custom_pricing if provided
        if "custom_pricing" in data:
            config["custom_pricing"] = data["custom_pricing"]

        # Update session key only if not masked
        if "claude_session_key" in data:
            val = data["claude_session_key"]
            if isinstance(val, str) and val and "***" not in val:
                config["claude_session_key"] = val

        # Update org id only if not masked
        if "claude_org_id" in data:
            val = data["claude_org_id"]
            if isinstance(val, str) and val and "***" not in val:
                config["claude_org_id"] = val

        # Write back to config.json
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            # Clear caches so new pricing takes effect
            _scan_cache.update(data=None, time=0)
            _live_cache.update(data=None, time=0)
            _logs_cache.update(data=None, time=0)
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def api_rhythm(self, params):
        """编码节奏 + 工作模式分析"""
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex()
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)

        # 1. Coding rhythm: from hourly heatmap aggregate by time period
        history = _load_history()
        periods = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}  # 06-12, 12-18, 18-24, 00-06
        hourly = [0] * 24
        for entry in history:
            ts = entry.get("timestamp", 0)
            h, _ = ms_to_hour_dow(ts)
            if h is not None:
                hourly[h] += 1
                if 6 <= h < 12:
                    periods["morning"] += 1
                elif 12 <= h < 18:
                    periods["afternoon"] += 1
                elif 18 <= h < 24:
                    periods["evening"] += 1
                else:
                    periods["night"] += 1
        total_p = sum(periods.values()) or 1
        peak_hour = hourly.index(max(hourly)) if any(hourly) else 0

        # 2. Work mode: classify tools
        tools = scan.get("tools_stats", {})
        exploration = sum(tools.get(t, {}).get("calls", 0) for t in ["Read", "Grep", "Glob", "WebFetch", "WebSearch"])
        building = sum(tools.get(t, {}).get("calls", 0) for t in ["Write", "Edit", "NotebookEdit"])
        execution = sum(tools.get(t, {}).get("calls", 0) for t in ["Bash", "Agent", "TodoWrite"])
        total_t = exploration + building + execution or 1
        primary = "exploration" if exploration >= building and exploration >= execution else "building" if building >= execution else "execution"

        # 3. Model DNA: distribution by model family
        models = scan.get("models", {})
        families = {}
        for m, v in models.items():
            total_tok = v.get("input", 0) + v.get("output", 0) + v.get("cache_read", 0) + v.get("cache_create", 0)
            ml = m.lower()
            if "opus" in ml:
                families["Opus"] = families.get("Opus", 0) + total_tok
            elif "sonnet" in ml:
                families["Sonnet"] = families.get("Sonnet", 0) + total_tok
            elif "haiku" in ml:
                families["Haiku"] = families.get("Haiku", 0) + total_tok
            elif "gpt" in ml or "codex" in ml:
                families["GPT/Codex"] = families.get("GPT/Codex", 0) + total_tok
            else:
                families["Other"] = families.get("Other", 0) + total_tok

        self.send_json({
            "rhythm": {
                "periods": {k: round(v / total_p * 100) for k, v in periods.items()},
                "raw": periods,
                "peak_hour": peak_hour,
                "hourly": hourly,
            },
            "work_mode": {
                "exploration": round(exploration / total_t * 100),
                "building": round(building / total_t * 100),
                "execution": round(execution / total_t * 100),
                "primary": primary,
                "raw": {"exploration": exploration, "building": building, "execution": execution},
            },
            "model_dna": families,
        })


    # ============================================================
    # v0.6.0 — MCP Server Analytics
    # ============================================================
    def api_mcp_stats(self, params):
        """MCP server-level aggregated statistics"""
        source = params.get("source", ["all"])[0]
        # MCP tools are Claude Code specific — return empty for codex-only
        if source == "codex":
            self.send_json({"servers": [], "total_calls": 0, "total_servers": 0})
            return
        scan = copy.deepcopy(_scan_all_projects())
        mcp = scan.get("mcp_stats", {})
        if not mcp:
            self.send_json({"servers": [], "total_calls": 0, "total_servers": 0})
            return

        servers = []
        total_calls = 0
        for name, data in sorted(mcp.items(), key=lambda x: x[1]["calls"], reverse=True):
            total_calls += data["calls"]
            # Top tools for this server
            top_tools = sorted(data.get("tools", {}).items(), key=lambda x: x[1], reverse=True)[:10]
            servers.append({
                "name": name,
                "calls": data["calls"],
                "sessions": data["sessions"],
                "top_tools": [{"name": t, "calls": c} for t, c in top_tools],
            })

        self.send_json({
            "servers": servers,
            "total_calls": total_calls,
            "total_servers": len(servers),
        })

    def api_mcp_trend(self, params):
        """MCP usage daily trend"""
        source = params.get("source", ["all"])[0]
        if source == "codex":
            self.send_json({"trend": [], "servers": [], "tool_type_trend": []})
            return
        days = int(params.get("days", ["30"])[0])
        scan = copy.deepcopy(_scan_all_projects())
        daily_tools = scan.get("daily_tools", {})

        # Aggregate by MCP server per day
        sorted_dates = sorted(daily_tools.keys())[-days:]
        # Collect all MCP server names
        all_servers = set()
        for dt in sorted_dates:
            for tool_name in daily_tools[dt]:
                if tool_name.startswith("mcp__"):
                    parts = tool_name.split("__")
                    if len(parts) >= 3:
                        all_servers.add(parts[1])

        trend = []
        for dt in sorted_dates:
            entry = {"date": dt}
            dt_tools = daily_tools.get(dt, {})
            for srv in all_servers:
                count = 0
                for tool_name, calls in dt_tools.items():
                    if tool_name.startswith(f"mcp__{srv}__"):
                        count += calls
                entry[srv] = count
            trend.append(entry)

        # Also daily total for non-MCP tools
        non_mcp_trend = []
        for dt in sorted_dates:
            dt_tools = daily_tools.get(dt, {})
            mcp_total = sum(c for t, c in dt_tools.items() if t.startswith("mcp__"))
            non_mcp = sum(c for t, c in dt_tools.items() if not t.startswith("mcp__"))
            non_mcp_trend.append({"date": dt, "mcp": mcp_total, "builtin": non_mcp})

        self.send_json({
            "trend": trend,
            "servers": sorted(all_servers),
            "tool_type_trend": non_mcp_trend,
        })

    # ============================================================
    # v0.6.1 — Rate Limit Predictor
    # ============================================================
    def api_rate_prediction(self, params):
        """Predict rate limit timing based on current burn rate + quota"""
        source = params.get("source", ["all"])[0]
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Get current quota utilization
        cur_util = 0
        resets_at = ""
        profile = ""
        try:
            if USAGE_CACHE_FILE.exists():
                with open(USAGE_CACHE_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("UTILIZATION="):
                            cur_util = int(line.split("=", 1)[1])
                        elif line.startswith("RESETS_AT="):
                            resets_at = line.split("=", 1)[1]
                        elif line.startswith("PROFILE_NAME="):
                            profile = line.split("=", 1)[1]
        except Exception:
            pass

        # 2. Compute burn rates over multiple windows
        try:
            logs = _scan_all_logs()
            if source != "all":
                logs = [c for c in logs if c.get("source", "claude") == source]
        except Exception:
            logs = []

        windows = {"5m": 300, "15m": 900, "30m": 1800, "60m": 3600}
        rates = {}
        for label, secs in windows.items():
            recent = [c for c in logs if c.get("timestamp") and
                      (now - parse_iso_ts(c["timestamp"])).total_seconds() < secs]
            if recent:
                total_tok = sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) +
                                c.get("cache_read", 0) + c.get("cache_create", 0)
                                for c in recent)
                minutes = secs / 60
                rates[label] = {
                    "calls": len(recent),
                    "tokens": total_tok,
                    "rpm": round(len(recent) / minutes, 1),
                    "tpm": round(total_tok / minutes),
                }
            else:
                rates[label] = {"calls": 0, "tokens": 0, "rpm": 0, "tpm": 0}

        # 3. Predict time to throttle
        remaining_pct = max(0, 100 - cur_util)
        # Use 30m window as primary predictor
        burn_30m = rates.get("30m", {})
        burn_rpm = burn_30m.get("rpm", 0)
        burn_tpm = burn_30m.get("tpm", 0)

        # Estimate minutes until 5h quota depletes
        # Predict minutes until quota exhausted using 30m burn rate
        # Logic: if 30m consumed X calls, and cur_util used Y%, then
        # util_per_minute ≈ (calls_30m_contribution) / 30, extrapolate remaining
        # Estimate remaining time: remaining_pct% at current pace
        # 5h window = 300 min. Used cur_util% so far.
        # elapsed ≈ cur_util/100 * 300, remaining ≈ remaining_pct/100 * 300
        if remaining_pct <= 0:
            minutes_to_throttle = 0
        else:
            minutes_to_throttle = round(remaining_pct / 100 * 300)
            minutes_to_throttle = max(0, min(minutes_to_throttle, 300))

        # 4. Risk level
        if cur_util >= 95 or remaining_pct <= 0:
            risk = "critical"
        elif cur_util >= 80 or (minutes_to_throttle is not None and minutes_to_throttle < 30):
            risk = "danger"
        elif cur_util >= 60 or (minutes_to_throttle is not None and minutes_to_throttle < 60):
            risk = "warning"
        elif cur_util >= 40:
            risk = "caution"
        else:
            risk = "safe"

        rate_5m = rates.get("5m", {})
        self.send_json({
            "utilization": cur_util,
            "remaining_pct": remaining_pct,
            "resets_at": resets_at,
            "profile": profile,
            "rates": rates,
            "minutes_to_throttle": minutes_to_throttle,
            "risk": risk,
            "rpm": rate_5m.get("rpm", 0),
            "tpm": rate_5m.get("tpm", 0),
        })

    # ============================================================
    # v0.6.2 — Prompt Efficiency Analysis
    # ============================================================
    def api_efficiency(self, params):
        """Prompt efficiency analysis: output ratio, cache grade, mode classification"""
        source = params.get("source", ["all"])[0]
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        # Source filtering for totals
        if source != "all":
            claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
            if source == "claude":
                scan["models"] = {m: v for m, v in scan.get("models", {}).items() if m in claude_models}
            elif source == "codex":
                scan["models"] = {m: v for m, v in scan.get("models", {}).items() if m not in claude_models}
            scan["total_input"] = sum(v.get("input", 0) for v in scan["models"].values())
            scan["total_output"] = sum(v.get("output", 0) for v in scan["models"].values())
            scan["total_cache_read"] = sum(v.get("cache_read", 0) for v in scan["models"].values())
            scan["total_cache_create"] = sum(v.get("cache_create", 0) for v in scan["models"].values())
        session_eff = scan.get("session_efficiency", {})

        # 1. Global efficiency metrics
        total_input = scan.get("total_input", 0)
        total_output = scan.get("total_output", 0)
        total_cr = scan.get("total_cache_read", 0)
        total_cc = scan.get("total_cache_create", 0)
        total_all = total_input + total_output + total_cr + total_cc
        output_ratio = round(total_output / total_all * 100, 1) if total_all > 0 else 0
        all_input = total_input + total_cr + total_cc
        cache_rate = round(total_cr / all_input * 100, 1) if all_input > 0 else 0

        if cache_rate >= 80:
            cache_grade = "Excellent"
        elif cache_rate >= 50:
            cache_grade = "Good"
        elif cache_rate >= 20:
            cache_grade = "Fair"
        else:
            cache_grade = "Poor"

        # 2. Per-session mode classification and efficiency ranking
        sessions_ranked = []
        mode_counts = {"exploration": 0, "building": 0, "debugging": 0, "review": 0}
        mode_tokens = {"exploration": 0, "building": 0, "debugging": 0, "review": 0}

        for sid, se in session_eff.items():
            s_in = se.get("input", 0)
            s_out = se.get("output", 0)
            s_cr = se.get("cache_read", 0)
            s_cc = se.get("cache_create", 0)
            s_total = s_in + s_out + s_cr + s_cc
            s_calls = se.get("calls", 0)
            s_tools = se.get("tool_calls", 0)

            if s_total == 0 or s_calls == 0:
                continue

            # Efficiency = output tokens / total tokens (higher = more "productive")
            eff = round(s_out / s_total * 100, 1)

            # Classify interaction mode
            all_in = s_in + s_cr + s_cc
            cache_ratio = s_cr / all_in if all_in > 0 else 0
            tool_ratio = s_tools / s_calls if s_calls > 0 else 0
            out_ratio = s_out / s_total if s_total > 0 else 0

            if s_calls <= 3 and out_ratio < 0.15:
                mode = "exploration"  # Short sessions, mostly reading
            elif tool_ratio > 0.5 and out_ratio > 0.1:
                mode = "building"    # Lots of tool use + output = writing code
            elif s_calls >= 5 and cache_ratio > 0.6:
                mode = "debugging"   # Many rounds, high cache reuse = iterating
            elif s_cc > s_cr and out_ratio < 0.1:
                mode = "review"      # Large cache creation, low output = reading lots of code
            elif tool_ratio > 0.3:
                mode = "building"
            elif cache_ratio > 0.5:
                mode = "debugging"
            else:
                mode = "exploration"

            mode_counts[mode] += 1
            mode_tokens[mode] += s_total

            sessions_ranked.append({
                "session_id": sid,
                "project": se.get("project", ""),
                "calls": s_calls,
                "tool_calls": s_tools,
                "total_tokens": s_total,
                "output_tokens": s_out,
                "efficiency": eff,
                "mode": mode,
                "cache_rate": round(cache_ratio * 100, 1),
            })

        # Sort by efficiency desc, take top/bottom
        sessions_ranked.sort(key=lambda x: x["efficiency"], reverse=True)
        top_efficient = sessions_ranked[:10]
        least_efficient = sessions_ranked[-10:][::-1] if len(sessions_ranked) > 10 else []

        # 3. Efficiency trend by day
        daily = scan.get("daily", {})
        eff_trend = []
        for date in sorted(daily.keys())[-30:]:
            d_tokens = daily[date].get("tokens", {})
            d_out = sum(v.get("output", 0) for v in d_tokens.values())
            d_total = sum(v.get("input", 0) + v.get("output", 0) + v.get("cache_read", 0) + v.get("cache_create", 0) for v in d_tokens.values())
            d_cr = sum(v.get("cache_read", 0) for v in d_tokens.values())
            d_all_in = sum(v.get("input", 0) + v.get("cache_read", 0) + v.get("cache_create", 0) for v in d_tokens.values())
            eff_trend.append({
                "date": date,
                "output_ratio": round(d_out / d_total * 100, 1) if d_total > 0 else 0,
                "cache_rate": round(d_cr / d_all_in * 100, 1) if d_all_in > 0 else 0,
            })

        # 4. Mode totals
        total_mode = sum(mode_counts.values()) or 1
        mode_pct = {k: round(v / total_mode * 100) for k, v in mode_counts.items()}

        self.send_json({
            "global": {
                "output_ratio": output_ratio,
                "cache_rate": cache_rate,
                "cache_grade": cache_grade,
                "total_sessions_analyzed": len(sessions_ranked),
            },
            "modes": {
                "counts": mode_counts,
                "percentages": mode_pct,
                "tokens": mode_tokens,
            },
            "top_efficient": top_efficient,
            "least_efficient": least_efficient,
            "trend": eff_trend,
        })

    # ============================================================
    # v0.7.0 — Cost Optimization Insights
    # ============================================================
    def api_insights(self, params):
        """Smart cost optimization suggestions (pure rule-driven)"""
        source = params.get("source", ["all"])[0]
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        if source != "all":
            claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
            if source == "claude":
                scan["models"] = {m: v for m, v in scan.get("models", {}).items() if m in claude_models}
            elif source == "codex":
                scan["models"] = {m: v for m, v in scan.get("models", {}).items() if m not in claude_models}
        session_eff = scan.get("session_efficiency", {})
        models = scan.get("models", {})
        daily = scan.get("daily", {})
        insights = []

        # Rule 1: Model downgrade — compare actual Opus cost vs hypothetical Sonnet cost
        opus_models = [m for m in models if "opus" in m.lower()]
        sonnet_models = [m for m in models if "sonnet" in m.lower()]
        if opus_models and sonnet_models:
            opus_total_cost = 0.0
            opus_as_sonnet_cost = 0.0
            for om in opus_models:
                md = models[om]
                opus_total_cost += _calc_cost(om, md.get("input", 0), md.get("output", 0), md.get("cache_read", 0), md.get("cache_create", 0))
                opus_as_sonnet_cost += _calc_cost(sonnet_models[0], md.get("input", 0), md.get("output", 0), md.get("cache_read", 0), md.get("cache_create", 0))
            potential_savings = opus_total_cost - opus_as_sonnet_cost
            if potential_savings > 1.0:
                pct_savings = round(potential_savings / opus_total_cost * 100) if opus_total_cost > 0 else 0
                insights.append({
                    "type": "model_downgrade",
                    "severity": "high" if potential_savings > 10 else "medium",
                    "title_en": f"Opus → Sonnet could save {pct_savings}%",
                    "title_zh": f"Opus → Sonnet 可节省 {pct_savings}%",
                    "desc_en": f"Your Opus usage costs ${opus_total_cost:.2f}. The same tokens on Sonnet would cost ${opus_as_sonnet_cost:.2f}, saving ~${potential_savings:.2f}.",
                    "desc_zh": f"Opus 用量成本 ${opus_total_cost:.2f}，同样的 token 在 Sonnet 上仅需 ${opus_as_sonnet_cost:.2f}，可节省约 ${potential_savings:.2f}。",
                    "savings_usd": round(potential_savings, 2),
                    "icon": "ph-swap",
                })

        # Rule 2: Cache optimization — low cache hit rate
        total_input = scan.get("total_input", 0)
        total_cr = scan.get("total_cache_read", 0)
        total_cc = scan.get("total_cache_create", 0)
        all_input = total_input + total_cr + total_cc
        cache_rate = total_cr / all_input * 100 if all_input > 0 else 0
        if cache_rate < 40 and all_input > 100000:
            wasted = (total_input + total_cc) * 0.3 / 1_000_000  # rough savings if cache_read replaced direct input
            insights.append({
                "type": "cache_optimization",
                "severity": "high" if cache_rate < 20 else "medium",
                "title_en": "Improve cache hit rate",
                "title_zh": "提升缓存命中率",
                "desc_en": f"Cache hit rate is only {cache_rate:.0f}%. Longer sessions and consistent project contexts improve caching. Potential savings: ~${wasted:.2f}.",
                "desc_zh": f"缓存命中率仅 {cache_rate:.0f}%。保持较长会话和一致的项目上下文可提高缓存利用率，预计可节省约 ${wasted:.2f}。",
                "savings_usd": round(wasted, 2),
                "icon": "ph-database",
            })

        # Rule 3: Cost anomaly — day with unusually high cost
        if len(daily) >= 7:
            daily_costs = []
            for dt, dd in sorted(daily.items())[-30:]:
                day_cost = 0.0
                for model_name, toks in dd.get("tokens", {}).items():
                    day_cost += _calc_cost(model_name, toks.get("input", 0), toks.get("output", 0),
                                           toks.get("cache_read", 0), toks.get("cache_create", 0))
                daily_costs.append((dt, day_cost))
            if len(daily_costs) >= 7:
                costs_only = [c for _, c in daily_costs]
                avg_cost = sum(costs_only) / len(costs_only)
                max_day, max_cost = max(daily_costs, key=lambda x: x[1])
                if avg_cost > 0 and max_cost > avg_cost * 2.5:
                    insights.append({
                        "type": "cost_anomaly",
                        "severity": "medium",
                        "title_en": f"Cost spike on {max_day}",
                        "title_zh": f"{max_day} 成本异常",
                        "desc_en": f"${max_cost:.2f} — {max_cost/avg_cost:.1f}x the daily average (${avg_cost:.2f}). Consider reviewing that day's sessions.",
                        "desc_zh": f"${max_cost:.2f} — 是日均（${avg_cost:.2f}）的 {max_cost/avg_cost:.1f} 倍。建议检查当日会话。",
                        "savings_usd": 0,
                        "icon": "ph-warning-circle",
                    })

        # Rule 4: Peak hour warning
        history = _load_history()
        hourly = [0] * 24
        for entry in history:
            ts = entry.get("timestamp", 0)
            h, _ = ms_to_hour_dow(ts)
            if h is not None:
                hourly[h] += 1
        peak = hourly.index(max(hourly)) if any(hourly) else -1
        total_h = sum(hourly) or 1
        if peak >= 0 and hourly[peak] / total_h > 0.15:
            insights.append({
                "type": "peak_hour",
                "severity": "low",
                "title_en": f"Peak usage at {peak}:00",
                "title_zh": f"高峰时段: {peak}:00",
                "desc_en": f"{hourly[peak]/total_h*100:.0f}% of activity concentrated at {peak}:00. Spreading usage may reduce rate limit risk.",
                "desc_zh": f"{hourly[peak]/total_h*100:.0f}% 的活动集中在 {peak}:00。分散使用可降低限速风险。",
                "savings_usd": 0,
                "icon": "ph-clock",
            })

        # Sort by severity
        sev_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: sev_order.get(x["severity"], 9))

        self.send_json({"insights": insights, "total": len(insights)})

    # ============================================================
    # v0.7.1 — Token Budget Management
    # ============================================================
    def api_budget_get(self, params):
        """GET /api/budget — current budget config + status"""
        source = params.get("source", ["all"])[0]
        config = _load_config()
        budget = config.get("budget", {})
        if not budget:
            self.send_json({"configured": False, "budget": {}, "status": {}})
            return

        # Compute current spend
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        # Filter daily tokens by source
        if source != "all":
            claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
            for d_data in scan.get("daily", {}).values():
                if "tokens" in d_data:
                    if source == "claude":
                        d_data["tokens"] = {m: v for m, v in d_data["tokens"].items() if m in claude_models}
                    elif source == "codex":
                        d_data["tokens"] = {m: v for m, v in d_data["tokens"].items() if m not in claude_models}
        daily = scan.get("daily", {})
        models_data = scan.get("models", {})
        today_str = datetime.date.today().isoformat()
        now = datetime.date.today()

        # Daily cost
        today_cost = 0.0
        td = daily.get(today_str, {}).get("tokens", {})
        for m, t in td.items():
            today_cost += _calc_cost(m, t.get("input", 0), t.get("output", 0), t.get("cache_read", 0), t.get("cache_create", 0))

        # Weekly cost (Mon-Sun)
        dow = now.weekday()
        week_cost = 0.0
        for i in range(dow + 1):
            d = (now - datetime.timedelta(days=i)).isoformat()
            dd = daily.get(d, {}).get("tokens", {})
            for m, t in dd.items():
                week_cost += _calc_cost(m, t.get("input", 0), t.get("output", 0), t.get("cache_read", 0), t.get("cache_create", 0))

        # Monthly cost
        month_cost = 0.0
        for d_str, dd in daily.items():
            if d_str.startswith(now.strftime("%Y-%m")):
                for m, t in dd.get("tokens", {}).items():
                    month_cost += _calc_cost(m, t.get("input", 0), t.get("output", 0), t.get("cache_read", 0), t.get("cache_create", 0))

        # Build status
        status = {}
        for period in ["daily", "weekly", "monthly"]:
            limit = budget.get(period, 0)
            if not limit:
                continue
            spent = {"daily": today_cost, "weekly": week_cost, "monthly": month_cost}[period]
            pct = round(spent / limit * 100, 1) if limit > 0 else 0
            alert = "over" if pct >= 100 else "danger" if pct >= 80 else "warning" if pct >= 60 else "ok"
            status[period] = {
                "limit": limit,
                "spent": round(spent, 4),
                "pct": min(pct, 999),
                "alert": alert,
            }

        self.send_json({
            "configured": True,
            "budget": budget,
            "status": status,
        })

    def api_budget_post(self, data):
        """POST /api/budget — save budget config"""
        config = _load_config()
        budget = {}
        for period in ["daily", "weekly", "monthly"]:
            val = data.get(period)
            if val is not None:
                budget[period] = float(val) if val else 0
        config["budget"] = budget
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # ============================================================
    # v0.7.2 — Comparison Reports
    # ============================================================
    def api_report(self, params):
        """Weekly/monthly comparison report"""
        report_type = params.get("type", ["weekly"])[0]
        source = params.get("source", ["all"])[0]
        scan = copy.deepcopy(_scan_all_projects())
        codex_scan = _scan_codex() if _codex_enabled() else None
        if codex_scan:
            scan = _merge_codex_into_scan(scan, codex_scan)
        # Filter daily data by source
        claude_models = set()
        if source != "all":
            claude_models = set(_scan_all_projects(force=False).get("models", {}).keys())
            for d_data in scan.get("daily", {}).values():
                if "tokens" in d_data:
                    orig_tokens = d_data["tokens"]
                    if source == "claude":
                        d_data["tokens"] = {m: v for m, v in orig_tokens.items() if m in claude_models}
                    elif source == "codex":
                        d_data["tokens"] = {m: v for m, v in orig_tokens.items() if m not in claude_models}
                    # Scale messages/sessions/tools proportionally by token volume
                    orig_total = sum(t.get("input",0)+t.get("output",0)+t.get("cache_read",0)+t.get("cache_create",0) for t in orig_tokens.values()) or 1
                    filt_total = sum(t.get("input",0)+t.get("output",0)+t.get("cache_read",0)+t.get("cache_create",0) for t in d_data["tokens"].values())
                    ratio = filt_total / orig_total
                    d_data["messages"] = round(d_data.get("messages", 0) * ratio)
                    d_data["sessions"] = max(1, round(d_data.get("sessions", 0) * ratio)) if filt_total > 0 else 0
                    d_data["tools"] = round(d_data.get("tools", 0) * ratio)
        daily = scan.get("daily", {})
        models = scan.get("models", {})
        today = datetime.date.today()

        def _period_stats(start_date, end_date):
            """Aggregate stats for a date range"""
            stats = {"messages": 0, "sessions": 0, "tools": 0, "tokens": 0, "cost": 0.0, "days": 0,
                     "models": {}, "cache_read": 0, "all_input": 0}
            d = start_date
            while d <= end_date:
                ds = d.isoformat()
                dd = daily.get(ds, {})
                if dd and dd.get("tokens"):
                    stats["messages"] += dd.get("messages", 0)
                    stats["sessions"] += dd.get("sessions", 0)
                    stats["tools"] += dd.get("tools", 0)
                    stats["days"] += 1
                    for m, t in dd.get("tokens", {}).items():
                        tok = t.get("input", 0) + t.get("output", 0) + t.get("cache_read", 0) + t.get("cache_create", 0)
                        stats["tokens"] += tok
                        stats["models"][m] = stats["models"].get(m, 0) + tok
                        stats["cost"] += _calc_cost(m, t.get("input", 0), t.get("output", 0),
                                                    t.get("cache_read", 0), t.get("cache_create", 0))
                        stats["cache_read"] += t.get("cache_read", 0)
                        stats["all_input"] += t.get("input", 0) + t.get("cache_read", 0) + t.get("cache_create", 0)
                d += datetime.timedelta(days=1)
            stats["cost"] = round(stats["cost"], 4)
            return stats

        def _delta(cur, prev):
            """Compute delta percentage"""
            if prev == 0:
                return 100.0 if cur > 0 else 0.0
            return round((cur - prev) / prev * 100, 1)

        if report_type == "weekly":
            dow = today.weekday()
            this_start = today - datetime.timedelta(days=dow)
            this_end = today
            last_start = this_start - datetime.timedelta(days=7)
            last_end = this_start - datetime.timedelta(days=1)
            period_label_en = f"Week of {this_start.isoformat()}"
            period_label_zh = f"{this_start.isoformat()} 起的一周"
        else:  # monthly
            this_start = today.replace(day=1)
            this_end = today
            last_month = (this_start - datetime.timedelta(days=1))
            last_start = last_month.replace(day=1)
            last_end = last_month
            period_label_en = today.strftime("%B %Y")
            period_label_zh = today.strftime("%Y年%m月")

        current = _period_stats(this_start, this_end)
        previous = _period_stats(last_start, last_end)

        # Deltas
        deltas = {
            "messages": _delta(current["messages"], previous["messages"]),
            "sessions": _delta(current["sessions"], previous["sessions"]),
            "tokens": _delta(current["tokens"], previous["tokens"]),
            "cost": _delta(current["cost"], previous["cost"]),
            "tools": _delta(current["tools"], previous["tools"]),
        }

        # Highlights
        highlights = []
        # Most active model
        if current["models"]:
            top_model = max(current["models"], key=current["models"].get)
            highlights.append({
                "label_en": "Top Model", "label_zh": "最活跃模型",
                "value": top_model.replace("claude-", "").replace("-20250", ""),
                "icon": "ph-cpu",
            })

        # Cache rate for this period (not global)
        total_cr = current.get("cache_read", 0)
        all_in = current.get("all_input", 0)
        if all_in > 0:
            highlights.append({
                "label_en": "Cache Rate", "label_zh": "缓存命中率",
                "value": f"{total_cr / all_in * 100:.0f}%",
                "icon": "ph-database",
            })

        # Avg cost per day
        if current["days"] > 0:
            avg_daily = current["cost"] / current["days"]
            highlights.append({
                "label_en": "Avg Daily Cost", "label_zh": "日均成本",
                "value": f"${avg_daily:.2f}",
                "icon": "ph-coins",
            })

        # Most productive day
        best_day = ""
        best_day_msgs = 0
        d = this_start
        while d <= this_end:
            ds = d.isoformat()
            dd = daily.get(ds, {})
            if dd.get("messages", 0) > best_day_msgs:
                best_day_msgs = dd["messages"]
                best_day = ds
            d += datetime.timedelta(days=1)
        if best_day:
            highlights.append({
                "label_en": "Most Active Day", "label_zh": "最活跃日",
                "value": f"{best_day} ({best_day_msgs} msgs)",
                "icon": "ph-fire",
            })

        self.send_json({
            "type": report_type,
            "period_label_en": period_label_en,
            "period_label_zh": period_label_zh,
            "current": current,
            "previous": previous,
            "deltas": deltas,
            "highlights": highlights,
            "range": {
                "current": {"start": this_start.isoformat(), "end": this_end.isoformat()},
                "previous": {"start": last_start.isoformat(), "end": last_end.isoformat()},
            }
        })


    # ============================================================
    # v0.8.0 — Git Integration Analysis
    # ============================================================
    def api_git_stats(self, params):
        """Correlate git commits with Claude sessions by time window"""
        project_filter = params.get("project", [""])[0]
        days = int(params.get("days", ["30"])[0])

        scan = _scan_all_projects()
        daily = scan.get("daily", {})
        session_eff = scan.get("session_efficiency", {})

        # Find projects with .git directories
        git_projects = []
        if PROJECTS_DIR.exists():
            for proj_dir in PROJECTS_DIR.iterdir():
                if not proj_dir.is_dir():
                    continue
                fname = friendly_project_name(proj_dir.name)
                if project_filter and project_filter not in fname:
                    continue
                # Reconstruct actual path from dir name by reading cwd from first JSONL
                actual_path = None
                for jf in proj_dir.glob("*.jsonl"):
                    try:
                        with open(jf, "r", encoding="utf-8", errors="replace") as jfh:
                            for jline in jfh:
                                try:
                                    jevt = json.loads(jline.strip())
                                    cwd = jevt.get("cwd", "")
                                    if cwd and Path(cwd).exists():
                                        actual_path = cwd
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        continue
                    if actual_path:
                        break
                if not actual_path:
                    continue
                git_dir = Path(actual_path) / ".git"
                if not git_dir.exists():
                    continue
                git_projects.append({"dir_name": proj_dir.name, "friendly": fname, "path": actual_path})

        if not git_projects:
            self.send_json({"projects": [], "commits": [], "summary": {}})
            return

        # Pre-compute daily cost per project for proportional attribution
        daily_project_cost = {}  # (date, project) -> total_cost
        daily_project_tokens = {}
        for d_str, dd in daily.items():
            for m, t in dd.get("tokens", {}).items():
                c = _calc_cost(m, t.get("input", 0), t.get("output", 0), t.get("cache_read", 0), t.get("cache_create", 0))
                tok = t.get("input", 0) + t.get("output", 0) + t.get("cache_read", 0) + t.get("cache_create", 0)
                # Attribute to all projects equally for this day (approximation)
                daily_project_cost[d_str] = daily_project_cost.get(d_str, 0) + c
                daily_project_tokens[d_str] = daily_project_tokens.get(d_str, 0) + tok

        # Count commits per day to split cost evenly
        cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        day_commit_counts = {}  # date -> commit count
        raw_commits = []

        for gp in git_projects:
            try:
                result = subprocess.run(
                    ["git", "-C", gp["path"], "log", f"--since={cutoff}",
                     "--format=%H|%aI|%s", "--no-merges"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    continue
                for line in result.stdout.strip().split("\n"):
                    if not line or "|" not in line:
                        continue
                    parts = line.split("|", 2)
                    if len(parts) < 3:
                        continue
                    commit_hash, commit_ts, subject = parts
                    commit_date = commit_ts[:10]
                    day_commit_counts[commit_date] = day_commit_counts.get(commit_date, 0) + 1
                    raw_commits.append((commit_hash, commit_ts, commit_date, subject, gp["friendly"]))
            except Exception:
                continue

        # Assign cost per commit = daily_cost / commits_that_day
        all_commits = []
        for commit_hash, commit_ts, commit_date, subject, project in raw_commits:
            day_cost = daily_project_cost.get(commit_date, 0)
            day_tokens = daily_project_tokens.get(commit_date, 0)
            n_commits = day_commit_counts.get(commit_date, 1)
            all_commits.append({
                "hash": commit_hash[:8],
                "date": commit_date,
                "timestamp": commit_ts,
                "subject": subject[:80],
                "project": project,
                "ai_cost": round(day_cost / n_commits, 4),
                "ai_tokens": round(day_tokens / n_commits),
            })

        all_commits.sort(key=lambda c: c["timestamp"], reverse=True)
        # Deduplicate by hash (worktrees may report same commit from multiple dirs)
        seen_hashes = set()
        deduped = []
        for c in all_commits:
            if c["hash"] not in seen_hashes:
                seen_hashes.add(c["hash"])
                deduped.append(c)
        all_commits = deduped

        # Summary
        total_commits = len(all_commits)
        total_ai_cost = sum(c["ai_cost"] for c in all_commits)
        ai_assisted = sum(1 for c in all_commits if c["ai_cost"] > 0)

        # Daily commit + cost trend
        daily_git = {}
        for c in all_commits:
            d = daily_git.setdefault(c["date"], {"commits": 0, "ai_cost": 0.0})
            d["commits"] += 1
            d["ai_cost"] += c["ai_cost"]
        trend = [{"date": d, "commits": v["commits"], "ai_cost": round(v["ai_cost"], 2)}
                 for d, v in sorted(daily_git.items())]

        self.send_json({
            "projects": [gp["friendly"] for gp in git_projects],
            "commits": all_commits[:100],
            "trend": trend,
            "summary": {
                "total_commits": total_commits,
                "total_ai_cost": round(total_ai_cost, 2),
                "ai_assisted_pct": round(ai_assisted / total_commits * 100) if total_commits > 0 else 0,
                "avg_cost_per_commit": round(total_ai_cost / total_commits, 2) if total_commits > 0 else 0,
                "projects_count": len(git_projects),
            },
        })

    # ============================================================
    # v0.8.1 — Webhook & Notifications
    # ============================================================
    def api_webhooks_post(self, data):
        """POST /api/webhooks — save webhook config or test"""
        action = data.get("action", "save")

        if action == "test":
            url = data.get("url", "")
            if not url:
                self.send_json({"error": "URL required"}, 400)
                return
            try:
                payload = json.dumps({
                    "type": "test",
                    "message": "CCDash webhook test",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload,
                                            headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    self.send_json({"ok": True, "status": resp.status})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})
            return

        # Save webhook config
        config = _load_config()
        webhooks = data.get("webhooks", [])
        config["webhooks"] = webhooks
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.send_json({"ok": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # ============================================================
    # v0.9.0 — Multi-Account Support
    # ============================================================
    def api_accounts(self, params):
        """Get all configured accounts with their quota status"""
        config = _load_config()
        accounts = config.get("accounts", [])
        if not accounts:
            sk = config.get("claude_session_key", "")
            oid = config.get("claude_org_id", "")
            if sk and oid:
                accounts = [{"name": "Default", "session_key": sk, "org_id": oid}]
            else:
                self.send_json({"accounts": [], "configured": False})
                return
        results = []
        for acc in accounts:
            name = acc.get("name", "Account")
            sk = acc.get("session_key", "")
            oid = acc.get("org_id", "")
            quota = {"utilization": 0, "error": None}
            if sk and oid:
                swift_path = DASHBOARD_DIR / "fetch-usage.swift"
                if swift_path.exists():
                    try:
                        env = os.environ.copy()
                        env["CLAUDE_SESSION_KEY"] = sk
                        env["CLAUDE_ORG_ID"] = oid
                        result = subprocess.run(
                            ["swift", str(swift_path)],
                            capture_output=True, text=True, timeout=15,
                            cwd=str(DASHBOARD_DIR), env=env
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            quota = json.loads(result.stdout.strip())
                        else:
                            quota["error"] = result.stderr.strip() or "unknown"
                    except Exception as e:
                        quota["error"] = str(e)
            results.append({
                "name": name,
                "org_id_masked": oid[:8] + "..." if len(oid) > 8 else oid,
                "quota": quota,
            })
        self.send_json({"accounts": results, "configured": True})

    # ============================================================
    # v0.9.2 — Plugin System
    # ============================================================
    def api_plugins(self, params):
        """List discovered plugins and their status"""
        plugins_dir = DASHBOARD_DIR / "plugins"
        plugins = []
        plugins.append({"name": "Claude Code", "type": "builtin", "enabled": True,
                         "status": "active" if PROJECTS_DIR.exists() else "no_data",
                         "description": "Claude Code CLI session data from ~/.claude/"})
        plugins.append({"name": "Codex CLI", "type": "builtin", "enabled": _codex_enabled(),
                         "status": "active" if _codex_enabled() else "not_detected",
                         "description": "OpenAI Codex CLI data from ~/.codex/"})
        if plugins_dir.exists():
            for pf in sorted(plugins_dir.glob("*.py")):
                if pf.name.startswith("_"):
                    continue
                meta = {"name": pf.stem, "description": "", "version": ""}
                try:
                    with open(pf, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("# name:"):
                                meta["name"] = line.split(":", 1)[1].strip()
                            elif line.startswith("# description:"):
                                meta["description"] = line.split(":", 1)[1].strip()
                            elif line.startswith("# version:"):
                                meta["version"] = line.split(":", 1)[1].strip()
                            elif not line.startswith("#"):
                                break
                except Exception:
                    pass
                config = _load_config()
                plugin_cfg = config.get("plugins", {}).get(pf.stem, {})
                enabled = plugin_cfg.get("enabled", False)
                plugins.append({"name": meta["name"], "type": "custom", "file": pf.name,
                                 "enabled": enabled, "status": "active" if enabled else "disabled",
                                 "description": meta["description"], "version": meta["version"]})
        self.send_json({"plugins": plugins, "plugins_dir": str(plugins_dir)})


# Webhook notification sender (called from background thread)
_webhook_last_check = {"time": 0}
WEBHOOK_CHECK_INTERVAL = 300  # 5 minutes

def _check_webhook_triggers():
    """Background check for webhook trigger conditions"""
    now = time.time()
    if now - _webhook_last_check["time"] < WEBHOOK_CHECK_INTERVAL:
        return
    _webhook_last_check["time"] = now

    config = _load_config()
    webhooks = config.get("webhooks", [])
    if not webhooks:
        return

    active = [w for w in webhooks if w.get("enabled", True)]
    if not active:
        return

    # Check triggers
    alerts = []

    # Trigger 1: Quota > threshold
    try:
        if USAGE_CACHE_FILE.exists():
            with open(USAGE_CACHE_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("UTILIZATION="):
                        util = int(line.split("=", 1)[1])
                        if util >= 80:
                            alerts.append({
                                "type": "quota_warning",
                                "message": f"⚠️ Quota at {util}% — approaching rate limit",
                                "severity": "danger" if util >= 95 else "warning",
                            })
    except Exception:
        pass

    # Trigger 2: Budget overrun
    budget = config.get("budget", {})
    if budget:
        try:
            scan = _scan_all_projects()
            today_str = datetime.date.today().isoformat()
            td = scan.get("daily", {}).get(today_str, {}).get("tokens", {})
            today_cost = sum(_calc_cost(m, t.get("input", 0), t.get("output", 0),
                                        t.get("cache_read", 0), t.get("cache_create", 0))
                             for m, t in td.items())
            daily_limit = budget.get("daily", 0)
            if daily_limit and today_cost > daily_limit:
                alerts.append({
                    "type": "budget_exceeded",
                    "message": f"💰 Daily budget exceeded: ${today_cost:.2f} / ${daily_limit:.2f}",
                    "severity": "danger",
                })
        except Exception:
            pass

    # Send alerts
    for alert in alerts:
        payload = json.dumps({
            **alert,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "CCDash",
        }).encode("utf-8")
        for w in active:
            url = w.get("url", "")
            if not url:
                continue
            # Check if this webhook listens to this alert type
            events = w.get("events", ["all"])
            if "all" not in events and alert["type"] not in events:
                continue
            try:
                headers = {"Content-Type": "application/json"}
                # Slack format
                if "slack" in url.lower() or w.get("format") == "slack":
                    payload = json.dumps({"text": alert["message"]}).encode("utf-8")
                # Discord format
                elif "discord" in url.lower() or w.get("format") == "discord":
                    payload = json.dumps({"content": alert["message"]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                urllib.request.urlopen(req, timeout=10)
            except Exception:
                pass


def _webhook_background_loop():
    """Background thread that periodically checks webhook triggers"""
    while True:
        try:
            _check_webhook_triggers()
        except Exception:
            pass
        time.sleep(WEBHOOK_CHECK_INTERVAL)


# ============================================================
# 启动
# ============================================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    print("=" * 50)
    print("  Claude Usage Dashboard")
    print("=" * 50)
    print(f"  数据目录: {CLAUDE_DIR}")
    print(f"  项目目录: {PROJECTS_DIR}")

    # 预检
    if PROJECTS_DIR.exists():
        proj_count = sum(1 for d in PROJECTS_DIR.iterdir() if d.is_dir())
        print(f"  发现 {proj_count} 个项目目录")
    else:
        print("  ⚠ 项目目录不存在")

    if USAGE_CACHE_FILE.exists():
        print("  ✅ 实时使用率缓存可用")
    else:
        print("  ⚠ 实时使用率缓存不可用")

    if HISTORY_FILE.exists():
        line_count = sum(1 for _ in open(HISTORY_FILE))
        print(f"  ✅ 历史记录: {line_count} 条")
    else:
        print("  ⚠ 历史记录不存在")

    # Codex CLI detection
    if CODEX_SESSIONS_DIR.exists() or CODEX_ARCHIVED_DIR.exists():
        codex_files = list(CODEX_SESSIONS_DIR.rglob("rollout-*.jsonl")) if CODEX_SESSIONS_DIR.exists() else []
        codex_files += list(CODEX_ARCHIVED_DIR.rglob("rollout-*.jsonl")) if CODEX_ARCHIVED_DIR.exists() else []
        print(f"  ✅ Codex CLI: {len(codex_files)} 会话文件 (model: {_read_codex_model()})")
    else:
        print("  ⚠ Codex CLI 数据目录不存在")

    print()
    print(f"  🌐 Dashboard: http://localhost:{PORT}")
    print(f"  按 Ctrl+C 停止")
    print()

    # 后台预扫描
    threading.Thread(target=_scan_all_projects, daemon=True).start()
    if _codex_enabled():
        threading.Thread(target=_scan_codex, daemon=True).start()
    # Webhook background checker
    config = _load_config()
    if config.get("webhooks"):
        threading.Thread(target=_webhook_background_loop, daemon=True).start()
        print("  📡 Webhook 通知已启用")

    server = ThreadedHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard 已停止")


if __name__ == "__main__":
    main()

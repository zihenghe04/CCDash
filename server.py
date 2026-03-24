#!/usr/bin/env python3
"""CCDash — Open-source usage analytics dashboard for Claude Code CLI"""

import json
import os
import time
import datetime
import threading
import urllib.parse
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
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
WEB_DIR = SCRIPT_DIR / "web"

# ============================================================
# 缓存
# ============================================================
_scan_cache = {"data": None, "time": 0, "file_mtimes": {}}
_scan_lock = threading.Lock()
SCAN_TTL = 300  # 5 minutes

_live_cache = {"data": None, "time": 0}
LIVE_TTL = 10

_history_cache = {"data": None, "time": 0, "mtime": 0}
HISTORY_TTL = 60

_remote_cache = {}  # {url: {"data": ..., "time": ...}}
REMOTE_TTL = 15

_claude_usage_cache = {"data": None, "time": 0}
CLAUDE_USAGE_TTL = 60


# ============================================================
# 远程 Agent 聚合
# ============================================================
def _load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {"remotes": []}


def _fetch_remote(url, token=None, timeout=5):
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
    """"-Users-czx-Desktop-SEU-Thesis-LaTeX" → "SEU-Thesis-LaTeX" """
    parts = dir_name.strip("-").split("-")
    # 找到最后一个有意义的段
    # 跳过 Users, czx, Desktop, Documents 等路径前缀
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
# Model pricing (per million tokens, USD)
# ============================================================
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
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_create": 3.75}

def _calc_cost(model, inp, out, cache_read, cache_create):
    """Calculate equivalent API cost in USD"""
    p = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return (inp * p["input"] + out * p["output"] +
            cache_read * p["cache_read"] + cache_create * p["cache_create"]) / 1_000_000


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
    projects = {}    # project_dir_name -> {messages, tokens_total, sessions: set, friendly_name}
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
                                tool_count = sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use")
                                if tool_count and date:
                                    daily.setdefault(date, {
                                        "messages": 0, "sessions": set(), "tools": 0,
                                        "tokens": {}
                                    })
                                    daily[date]["tools"] += tool_count

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

            except Exception as e:
                # 跳过损坏的文件
                continue

            total_sessions.add(session_id)

    # 转换 set → count
    for d in daily.values():
        d["sessions"] = len(d.pop("sessions", set()))
    for p in projects.values():
        p["sessions"] = len(p.pop("sessions", set()))

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
                        })
            except Exception:
                continue

    calls.sort(key=lambda x: x["timestamp"], reverse=True)
    _logs_cache["data"] = calls
    _logs_cache["time"] = time.time()
    return calls


# ============================================================
# Claude.ai Usage API
# ============================================================
def _fetch_claude_usage():
    """Fetch usage data from claude.ai via Swift script (bypasses Cloudflare)"""
    now = time.time()
    if _claude_usage_cache["data"] and (now - _claude_usage_cache["time"]) < CLAUDE_USAGE_TTL:
        return _claude_usage_cache["data"]

    swift_path = SCRIPT_DIR / "fetch-usage.swift"
    if not swift_path.exists():
        return {"error": "swift_script_missing", "stale": True}

    try:
        result = subprocess.run(
            ["swift", str(swift_path)],
            capture_output=True, text=True, timeout=15,
            cwd=str(SCRIPT_DIR)
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
# HTTP Handler
# ============================================================
class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

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
            "/api/hourly": self.api_hourly,
            "/api/live": self.api_live,
            "/api/logs": self.api_logs,
            "/api/claude-usage": self.api_claude_usage,
        }

        handler = routes.get(path)
        if handler:
            try:
                handler(params)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            # 静态文件（index.html 等）
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

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
        """概览卡片（聚合本地 + 远程）"""
        force = "refresh" in params
        if force:
            _clear_all_caches()
        scan = _scan_all_projects(force=force)
        today_str = datetime.date.today().isoformat()
        today_data = scan["daily"].get(today_str, {})

        # Compute RPM, TPM, avg_duration from recent logs
        try:
            logs = _scan_all_logs()
            now = datetime.datetime.now(datetime.timezone.utc)
            recent_5m = [c for c in logs if c.get("timestamp") and
                         (now - parse_iso_ts(c["timestamp"])).total_seconds() < 300]
            rpm = round(len(recent_5m) / 5, 1) if recent_5m else 0
            tpm_val = sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) for c in recent_5m)
            tpm = round(tpm_val / 5) if recent_5m else 0
            durations = [c["duration_ms"] for c in logs[:100] if c.get("duration_ms")]
            avg_duration = round(sum(durations) / len(durations)) if durations else 0
            avg_ttft = 0
            ttfts = [c["ttft_ms"] for c in logs[:100] if c.get("ttft_ms")]
            avg_ttft = round(sum(ttfts) / len(ttfts)) if ttfts else 0
        except Exception:
            rpm, tpm, avg_duration, avg_ttft = 0, 0, 0, 0

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
            "today_messages": today_data.get("messages", 0),
            "today_sessions": today_data.get("sessions", 0),
            "today_tools": today_data.get("tools", 0),
            "rpm": rpm,
            "tpm": tpm,
            "avg_duration_ms": avg_duration,
            "avg_ttft_ms": avg_ttft,
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

        # 聚合远程
        remotes = _get_active_remotes()
        remote_overviews = []
        for r in remotes:
            rd = _fetch_remote_cached(r["url"], "/api/overview", r.get("token"))
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
        scan = _scan_all_projects()
        daily = scan["daily"]

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
        remote_daily = [_fetch_remote_cached(r["url"], f"/api/daily?days={days}", r.get("token")) for r in remotes]
        remote_daily = [rd for rd in remote_daily if rd]
        if remote_daily:
            activity, tokens = _merge_daily(activity, tokens, remote_daily)
            activity = activity[-days:]
            tokens = tokens[-days:]

        self.send_json({"activity": activity, "tokens": tokens})

    def api_models(self, params):
        """模型用量明细（聚合远程）"""
        scan = _scan_all_projects()
        models = scan["models"]
        remotes = _get_active_remotes()
        remote_models = [_fetch_remote_cached(r["url"], "/api/models", r.get("token")) for r in remotes]
        models = _merge_models(models, [rd for rd in remote_models if rd])
        # Add cost per model
        for m_name, m_data in models.items():
            m_data["cost_usd"] = round(_calc_cost(
                m_name, m_data.get("input", 0), m_data.get("output", 0),
                m_data.get("cache_read", 0), m_data.get("cache_create", 0)
            ), 4)
        self.send_json({"models": models})

    def api_projects(self, params):
        """项目用量分布"""
        scan = _scan_all_projects()
        # 按 token 总量排序
        sorted_projects = sorted(
            scan["projects"].items(),
            key=lambda x: x[1]["tokens_total"],
            reverse=True
        )
        result = []
        for proj_dir, info in sorted_projects[:20]:
            result.append({
                "dir_name": proj_dir,
                "name": info["friendly_name"],
                "messages": info["messages"],
                "sessions": info["sessions"],
                "tokens_total": info["tokens_total"],
            })
        # 聚合远程
        remotes = _get_active_remotes()
        remote_proj = []
        for r in remotes:
            rd = _fetch_remote_cached(r["url"], "/api/projects", r.get("token"))
            if rd:
                rd["_remote_name"] = r.get("name", "cloud")
                remote_proj.append(rd)
        if remote_proj:
            result = _merge_projects(result, remote_proj)
        self.send_json({"projects": result})

    def api_sessions(self, params):
        """会话列表（支持搜索、项目过滤、日期范围）"""
        limit = int(params.get("limit", ["50"])[0])
        project_filter = params.get("project", [""])[0]
        search_query = params.get("q", [""])[0].lower()
        # 日期范围: "1d", "7d", "30d", 或 "2026-03-20,2026-03-24"
        date_range = params.get("range", [""])[0]

        history = _load_history()

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
            })
            if len(unique_sessions) >= limit:
                break

        # 收集所有项目路径用于筛选
        all_projects = list(set(e.get("project", "") for e in history if e.get("project")))
        all_projects.sort()

        self.send_json({
            "sessions": unique_sessions,
            "projects": all_projects,
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
        """今日实时调用（聚合远程）"""
        data = _scan_today()
        remotes = _get_active_remotes()
        remote_live = [_fetch_remote_cached(r["url"], "/api/live", r.get("token")) for r in remotes]
        remote_live = [rd for rd in remote_live if rd]
        if remote_live:
            data = _merge_live(data, remote_live)
        self.send_json(data)

    def api_logs(self, params):
        """带过滤与分页的用量日志"""
        limit = int(params.get("limit", ["50"])[0])
        offset = int(params.get("offset", ["0"])[0])
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


    def api_claude_usage(self, params):
        """Claude.ai weekly usage from official API"""
        data = _fetch_claude_usage()
        self.send_json(data)


# ============================================================
# 启动
# ============================================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    print("=" * 50)
    print("  CCDash - CLI Code Dashboard")
    print("=" * 50)
    print(f"  Data dir:    {CLAUDE_DIR}")
    print(f"  Projects:    {PROJECTS_DIR}")
    print(f"  Config:      {CONFIG_FILE}")
    print(f"  Web dir:     {WEB_DIR}")

    # Pre-flight checks
    if PROJECTS_DIR.exists():
        proj_count = sum(1 for d in PROJECTS_DIR.iterdir() if d.is_dir())
        print(f"  Found {proj_count} project directories")
    else:
        print("  [!] Projects directory not found")

    if USAGE_CACHE_FILE.exists():
        print("  [OK] Usage rate cache available")
    else:
        print("  [!] Usage rate cache not available")

    if HISTORY_FILE.exists():
        line_count = sum(1 for _ in open(HISTORY_FILE))
        print(f"  [OK] History: {line_count} entries")
    else:
        print("  [!] History file not found")

    print()
    print(f"  Dashboard: http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop")
    print()

    # Background pre-scan
    threading.Thread(target=_scan_all_projects, daemon=True).start()

    server = ThreadedHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  CCDash stopped")


if __name__ == "__main__":
    main()

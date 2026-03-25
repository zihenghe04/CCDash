#!/usr/bin/env python3
"""Claude Usage Agent — 部署在远程服务器上的轻量数据采集 API

用法:
  python3 agent.py                    # 默认端口 8421
  python3 agent.py --port 8421        # 自定义端口
  python3 agent.py --token mysecret   # 加 token 认证

Dashboard 配置 (本地 config.json):
  {"remotes": [{"name": "云服务器", "url": "http://your-server:8421", "token": "mysecret"}]}
"""

import json
import os
import sys
import time
import datetime
import threading
import urllib.parse
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
USAGE_CACHE_FILE = CLAUDE_DIR / ".statusline-usage-cache"

AUTH_TOKEN = None  # 设为 None 表示不验证

# ============================================================
# Model pricing (same as server.py)
# ============================================================
MODEL_PRICING = {
    "claude-opus-4-6":            {"input": 5.0,  "output": 25.0,  "cache_read": 0.50,  "cache_create": 6.25},
    "claude-opus-4-5-20251101":   {"input": 5.0,  "output": 25.0,  "cache_read": 0.50,  "cache_create": 6.25},
    "claude-sonnet-4-6":          {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-sonnet-4-5":          {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-sonnet-4-5-20250929": {"input": 3.0,  "output": 15.0,  "cache_read": 0.30,  "cache_create": 3.75},
    "claude-haiku-4-5-20251001":  {"input": 1.0,  "output": 5.0,   "cache_read": 0.10,  "cache_create": 1.25},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_create": 3.75}

def _calc_cost(model, inp, out, cache_read, cache_create):
    p = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return (inp * p["input"] + out * p["output"] + cache_read * p["cache_read"] + cache_create * p["cache_create"]) / 1_000_000

# ============================================================
# 缓存
# ============================================================
_scan_cache = {"data": None, "time": 0}
_scan_lock = threading.Lock()
SCAN_TTL = 300

_live_cache = {"data": None, "time": 0}
LIVE_TTL = 30


# ============================================================
# 工具函数（与 server.py 相同）
# ============================================================
def friendly_project_name(dir_name):
    parts = dir_name.strip("-").split("-")
    skip = {"users", "user", "home", "root", "desktop", "documents", "downloads", "projects", "workspace"}
    meaningful = [p for p in parts if p.lower() not in skip and len(p) > 1]
    return "-".join(meaningful[-3:]) if meaningful else dir_name


def ts_to_date(ts_str):
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(ts_str).strftime("%Y-%m-%d")
    except Exception:
        return ""


def ms_to_date(ms):
    try:
        return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""


def ms_to_hour_dow(ms):
    try:
        dt = datetime.datetime.fromtimestamp(ms / 1000)
        return dt.hour, dt.weekday()
    except Exception:
        return None, None


# ============================================================
# 扫描器
# ============================================================
def _scan_all(force=False):
    now = time.time()
    with _scan_lock:
        if not force and _scan_cache["data"] and (now - _scan_cache["time"]) < SCAN_TTL:
            return _scan_cache["data"]

    daily = {}
    models = {}
    projects = {}
    total_messages = 0
    total_sessions = set()
    total_tokens = 0

    if not PROJECTS_DIR.exists():
        result = {"daily": {}, "models": {}, "projects": {},
                  "total_messages": 0, "total_sessions": 0, "total_tokens": 0}
        with _scan_lock:
            _scan_cache.update(data=result, time=time.time())
        return result

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        proj_name = project_dir.name
        friendly = friendly_project_name(proj_name)

        for jsonl_file in project_dir.glob("*.jsonl"):
            session_id = jsonl_file.stem
            session_dates = set()
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
                            session_dates.add(date)
                            daily.setdefault(date, {"messages": 0, "sessions": set(), "tools": 0, "tokens": {}})
                            daily[date]["messages"] += 1
                            daily[date]["sessions"].add(session_id)
                            projects.setdefault(proj_name, {"messages": 0, "tokens_total": 0, "sessions": set(), "friendly_name": friendly})
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
                            tok = inp + out + cr + cc
                            total_tokens += tok

                            content = msg.get("content", [])
                            if isinstance(content, list):
                                tc = sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use")
                                if tc and date:
                                    daily.setdefault(date, {"messages": 0, "sessions": set(), "tools": 0, "tokens": {}})
                                    daily[date]["tools"] += tc

                            if date:
                                daily.setdefault(date, {"messages": 0, "sessions": set(), "tools": 0, "tokens": {}})
                                tm = daily[date]["tokens"].setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0})
                                tm["input"] += inp
                                tm["output"] += out
                                tm["cache_read"] += cr
                                tm["cache_create"] += cc

                            models.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0})
                            models[model]["input"] += inp
                            models[model]["output"] += out
                            models[model]["cache_read"] += cr
                            models[model]["cache_create"] += cc
                            models[model]["calls"] += 1

                            if proj_name in projects:
                                projects[proj_name]["tokens_total"] += tok
            except Exception:
                continue
            total_sessions.add(session_id)

    for d in daily.values():
        d["sessions"] = len(d.pop("sessions", set()))
    for p in projects.values():
        p["sessions"] = len(p.pop("sessions", set()))

    result = {
        "daily": daily, "models": models, "projects": projects,
        "total_messages": total_messages, "total_sessions": len(total_sessions),
        "total_tokens": total_tokens,
    }
    with _scan_lock:
        _scan_cache.update(data=result, time=time.time())
    return result


def _scan_today():
    now = time.time()
    if _live_cache["data"] and (now - _live_cache["time"]) < LIVE_TTL:
        return _live_cache["data"]

    today = datetime.date.today()
    today_str = today.isoformat()
    calls = []
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0, "calls": 0}

    def _parse_iso(s):
        try:
            s = s.replace("Z", "+00:00")
            return datetime.datetime.fromisoformat(s)
        except Exception:
            return None

    if PROJECTS_DIR.exists():
        for pd in PROJECTS_DIR.iterdir():
            if not pd.is_dir():
                continue
            pf = friendly_project_name(pd.name)
            for jf in pd.glob("*.jsonl"):
                try:
                    if datetime.date.fromtimestamp(jf.stat().st_mtime) != today:
                        continue
                except Exception:
                    continue
                try:
                    # Read all events from this file
                    events = []
                    with open(jf, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                events.append(json.loads(line))
                            except:
                                continue

                    # Pass 1: collect turn_duration events
                    turn_durations = {}
                    for evt in events:
                        if evt.get("type") == "system" and evt.get("subtype") == "turn_duration":
                            parent = evt.get("parentUuid", "")
                            if parent:
                                turn_durations[parent] = evt.get("durationMs", 0)

                    # Pass 2: match user→assistant for TTFT/duration
                    last_user_ts = None
                    for evt in events:
                        t = evt.get("type", "")
                        ts = evt.get("timestamp", "")

                        if t == "user":
                            last_user_ts = _parse_iso(ts)

                        elif t == "assistant" and "message" in evt:
                            if not ts or not ts.startswith(today_str):
                                continue
                            msg = evt["message"]
                            if not isinstance(msg, dict):
                                continue
                            usage = msg.get("usage", {})
                            inp = usage.get("input_tokens", 0) or 0
                            out = usage.get("output_tokens", 0) or 0
                            cr = usage.get("cache_read_input_tokens", 0) or 0
                            cc = usage.get("cache_creation_input_tokens", 0) or 0
                            if not inp and not out:
                                continue

                            # TTFT
                            ttft_ms = None
                            assistant_dt = _parse_iso(ts)
                            if last_user_ts and assistant_dt:
                                ttft_ms = int((assistant_dt - last_user_ts).total_seconds() * 1000)
                                if ttft_ms < 0:
                                    ttft_ms = None

                            # Duration: prefer turn_duration, fallback to TTFT
                            duration_ms = None
                            evt_uuid = evt.get("uuid", "")
                            parent_uuid = evt.get("parentUuid", "")
                            if evt_uuid in turn_durations:
                                duration_ms = turn_durations[evt_uuid]
                            elif parent_uuid in turn_durations:
                                duration_ms = turn_durations[parent_uuid]
                            if duration_ms is None:
                                duration_ms = ttft_ms

                            model = msg.get("model", "?")
                            row_cost = round(_calc_cost(model, inp, out, cr, cc), 6)
                            calls.append({"timestamp": ts, "model": model, "project": pf,
                                          "input_tokens": inp, "output_tokens": out, "cache_read": cr, "cache_create": cc,
                                          "cost_usd": row_cost, "status": 200,
                                          "ttft_ms": ttft_ms, "duration_ms": duration_ms})
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
    _live_cache.update(data=result, time=time.time())
    return result


def _load_history():
    entries = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except:
                            pass
        except Exception:
            pass
    return entries


# ============================================================
# HTTP Handler
# ============================================================
class AgentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静默日志

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Token 认证
        if AUTH_TOKEN:
            auth = self.headers.get("Authorization", "")
            if auth != f"Bearer {AUTH_TOKEN}":
                self.send_json({"error": "Unauthorized"}, 401)
                return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        try:
            if path == "/api/ping":
                self.send_json({"ok": True, "hostname": os.uname().nodename,
                                "timestamp": time.time()})
            elif path == "/api/status":
                self._api_status()
            elif path == "/api/overview":
                scan = _scan_all(force="refresh" in params)
                today_str = datetime.date.today().isoformat()
                td = scan["daily"].get(today_str, {})
                total_cost = sum(_calc_cost(m, v.get("input",0), v.get("output",0), v.get("cache_read",0), v.get("cache_create",0)) for m,v in scan["models"].items())
                self.send_json({
                    "total_messages": scan["total_messages"],
                    "total_sessions": scan["total_sessions"],
                    "total_tokens": scan["total_tokens"],
                    "total_projects": len(scan["projects"]),
                    "total_models": len(scan["models"]),
                    "today_messages": td.get("messages", 0),
                    "today_sessions": td.get("sessions", 0),
                    "total_cost_usd": round(total_cost, 4),
                })
            elif path == "/api/daily":
                days = int(params.get("days", ["30"])[0])
                scan = _scan_all()
                dates = sorted(scan["daily"].keys())[-days:]
                activity = [{"date": d, **{k: scan["daily"][d][k] for k in ("messages", "sessions", "tools")}} for d in dates]
                tokens = [{"date": d, "byModel": scan["daily"][d].get("tokens", {})} for d in dates]
                self.send_json({"activity": activity, "tokens": tokens})
            elif path == "/api/models":
                models = _scan_all()["models"]
                for m_name, m_data in models.items():
                    m_data["cost_usd"] = round(_calc_cost(m_name, m_data.get("input",0), m_data.get("output",0), m_data.get("cache_read",0), m_data.get("cache_create",0)), 4)
                self.send_json({"models": models})
            elif path == "/api/projects":
                scan = _scan_all()
                sp = sorted(scan["projects"].items(), key=lambda x: -x[1]["tokens_total"])
                result = []
                for k, v in sp[:20]:
                    # Approximate cost from total tokens (no per-project model breakdown in agent scan)
                    proj_cost = v["tokens_total"] * 3.0 / 1_000_000 if not v.get("models") else sum(_calc_cost(pm, pd.get("input",0), pd.get("output",0), pd.get("cache_read",0), pd.get("cache_create",0)) for pm, pd in v["models"].items())
                    result.append({"dir_name": k, "name": v["friendly_name"], "messages": v["messages"],
                     "sessions": v["sessions"], "tokens_total": v["tokens_total"], "cost_usd": round(proj_cost, 4)})
                self.send_json({"projects": result})
            elif path == "/api/sessions":
                limit = int(params.get("limit", ["50"])[0])
                history = _load_history()
                entries = sorted(history, key=lambda x: x.get("timestamp", 0), reverse=True)
                seen = set()
                sessions = []
                for e in entries:
                    sid = e.get("sessionId", "")
                    if sid in seen:
                        continue
                    seen.add(sid)
                    pp = e.get("project", "")
                    sessions.append({
                        "sessionId": sid, "timestamp": e.get("timestamp", 0),
                        "project": pp, "projectShort": pp.split("/")[-1] or "~",
                        "firstPrompt": e.get("display", "")[:100],
                    })
                    if len(sessions) >= limit:
                        break
                self.send_json({"sessions": sessions})
            elif path == "/api/hourly":
                days = int(params.get("days", [0])[0] or 0)
                cutoff_ms = (time.time() - days * 86400) * 1000 if days > 0 else 0
                history = _load_history()
                hm = [[0]*24 for _ in range(7)]
                for e in history:
                    ts = e.get("timestamp", 0)
                    if cutoff_ms and ts < cutoff_ms:
                        continue
                    h, dow = ms_to_hour_dow(ts)
                    if h is not None:
                        hm[dow][h] += 1
                self.send_json({"heatmap": hm})
            elif path == "/api/logs":
                # Reuse live scan data (today only for agent — full logs stay on main server)
                data = _scan_today()
                limit = int(params.get("limit", ["50"])[0])
                offset = int(params.get("offset", ["0"])[0])
                calls = data["calls"]
                self.send_json({"logs": calls[offset:offset+limit], "total": len(calls)})
            elif path == "/api/live":
                self.send_json(_scan_today())
            elif path == "/api/session-detail":
                sid = params.get("id", [""])[0]
                if not sid:
                    self.send_json({"error": "missing id"}, 400)
                else:
                    result = self._get_session_detail(sid)
                    self.send_json(result)
            else:
                self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _api_status(self):
        data = {"utilization": 0, "resets_at": "", "profile_name": "Unknown", "stale": True,
                "today_messages": 0, "today_sessions": 0}
        try:
            with open(USAGE_CACHE_FILE) as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        if k == "UTILIZATION": data["utilization"] = int(v)
                        elif k == "RESETS_AT": data["resets_at"] = v
                        elif k == "PROFILE_NAME": data["profile_name"] = v
                        elif k == "TIMESTAMP":
                            data["stale"] = (time.time() - int(v)) > 300
        except Exception:
            pass
        today_str = datetime.date.today().isoformat()
        history = _load_history()
        ts_set = set()
        mc = 0
        for e in history:
            if ms_to_date(e.get("timestamp", 0)) == today_str:
                mc += 1
                ts_set.add(e.get("sessionId", ""))
        data["today_messages"] = mc
        data["today_sessions"] = len(ts_set)
        self.send_json(data)

    def _get_session_detail(self, session_id):
        """Parse a session's JSONL file for detailed timeline"""
        # Find the JSONL file: match by filename (UUID) or by sessionId in events
        target_file = None
        if PROJECTS_DIR.exists():
            for pd in PROJECTS_DIR.iterdir():
                if not pd.is_dir():
                    continue
                # First try: filename matches session_id
                direct = pd / f"{session_id}.jsonl"
                if direct.exists():
                    target_file = direct
                    break
                # Fallback: scan first few lines for sessionId field
                for jf in pd.glob("*.jsonl"):
                    try:
                        with open(jf, "r", encoding="utf-8", errors="replace") as f:
                            for i, line in enumerate(f):
                                if i > 10:
                                    break
                                line = line.strip()
                                if not line:
                                    continue
                                evt = json.loads(line)
                                if evt.get("sessionId") == session_id:
                                    target_file = jf
                                    break
                        if target_file:
                            break
                    except Exception:
                        continue
                if target_file:
                    break

        if not target_file:
            return {"error": "session not found", "events": [], "stats": {}}

        events = []
        tools_summary = {}
        files_touched = {}
        models_used = set()
        total_cost = 0.0
        total_input = 0
        total_output = 0
        first_ts = None
        last_ts = None

        try:
            raw_events = []
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_events.append(json.loads(line))
                    except:
                        continue

            for evt in raw_events:
                t = evt.get("type", "")
                ts = evt.get("timestamp", "")

                if t == "user":
                    msg = evt.get("message", {})
                    content = ""
                    if isinstance(msg, dict):
                        c = msg.get("content", "")
                        if isinstance(c, str):
                            content = c[:500]
                        elif isinstance(c, list):
                            for block in c:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    content = block.get("text", "")[:500]
                                    break
                    events.append({"type": "user", "timestamp": ts, "content": content})
                    if not first_ts:
                        first_ts = ts
                    last_ts = ts

                elif t == "assistant" and "message" in evt:
                    msg = evt.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {})
                    model = msg.get("model", "")
                    inp = usage.get("input_tokens", 0) or 0
                    out = usage.get("output_tokens", 0) or 0
                    cr = usage.get("cache_read_input_tokens", 0) or 0
                    cc = usage.get("cache_creation_input_tokens", 0) or 0
                    cost = round(_calc_cost(model, inp, out, cr, cc), 6)

                    if model:
                        models_used.add(model)
                    total_cost += cost
                    total_input += inp
                    total_output += out

                    # Extract text and tools
                    content_text = ""
                    tools_used = []
                    content_blocks = msg.get("content", [])
                    if isinstance(content_blocks, list):
                        for block in content_blocks:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") == "text":
                                content_text = block.get("text", "")[:500]
                            elif block.get("type") == "tool_use":
                                tool_name = block.get("name", "?")
                                tools_used.append(tool_name)
                                tools_summary[tool_name] = tools_summary.get(tool_name, 0) + 1
                                # Track files
                                tool_input = block.get("input", {})
                                if isinstance(tool_input, dict):
                                    fp = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("command", "")
                                    if fp and tool_name in ("Read", "Edit", "Write"):
                                        if fp not in files_touched:
                                            files_touched[fp] = {}
                                        files_touched[fp][tool_name.lower()] = files_touched[fp].get(tool_name.lower(), 0) + 1

                    if inp > 0 or out > 0:
                        events.append({
                            "type": "assistant", "timestamp": ts, "content": content_text,
                            "model": model, "input_tokens": inp, "output_tokens": out,
                            "cost_usd": cost, "tools_used": tools_used
                        })
                    last_ts = ts
        except Exception:
            pass

        # Compute duration
        duration_ms = 0
        if first_ts and last_ts:
            try:
                from datetime import datetime as _dt
                t1 = _dt.fromisoformat(first_ts.replace("Z", "+00:00"))
                t2 = _dt.fromisoformat(last_ts.replace("Z", "+00:00"))
                duration_ms = int((t2 - t1).total_seconds() * 1000)
            except:
                pass

        return {
            "session_id": session_id,
            "events": events[-200:],  # Limit to last 200 events
            "stats": {
                "messages": len(events),
                "duration_ms": duration_ms,
                "total_cost": round(total_cost, 4),
                "total_input": total_input,
                "total_output": total_output,
                "models": list(models_used),
                "tools_summary": tools_summary,
                "files_touched": files_touched,
            }
        }


class ThreadedServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="Claude Usage Agent")
    parser.add_argument("--port", type=int, default=8421)
    parser.add_argument("--token", type=str, default=None, help="Bearer token for auth")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    global AUTH_TOKEN
    AUTH_TOKEN = args.token

    print(f"Claude Usage Agent")
    print(f"  Host: {args.host}:{args.port}")
    print(f"  Auth: {'enabled' if AUTH_TOKEN else 'disabled'}")
    print(f"  Data: {CLAUDE_DIR}")
    if PROJECTS_DIR.exists():
        pc = sum(1 for d in PROJECTS_DIR.iterdir() if d.is_dir())
        print(f"  Projects: {pc}")

    # 预扫描
    threading.Thread(target=_scan_all, daemon=True).start()

    server = ThreadedServer((args.host, args.port), AgentHandler)
    print(f"  Ready: http://{args.host}:{args.port}/api/ping")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAgent stopped")


if __name__ == "__main__":
    main()

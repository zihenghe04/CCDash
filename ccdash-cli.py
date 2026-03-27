#!/usr/bin/env python3
"""CCDash CLI — Quick usage check from the terminal.

Usage:
    python3 ccdash-cli.py status       — Today's overview
    python3 ccdash-cli.py top          — Project TOP 5
    python3 ccdash-cli.py models       — Model cost breakdown
    python3 ccdash-cli.py budget       — Budget progress
    python3 ccdash-cli.py live         — Recent API calls (tail -f style)

Options:
    --server URL   Connect to running CCDash server (default: http://localhost:8420)
    --no-color     Disable colored output
"""

import sys
import json
import urllib.request

SERVER = "http://localhost:8420"
COLOR = True


# ── ANSI Colors ──────────────────────────────────────────
def c(text, code):
    return f"\033[{code}m{text}\033[0m" if COLOR else str(text)

def bold(t):    return c(t, "1")
def dim(t):     return c(t, "2")
def green(t):   return c(t, "32")
def yellow(t):  return c(t, "33")
def red(t):     return c(t, "31")
def cyan(t):    return c(t, "36")
def magenta(t): return c(t, "35")


def fmt(n):
    if n >= 1e9: return f"{n/1e9:.1f}B"
    if n >= 1e6: return f"{n/1e6:.1f}M"
    if n >= 1e3: return f"{n/1e3:.1f}K"
    return str(n)


def api(path):
    try:
        url = f"{SERVER}{path}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(red(f"  Error: {e}"))
        print(dim(f"  Is CCDash server running at {SERVER}?"))
        sys.exit(1)


# ── Commands ─────────────────────────────────────────────
def cmd_status():
    d = api("/api/overview")
    s = api("/api/status")

    util = s.get("utilization", 0)
    bar_len = 30
    filled = int(util / 100 * bar_len)
    bar_color = green if util < 60 else yellow if util < 80 else red
    bar = bar_color("█" * filled) + dim("░" * (bar_len - filled))

    print()
    print(bold("  ⚡ CCDash Status"))
    print(f"  {dim('─' * 44)}")
    print(f"  Quota:  [{bar}] {bar_color(f'{util}%')}")
    if s.get("profile_name"):
        print(f"  Plan:   {cyan(s['profile_name'])}")
    print()
    print(f"  {bold('Today')}     {green(d.get('today_messages', 0))} msgs  ·  {d.get('today_sessions', 0)} sessions")
    print(f"  {bold('Total')}     {cyan(fmt(d.get('total_messages', 0)))} msgs  ·  {fmt(d.get('total_tokens', 0))} tokens")
    print(f"  {bold('Cost')}      {green('$' + str(round(d.get('total_cost_usd', 0), 2)))}")
    print(f"  {bold('RPM/TPM')}   {yellow(d.get('rpm', 0))} rpm  ·  {fmt(d.get('tpm', 0))} tpm")
    print(f"  {bold('Burn')}      {fmt(d.get('burn_rate_tokens_per_min', 0))} tok/min  ·  ${d.get('burn_rate_cost_per_hour', 0):.2f}/hr")
    print()


def cmd_top():
    d = api("/api/projects")
    projects = d.get("projects", [])
    if not projects:
        print(dim("  No projects found"))
        return

    # Calculate total tokens for percentage
    total_tok = sum(p.get("tokens_total", 0) for p in projects) or 1

    print()
    print(bold("  📁 Project TOP 5"))
    print(f"  {dim('─' * 60)}")
    for i, p in enumerate(projects[:5], 1):
        name = p.get("name", p.get("friendly_name", "?"))
        tok = fmt(p.get("tokens_total", 0))
        cost = f"${p.get('cost_usd', 0):.2f}"
        pct = p.get("tokens_total", 0) / total_tok * 100
        filled = max(1, int(pct / 5))
        bar = green("█" * filled) + dim("░" * (20 - filled))
        print(f"  {dim(f'{i}.')} {name[:28]:<28s} {bar} {cyan(f'{pct:>4.0f}%')}  {tok:>7s}  {green(cost)}")
    print()


def cmd_models():
    d = api("/api/models")
    raw = d.get("models", {})
    if not raw:
        print(dim("  No models found"))
        return

    # models can be dict {name: data} or list [{model, ...}]
    if isinstance(raw, dict):
        models = []
        for name, data in raw.items():
            data["model"] = name
            models.append(data)
        models.sort(key=lambda m: m.get("cost_usd", 0), reverse=True)
    else:
        models = raw

    print()
    print(bold("  🤖 Model Usage"))
    print(f"  {dim('─' * 60)}")
    print(f"  {'Model':<30s} {'Calls':>6s} {'Tokens':>8s} {'Cost':>10s} {'Hit%':>5s}")
    print(f"  {dim('─' * 60)}")
    for m in models[:10]:
        name = m.get("model", "?").replace("claude-", "")[:28]
        calls = m.get("calls", 0)
        inp = m.get("input", 0)
        out = m.get("output", 0)
        cr = m.get("cache_read", 0)
        cc = m.get("cache_create", 0)
        tok = fmt(inp + out + cr + cc)
        cost = f"${m.get('cost_usd', 0):.2f}"
        all_in = inp + cr + cc
        hit = f"{cr / all_in * 100:.0f}%" if all_in > 0 else "—"
        # Pad BEFORE coloring to avoid ANSI codes breaking alignment
        print(f"  {name:<30s} {calls:>6d} {tok:>8s} {cost:>10s} {hit:>5s}")
    print()


def cmd_budget():
    d = api("/api/budget")
    if not d.get("configured"):
        print(dim("  No budget configured. Set one in Settings."))
        return

    print()
    print(bold("  💰 Budget Status"))
    print(f"  {dim('─' * 44)}")
    labels = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
    for period, label in labels.items():
        s = d.get("status", {}).get(period)
        if not s:
            continue
        pct = min(s["pct"], 100)
        bar_len = 25
        filled = int(pct / 100 * bar_len)
        color = green if s["alert"] == "ok" else yellow if s["alert"] == "warning" else red
        bar = color("█" * filled) + dim("░" * (bar_len - filled))
        over = red(" OVER!") if s["pct"] > 100 else ""
        print(f"  {label:<8s} [{bar}] ${s['spent']:.2f} / ${s['limit']:.2f}{over}")
    print()


def cmd_live():
    d = api("/api/live")
    calls = d.get("calls", [])
    if not calls:
        print(dim("  No calls today"))
        return

    print()
    print(bold("  📡 Recent Calls"))
    print(f"  {dim('─' * 70)}")
    print(f"  {'Time':<8s} {'Model':<20s} {'↓In':>7s} {'↑Out':>7s} {'⟲Cache':>8s} {'Cost':>8s}")
    print(f"  {dim('─' * 70)}")
    for call in calls[:15]:
        raw_ts = call.get("timestamp", "")
        # Extract HH:MM from ISO timestamp like "2026-03-27T15:49:49.722Z"
        ts = raw_ts[11:16] if len(raw_ts) > 16 else raw_ts[-8:]
        model = call.get("model", "?").replace("claude-", "")[:18]
        inp = fmt(call.get("input_tokens", 0))
        out = fmt(call.get("output_tokens", 0))
        cr = fmt(call.get("cache_read", 0))
        cost = f"${call.get('cost_usd', 0):.4f}" if call.get("cost_usd") else "—"
        print(f"  {dim(ts):<8s} {model:<20s} {cyan(inp):>7s} {green(out):>7s} {magenta(cr):>8s} {green(cost):>8s}")
    totals = d.get("totals", {})
    print(f"  {dim('─' * 70)}")
    print(f"  {bold('Total')}  {len(calls)} calls  ·  ↓{fmt(totals.get('input', 0))}  ↑{fmt(totals.get('output', 0))}  ⟲{fmt(totals.get('cache_read', 0))}  {green('$' + str(round(totals.get('cost', 0), 2)))}")
    print()


# ── Main ─────────────────────────────────────────────────
def main():
    global SERVER, COLOR
    args = sys.argv[1:]

    # Parse flags
    while args and args[0].startswith("--"):
        if args[0] == "--server" and len(args) > 1:
            SERVER = args[1]
            args = args[2:]
        elif args[0] == "--no-color":
            COLOR = False
            args = args[1:]
        else:
            args = args[1:]

    cmd = args[0] if args else "status"
    cmds = {
        "status": cmd_status,
        "top": cmd_top,
        "models": cmd_models,
        "budget": cmd_budget,
        "live": cmd_live,
    }
    if cmd in cmds:
        cmds[cmd]()
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
    else:
        print(f"  Unknown command: {cmd}")
        print(f"  Available: {', '.join(cmds.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()

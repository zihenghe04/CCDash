#!/usr/bin/env bash
# CCDash launchd installer (macOS)
#
# Installs com.ccdash.server as a LaunchAgent so CCDash auto-starts at login
# and automatically restarts on crash. Optional: install com.ccdash.tunnel
# for SSH-tunneled remote agent.
#
# Usage:
#   ./launchd/install.sh server             # install server only
#   ./launchd/install.sh server tunnel      # install server + prompt for tunnel
#   ./launchd/install.sh uninstall          # uninstall both

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || echo /usr/bin/python3)}"

install_server() {
    mkdir -p "$LAUNCH_AGENTS"
    local target="$LAUNCH_AGENTS/com.ccdash.server.plist"
    sed \
        -e "s|{{CCDASH_DIR}}|$REPO_DIR|g" \
        -e "s|{{PYTHON_BIN}}|$PYTHON_BIN|g" \
        "$SCRIPT_DIR/com.ccdash.server.plist.template" > "$target"
    # Unload if already loaded
    launchctl unload "$target" 2>/dev/null || true
    launchctl load "$target"
    echo "✅ Installed: $target"
    echo "   Python: $PYTHON_BIN"
    echo "   Repo:   $REPO_DIR"
    echo "   Logs:   /tmp/ccdash.log, /tmp/ccdash.err"
    echo "   Dashboard: http://localhost:8420"
}

install_tunnel() {
    local autossh_bin
    autossh_bin="$(command -v autossh || true)"
    if [[ -z "$autossh_bin" ]]; then
        echo "❌ autossh not found. Install with: brew install autossh"
        return 1
    fi
    read -r -p "Local port (e.g. 8423): " local_port
    read -r -p "Remote port (agent.py, e.g. 8421): " remote_port
    read -r -p "Remote SSH user: " remote_user
    read -r -p "Remote SSH host: " remote_host

    mkdir -p "$LAUNCH_AGENTS"
    local target="$LAUNCH_AGENTS/com.ccdash.tunnel.plist"
    sed \
        -e "s|{{AUTOSSH_BIN}}|$autossh_bin|g" \
        -e "s|{{LOCAL_PORT}}|$local_port|g" \
        -e "s|{{REMOTE_PORT}}|$remote_port|g" \
        -e "s|{{REMOTE_USER}}|$remote_user|g" \
        -e "s|{{REMOTE_HOST}}|$remote_host|g" \
        "$SCRIPT_DIR/com.ccdash.tunnel.plist.template" > "$target"
    launchctl unload "$target" 2>/dev/null || true
    launchctl load "$target"
    echo "✅ Installed: $target"
    echo "   ${remote_user}@${remote_host}:${remote_port} → localhost:${local_port}"
    echo ""
    echo "Add this remote to config.json:"
    echo "  \"remotes\": [ { \"name\": \"Cloud\", \"url\": \"http://127.0.0.1:${local_port}\", \"token\": \"your_secret\", \"enabled\": true } ]"
}

uninstall_all() {
    for name in com.ccdash.server com.ccdash.tunnel; do
        local target="$LAUNCH_AGENTS/${name}.plist"
        if [[ -f "$target" ]]; then
            launchctl unload "$target" 2>/dev/null || true
            rm -f "$target"
            echo "🗑  Removed: $target"
        fi
    done
}

case "${1:-}" in
    server)
        install_server
        [[ "${2:-}" == "tunnel" ]] && install_tunnel || true
        ;;
    tunnel)
        install_tunnel
        ;;
    uninstall)
        uninstall_all
        ;;
    *)
        cat <<USAGE
CCDash launchd installer (macOS)

Usage:
  ./launchd/install.sh server             Install CCDash server auto-start
  ./launchd/install.sh server tunnel      Also install SSH tunnel (autossh)
  ./launchd/install.sh tunnel             Install SSH tunnel only
  ./launchd/install.sh uninstall          Uninstall both

Environment:
  PYTHON_BIN=/path/to/python3             Override Python interpreter
USAGE
        exit 1
        ;;
esac

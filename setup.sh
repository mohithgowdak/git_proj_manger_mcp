#!/usr/bin/env bash
# Sets up the GitHub Project Manager MCP server and registers it with Claude.
set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 1. Locate Python 3.10+ ────────────────────────────────────────────────────
info "Checking Python..."
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ok=$("$candidate" -c 'import sys; print(sys.version_info >= (3, 10))' 2>/dev/null || true)
        if [[ "$ok" == "True" ]]; then
            PYTHON="$candidate"; break
        fi
    fi
done
[[ -z "$PYTHON" ]] && error "Python 3.10+ is required. Install it and re-run."
success "Found $($PYTHON --version)"

# ── 2. Virtual environment ────────────────────────────────────────────────────
VENV_DIR="$REPO_DIR/venv"
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate (Git Bash on Windows uses Scripts/, Unix uses bin/)
if [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
    PYTHON_EXEC="$VENV_DIR/Scripts/python.exe"
else
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    PYTHON_EXEC="$VENV_DIR/bin/python"
fi
success "Virtual environment ready."

# ── 3. Install dependencies ───────────────────────────────────────────────────
info "Installing dependencies (this may take a minute)..."
pip install --quiet --upgrade pip
pip install --quiet -r "$REPO_DIR/requirements.txt"
success "Dependencies installed."

# ── 4. Gather GitHub credentials ─────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Enter your GitHub credentials (required to run the MCP server):${NC}"
echo ""

read -rp "  GitHub Personal Access Token : " GITHUB_TOKEN
[[ -z "$GITHUB_TOKEN" ]] && error "GITHUB_TOKEN cannot be empty."

read -rp "  GitHub Owner (user or org)   : " GITHUB_OWNER
[[ -z "$GITHUB_OWNER" ]] && error "GITHUB_OWNER cannot be empty."

read -rp "  GitHub Repository name       : " GITHUB_REPO
[[ -z "$GITHUB_REPO" ]] && error "GITHUB_REPO cannot be empty."

# ── 5. Write .env file ────────────────────────────────────────────────────────
ENV_FILE="$REPO_DIR/.env"
cat > "$ENV_FILE" <<ENVEOF
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_OWNER=$GITHUB_OWNER
GITHUB_REPO=$GITHUB_REPO
ENVEOF
success ".env written → $ENV_FILE"

# ── 6. Determine Claude config paths ─────────────────────────────────────────
# Claude Desktop: platform-specific JSON config file
# Claude Code CLI: user-level settings (~/.claude/settings.json on all platforms)

case "$(uname -s)" in
    Darwin)
        CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        CLAUDE_CODE_SETTINGS="$HOME/.claude/settings.json"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        # Git Bash on Windows — APPDATA is a Windows path, convert to POSIX
        WIN_APPDATA="${APPDATA:-}"
        if [[ -z "$WIN_APPDATA" ]]; then
            WIN_APPDATA="$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d '\r\n')"
        fi
        POSIX_APPDATA="$(cygpath -u "$WIN_APPDATA" 2>/dev/null || echo "$WIN_APPDATA")"
        CLAUDE_DESKTOP_CONFIG="$POSIX_APPDATA/Claude/claude_desktop_config.json"
        USERPROFILE_POSIX="$(cygpath -u "${USERPROFILE:-$HOME}" 2>/dev/null || echo "$HOME")"
        CLAUDE_CODE_SETTINGS="$USERPROFILE_POSIX/.claude/settings.json"
        ;;
    Linux)
        CLAUDE_DESKTOP_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json"
        CLAUDE_CODE_SETTINGS="$HOME/.claude/settings.json"
        ;;
    *)
        CLAUDE_DESKTOP_CONFIG=""
        CLAUDE_CODE_SETTINGS="$HOME/.claude/settings.json"
        ;;
esac

# ── 7. Helper: merge mcpServers entry into a JSON config file ─────────────────
merge_mcp_config() {
    local config_file="$1"
    local server_name="$2"
    local server_json="$3"   # JSON object for this single server

    mkdir -p "$(dirname "$config_file")"

    "$PYTHON_EXEC" - <<PYEOF
import json, os, sys

config_file = r"""$config_file"""
server_name = r"""$server_name"""
server_json = r"""$server_json"""

try:
    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}

config.setdefault("mcpServers", {})[server_name] = json.loads(server_json)

with open(config_file, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PYEOF
}

# Build the server JSON (single entry, no surrounding mcpServers key)
SERVER_JSON=$(cat <<JSONEOF
{
  "command": "$PYTHON_EXEC",
  "args": ["-m", "src"],
  "cwd": "$REPO_DIR",
  "env": {
    "PYTHONPATH": "$REPO_DIR",
    "GITHUB_TOKEN": "$GITHUB_TOKEN",
    "GITHUB_OWNER": "$GITHUB_OWNER",
    "GITHUB_REPO": "$GITHUB_REPO"
  }
}
JSONEOF
)

# ── 8. Register with Claude Code CLI (settings.json) ─────────────────────────
info "Registering with Claude Code CLI → $CLAUDE_CODE_SETTINGS"
if merge_mcp_config "$CLAUDE_CODE_SETTINGS" "github-project-manager" "$SERVER_JSON"; then
    success "Claude Code CLI config updated."
else
    warn "Could not update Claude Code CLI config. See manual step at the bottom."
fi

# ── 9. Register with Claude Desktop (if config exists or Desktop is installed) ──
if [[ -n "$CLAUDE_DESKTOP_CONFIG" ]]; then
    if [[ -f "$CLAUDE_DESKTOP_CONFIG" ]] || [[ -d "$(dirname "$CLAUDE_DESKTOP_CONFIG")" ]]; then
        info "Registering with Claude Desktop → $CLAUDE_DESKTOP_CONFIG"
        if merge_mcp_config "$CLAUDE_DESKTOP_CONFIG" "github-project-manager" "$SERVER_JSON"; then
            success "Claude Desktop config updated."
        else
            warn "Could not update Claude Desktop config. See manual step at the bottom."
        fi
    else
        warn "Claude Desktop config dir not found — skipping Desktop registration."
    fi
fi

# ── 10. Summary ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Repo     : $REPO_DIR"
echo "  Python   : $PYTHON_EXEC"
echo "  Owner    : $GITHUB_OWNER / $GITHUB_REPO"
echo ""
echo "  Next steps:"
echo "    • Claude Code CLI  — restart the CLI session"
echo "    • Claude Desktop   — quit and reopen the app"
echo ""
echo -e "${YELLOW}Manual config (paste into mcpServers if auto-registration failed):${NC}"
cat <<MANUALEOF
{
  "mcpServers": {
    "github-project-manager": $SERVER_JSON
  }
}
MANUALEOF

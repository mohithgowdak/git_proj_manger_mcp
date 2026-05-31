#!/usr/bin/env bash
# Sets up the GitHub Project Manager MCP server and registers it with Claude Code CLI.
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
    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

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
echo -e "${YELLOW}Enter your GitHub credentials:${NC}"
echo ""

read -rp "  GitHub Personal Access Token : " GITHUB_TOKEN
[[ -z "$GITHUB_TOKEN" ]] && error "GITHUB_TOKEN cannot be empty."

read -rp "  GitHub Owner (user or org)   : " GITHUB_OWNER
[[ -z "$GITHUB_OWNER" ]] && error "GITHUB_OWNER cannot be empty."

read -rp "  GitHub Repository name       : " GITHUB_REPO
[[ -z "$GITHUB_REPO" ]] && error "GITHUB_REPO cannot be empty."

# ── 5. Write .env file ────────────────────────────────────────────────────────
cat > "$REPO_DIR/.env" <<ENVEOF
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_OWNER=$GITHUB_OWNER
GITHUB_REPO=$GITHUB_REPO
ENVEOF
success ".env written."

# ── 6. Register with Claude Code CLI ─────────────────────────────────────────
# Stored in ~/.claude.json (user scope = available in all projects).
# Re-running removes the old entry first to avoid duplicates.
if command -v claude &>/dev/null; then
    info "Registering with Claude Code CLI..."
    claude mcp remove "github-project-manager" -s user 2>/dev/null || true
    claude mcp add "github-project-manager" \
        -s user \
        -e PYTHONPATH="$REPO_DIR" \
        -e GITHUB_TOKEN="$GITHUB_TOKEN" \
        -e GITHUB_OWNER="$GITHUB_OWNER" \
        -e GITHUB_REPO="$GITHUB_REPO" \
        -- "$PYTHON_EXEC" -m src
    success "Registered with Claude Code CLI."
else
    warn "'claude' CLI not found — skipping CLI registration."
fi

# ── 7. Register with Claude Desktop ──────────────────────────────────────────
# Claude Desktop reads from a JSON config file; mcpServers go there directly.
case "$(uname -s)" in
    Darwin)
        CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        WIN_APPDATA="${APPDATA:-$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d '\r\n')}"
        CLAUDE_DESKTOP_CONFIG="$(cygpath -u "$WIN_APPDATA" 2>/dev/null || echo "$WIN_APPDATA")/Claude/claude_desktop_config.json"
        ;;
    Linux)
        CLAUDE_DESKTOP_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json"
        ;;
    *)
        CLAUDE_DESKTOP_CONFIG=""
        ;;
esac

if [[ -n "$CLAUDE_DESKTOP_CONFIG" && ( -f "$CLAUDE_DESKTOP_CONFIG" || -d "$(dirname "$CLAUDE_DESKTOP_CONFIG")" ) ]]; then
    info "Registering with Claude Desktop..."
    DESKTOP_CONFIG_WIN="$(cygpath -w "$CLAUDE_DESKTOP_CONFIG" 2>/dev/null || echo "$CLAUDE_DESKTOP_CONFIG")"
    PYTHON_EXEC_WIN="$(cygpath -w "$PYTHON_EXEC" 2>/dev/null || echo "$PYTHON_EXEC")"
    REPO_DIR_WIN="$(cygpath -w "$REPO_DIR" 2>/dev/null || echo "$REPO_DIR")"
    "$PYTHON_EXEC" - <<PYEOF
import json, os

path = r"""$DESKTOP_CONFIG_WIN"""
entry = {
    "command": r"""$PYTHON_EXEC_WIN""",
    "args": ["-m", "src"],
    "env": {
        "PYTHONPATH": r"""$REPO_DIR_WIN""",
        "GITHUB_TOKEN": r"""$GITHUB_TOKEN""",
        "GITHUB_OWNER": r"""$GITHUB_OWNER""",
        "GITHUB_REPO":  r"""$GITHUB_REPO""",
    }
}
try:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}
cfg.setdefault("mcpServers", {})["github-project-manager"] = entry
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
PYEOF
    success "Claude Desktop config updated → $CLAUDE_DESKTOP_CONFIG"
    warn "Restart Claude Desktop to pick up the change."
else
    info "Claude Desktop not detected — skipping."
fi

# ── 8. Register with Cline (VS Code extension) ───────────────────────────────
# Cline reads MCP servers from its globalStorage settings file.
case "$(uname -s)" in
    Darwin)
        CLINE_CONFIG="$HOME/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        WIN_APPDATA2="${APPDATA:-$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d '\r\n')}"
        CLINE_CONFIG="$(cygpath -u "$WIN_APPDATA2" 2>/dev/null || echo "$WIN_APPDATA2")/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
        ;;
    Linux)
        CLINE_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
        ;;
    *)
        CLINE_CONFIG=""
        ;;
esac

if [[ -n "$CLINE_CONFIG" ]]; then
    # Convert POSIX path → Windows path so Python (native Windows) can open it
    CLINE_CONFIG_WIN="$(cygpath -w "$CLINE_CONFIG" 2>/dev/null || echo "$CLINE_CONFIG")"
    PYTHON_EXEC_WIN="$(cygpath -w "$PYTHON_EXEC" 2>/dev/null || echo "$PYTHON_EXEC")"
    REPO_DIR_WIN="$(cygpath -w "$REPO_DIR" 2>/dev/null || echo "$REPO_DIR")"

    info "Registering with Cline..."
    "$PYTHON_EXEC" - <<PYEOF || warn "Cline registration failed — see manual JSON below."
import json, os

path = r"""$CLINE_CONFIG_WIN"""
entry = {
    "command": r"""$PYTHON_EXEC_WIN""",
    "args": ["-m", "src"],
    "env": {
        "PYTHONPATH": r"""$REPO_DIR_WIN""",
        "GITHUB_TOKEN": r"""$GITHUB_TOKEN""",
        "GITHUB_OWNER": r"""$GITHUB_OWNER""",
        "GITHUB_REPO":  r"""$GITHUB_REPO""",
    }
}
os.makedirs(os.path.dirname(path), exist_ok=True)
try:
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}
cfg.setdefault("mcpServers", {})["github-project-manager"] = entry
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
PYEOF
    success "Cline config updated → $CLINE_CONFIG"
    warn "Reload VS Code window (Ctrl+Shift+P → 'Developer: Reload Window') to pick up the change."
else
    info "Cline not detected — skipping auto-registration."
fi

echo ""
echo -e "  ${YELLOW}Cline MCP JSON${NC} — add this to your cline_mcp_settings.json if needed:"
echo ""
cat <<JSONEOF
  {
    "mcpServers": {
      "github-project-manager": {
        "command": "$PYTHON_EXEC",
        "args": ["-m", "src"],
        "env": {
          "PYTHONPATH": "$REPO_DIR",
          "GITHUB_TOKEN": "$GITHUB_TOKEN",
          "GITHUB_OWNER": "$GITHUB_OWNER",
          "GITHUB_REPO": "$GITHUB_REPO"
        }
      }
    }
  }
JSONEOF

# ── 9. Verify ─────────────────────────────────────────────────────────────────
if command -v claude &>/dev/null; then
    echo ""
    info "Verifying connection..."
    claude mcp list 2>&1 | grep -E "github-project-manager|ERROR" || true
fi

# ── 10. Summary ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Repo   : $REPO_DIR"
echo "  Python : $PYTHON_EXEC"
echo "  Owner  : $GITHUB_OWNER / $GITHUB_REPO"
echo ""
echo "  • Claude Code  — restart your session to load the new server."
echo "  • Claude Desktop — restart the app."
echo "  • Cline (VS Code) — Ctrl+Shift+P → 'Developer: Reload Window'."

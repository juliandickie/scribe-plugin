#!/usr/bin/env bash
# Post-install hook for gworkspace plugin.
#
# Installs the workspace-mcp Python package (our fork of taylorwilsdon's
# google_workspace_mcp) from the GitHub fork branch, then prints setup
# instructions for the user to complete OAuth configuration.

set -euo pipefail

FORK_REPO="https://github.com/juliandickie/google_workspace_mcp.git"
FORK_BRANCH="fork-extension"

echo ""
echo "=== gworkspace plugin - post-install ==="
echo ""

if command -v uv >/dev/null 2>&1; then
    echo "Installing workspace-mcp via uv tool..."
    uv tool install --from "git+${FORK_REPO}@${FORK_BRANCH}" workspace-mcp
else
    echo "uv not found - falling back to pip"
    python3 -m pip install --user "git+${FORK_REPO}@${FORK_BRANCH}"
fi

echo ""
echo "workspace-mcp installed."
echo ""
echo "NEXT STEPS -"
echo ""
echo "  1. Set up a Google Cloud Project with OAuth credentials"
echo "     See the plugin README for a 5-minute walkthrough."
echo ""
echo "  2. Run /gws-auth-init in Claude Code for guided OAuth setup."
echo ""
echo "  3. Once authenticated, the gworkspace skill lets Claude"
echo "     read and write Google Docs, Drive, and Gmail."
echo ""
echo "MCP server registration - the gworkspace-plugin skill teaches Claude"
echo "how to invoke the workspace-mcp server. If you want the MCP server"
echo "always-on in Claude Code, add this to your ~/.claude/settings.json -"
echo ""
echo '    "mcpServers": {'
echo '      "gworkspace": {'
echo '        "command": "uvx",'
echo '        "args": ["workspace-mcp", "--tools", "docs", "drive", "gmail", "calendar"]'
echo '      }'
echo '    }'
echo ""

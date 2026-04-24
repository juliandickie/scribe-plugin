#!/usr/bin/env bash
# Optional manual install script for the Scribe plugin.
#
# The plugin's manifest declares the workspace-mcp server inline via uvx,
# so Claude Code will auto-install on first MCP tool call. This script
# is only needed if you want to pre-warm the install (e.g., to avoid a
# slow first invocation, or on machines without network at first-use time).
#
# Installs the workspace-mcp Python package from the fork branch.

set -euo pipefail

# Idempotency guard - skip if workspace-mcp is already installed
if command -v workspace-mcp >/dev/null 2>&1; then
    echo "workspace-mcp already installed. Skipping."
    exit 0
fi

FORK_REPO="https://github.com/juliandickie/google_workspace_mcp.git"
FORK_BRANCH="fork-extension"

echo ""
echo "=== Scribe plugin - optional pre-install ==="
echo ""

if command -v uv >/dev/null 2>&1; then
    echo "Installing workspace-mcp via uv tool..."
    uv tool install --from "git+${FORK_REPO}@${FORK_BRANCH}" workspace-mcp
else
    echo "uv not found - falling back to pip"
    python3 -m pip install --user "git+${FORK_REPO}@${FORK_BRANCH}"
fi

echo ""
echo "workspace-mcp installed. Scribe is ready."
echo ""
echo "NEXT STEPS -"
echo ""
echo "  1. Set up a Google Cloud Project with OAuth credentials"
echo "     See the plugin README for a 5-minute walkthrough."
echo ""
echo "  2. Run /scribe:auth-init in Claude Code for guided OAuth setup."
echo ""
echo "  3. Once authenticated, the scribe skill lets Claude"
echo "     read and write Google Docs, Drive, and Gmail."
echo ""

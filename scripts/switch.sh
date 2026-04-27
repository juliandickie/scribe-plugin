#!/usr/bin/env bash
# Switch the active Scribe OAuth client by org.
#
# Use this when you have OAuth clients in multiple Google Workspace orgs
# (e.g. one per agency engagement). See docs/multi-org-setup.md for the
# full setup walkthrough.
#
# Usage - switch.sh <org-suffix>
# Example - switch.sh pro-marketing    or    switch.sh idd
#
# To install -
#   cp scripts/switch.sh ~/.workspace-mcp/switch.sh
#   chmod +x ~/.workspace-mcp/switch.sh

set -euo pipefail

WORKSPACE_DIR="$HOME/.workspace-mcp"
ORG="${1:-}"

list_available() {
    echo "Available orgs -"
    if ls "$WORKSPACE_DIR"/client_secret_*.json >/dev/null 2>&1; then
        ls "$WORKSPACE_DIR"/client_secret_*.json | \
            sed -e 's|.*client_secret_||' -e 's|\.json$||' | \
            awk '{print "  " $1}'
    else
        echo "  (none yet - drop client_secret_<org>.json files into $WORKSPACE_DIR)"
    fi
}

show_active() {
    echo "Currently active -"
    if [ -L "$WORKSPACE_DIR/oauth_client.json" ]; then
        TARGET=$(readlink "$WORKSPACE_DIR/oauth_client.json")
        echo "  $TARGET"
    elif [ -f "$WORKSPACE_DIR/oauth_client.json" ]; then
        echo "  (real file, not a symlink)"
    else
        echo "  (no oauth_client.json present)"
    fi
}

if [ -z "$ORG" ]; then
    echo "Usage - $(basename "$0") <org-suffix>"
    echo ""
    list_available
    echo ""
    show_active
    exit 1
fi

TARGET="$WORKSPACE_DIR/client_secret_${ORG}.json"
if [ ! -f "$TARGET" ]; then
    echo "ERROR - $TARGET not found"
    echo ""
    list_available
    exit 1
fi

ln -sf "client_secret_${ORG}.json" "$WORKSPACE_DIR/oauth_client.json"
echo "Switched active OAuth client to $ORG"
echo "Now pointing at - $(readlink "$WORKSPACE_DIR/oauth_client.json")"

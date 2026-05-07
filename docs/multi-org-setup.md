# Multi-org / Cross-Workspace Setup

If you operate across more than one Google Workspace organisation (e.g. an agency Workspace and a client/institute Workspace), the default Scribe setup needs a small extension. This page walks you through it.

## Why the default setup is not enough

`/scribe:auth-init` walks you through creating ONE OAuth client inside ONE Google Cloud project. That OAuth client is bound to the consent screen of the Workspace org it was created in. If the consent screen is set to **Internal** (which is the recommended setting for org-scoped use), the OAuth client only accepts identities from the OWNING Workspace.

Result - if you authenticate `you@org-a.com` against an OAuth client created in org A, it works. If you then try to authenticate `you@org-b.com` against the SAME client, the consent flow rejects you ("Access blocked" or similar).

The fix is to create one OAuth client per org and switch between them.

## Setup overview

1. Create a Google Cloud project inside EACH Workspace org

2. Inside each project, enable the same APIs (Drive, Docs, optional Gmail/Calendar) and create a Desktop-type OAuth client

3. Download the credentials JSON for each org, name them per-org, save under `~/.workspace-mcp/`

4. Symlink the currently-active credentials at `~/.workspace-mcp/oauth_client.json`

5. Use `switch.sh <org>` to flip the symlink when changing context

The plugin's MCP server reads `~/.workspace-mcp/oauth_client.json` (set in `plugin.json`'s `env.GOOGLE_CLIENT_SECRET_PATH`). The symlink-swap pattern means the server always reads the same path; only the target changes.

## Detailed walkthrough

### 1. Create one OAuth client per org

For EACH Workspace org -

- Sign in to https://console.cloud.google.com with an account inside that org

- Create a new project (suggest naming `scribe-{org-name}`)

- Enable Google Drive API and Google Docs API (and Gmail/Calendar if needed)

- Configure OAuth consent screen as **Internal** (org-scoped)

- Create OAuth Client ID of type **Desktop app**

- Download the JSON

### 2. Save credentials with org-specific names

```bash
mkdir -p ~/.workspace-mcp
mv ~/Downloads/client_secret_<org-a-id>.apps.googleusercontent.com.json \
   ~/.workspace-mcp/client_secret_org-a.json
mv ~/Downloads/client_secret_<org-b-id>.apps.googleusercontent.com.json \
   ~/.workspace-mcp/client_secret_org-b.json
```

Use whatever short org identifier makes sense - `pro-marketing`, `idd`, `acme-corp`, etc.

### 3. Set up the active symlink

```bash
cd ~/.workspace-mcp
ln -sf client_secret_org-a.json oauth_client.json
ls -l oauth_client.json
# oauth_client.json -> client_secret_org-a.json
```

### 4. Add the switch helper

Save this as `~/.workspace-mcp/switch.sh` and make it executable -

```bash
#!/usr/bin/env bash
# Switch the active Scribe OAuth client by org.
# Usage - switch.sh <org-suffix>
# Example - switch.sh org-a    or    switch.sh idd

set -euo pipefail

ORG="${1:-}"
if [ -z "$ORG" ]; then
    echo "Usage - $(basename "$0") <org-suffix>"
    echo ""
    echo "Available orgs -"
    ls ~/.workspace-mcp/client_secret_*.json 2>/dev/null | \
        sed -e 's|.*client_secret_||' -e 's|\.json$||' | \
        awk '{print "  " $1}'
    echo ""
    echo "Currently active -"
    if [ -L ~/.workspace-mcp/oauth_client.json ]; then
        readlink ~/.workspace-mcp/oauth_client.json
    else
        echo "  (no symlink)"
    fi
    exit 1
fi

TARGET="$HOME/.workspace-mcp/client_secret_${ORG}.json"
if [ ! -f "$TARGET" ]; then
    echo "ERROR - $TARGET not found"
    echo ""
    echo "Available orgs -"
    ls ~/.workspace-mcp/client_secret_*.json 2>/dev/null | \
        sed -e 's|.*client_secret_||' -e 's|\.json$||' | \
        awk '{print "  " $1}'
    exit 1
fi

ln -sf "client_secret_${ORG}.json" ~/.workspace-mcp/oauth_client.json
echo "Switched active OAuth client to $ORG"
echo "Now pointing at - $(readlink ~/.workspace-mcp/oauth_client.json)"
```

```bash
chmod +x ~/.workspace-mcp/switch.sh
```

### 5. Authenticate once per org

For EACH org's primary email -

```bash
~/.workspace-mcp/switch.sh org-a
USER_GOOGLE_EMAIL=you@org-a.com uvx workspace-mcp@1.20.4 --single-user --tools drive docs

~/.workspace-mcp/switch.sh org-b
USER_GOOGLE_EMAIL=you@org-b.com uvx workspace-mcp@1.20.4 --single-user --tools drive docs
```

Each consent flow stores a refresh token at `~/.workspace-mcp/credentials/<email>.json`. Tokens are SELF-CONTAINED - they don't depend on which `oauth_client.json` is active when they're used. Once you've authenticated both orgs, you can flip the symlink whenever and pre-existing tokens still work for read/write.

## Daily workflow

After initial setup, all you need is the symlink flip when context changes -

```bash
# Working with org A's Drive
~/.workspace-mcp/switch.sh org-a
# ... in Claude Code, use /scribe:push or any push action ...

# Now switching to org B
~/.workspace-mcp/switch.sh org-b
# ... in Claude Code, push files to org B's Drive ...
```

In a Claude Code session that's already running, you may need to restart the session for the MCP server to pick up the new credentials (because uvx caches the started server process). A `/plugin reload scribe` if available also works.

## Why not use a single OAuth client for both orgs

You can, IF -

- Both orgs accept External OAuth consent (lower security posture)

- AND you mark the OAuth client's user type as External in the consent screen

- AND you accept that anyone with the client_id can request consent against your app

For most agency-with-clients setups, Internal-per-org is the right security model. The symlink-swap is a 50-line mitigation to the workflow friction it creates.

## Acknowledgement

The symlink-swap pattern was developed by Julian Dickie during a real bulk-upload session pushing 13 markdown files across two Workspace orgs. The friction it solves was documented in detail and surfaced via plugin feedback - that feedback is what produced this page.

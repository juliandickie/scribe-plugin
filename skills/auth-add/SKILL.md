---
description: Authenticate an additional Google account with workspace-mcp so multiple accounts can be used interchangeably.
disable-model-invocation: true
last-validated: 2026-05-15
---

# Scribe - Auth Add

Add a new Google account to the workspace-mcp token cache.

## Precondition check (do this FIRST)

Before running the OAuth flow, verify the OAuth client credentials are in place. If they are NOT, the auth flow will fail with a confusing "credentials not found" error.

**macOS / Linux:**
```bash
test -f ~/.workspace-mcp/oauth_client.json && echo "OAuth client present" || echo "MISSING - run /scribe:auth-init first"
```

**Windows (PowerShell):**
```powershell
if (Test-Path "$env:USERPROFILE\.workspace-mcp\oauth_client.json") { "OAuth client present" } else { "MISSING - run /scribe:auth-init first" }
```

If the file is missing, STOP and tell the user -

> No OAuth client configured at `~/.workspace-mcp/oauth_client.json`. You need to run `/scribe:auth-init` first to set up your Google Cloud credentials. This is a one-time process. After that, return here to add accounts.

Do NOT proceed past this point if the credentials file is missing.

## If preconditions pass - run the OAuth flow

If the user provided an email address in $ARGUMENTS, use that. Otherwise ask the user which email to authenticate.

The workspace-mcp server is already running in the background (Claude Code starts it automatically via the plugin manifest). There is no need to run it manually.

Call the `start_google_auth` MCP tool:

- `user_google_email` - the email the user provided

- `service_name` - use `"drive"` for the initial setup. This authorises the default scope set the server requests, which covers Drive, Docs, Gmail, Calendar, Sheets, Slides, and most other services in one consent flow. If you later see a "Scope not authorized" error for a specific service, re-run `start_google_auth` with that service name (e.g. `"contacts"`, `"tasks"`, `"forms"`, `"chat"`).

The tool returns a Google authorization URL. Present it to the user as a clickable link and instruct them to -

1. Click the link - it opens a Google consent screen in their browser.

2. Sign in if prompted, then click **Allow** to grant the requested permissions.

3. Wait for the browser to show a success or redirect page before closing it.

The token is then written automatically to `~/.workspace-mcp/credentials/<email>.json`. Subsequent MCP tool calls can target this account by passing its email as the `user_google_email` parameter.

**Important:** Complete the browser consent before the auth session expires (usually a few minutes). If the authorization URL expires before the user clicks Allow, call `start_google_auth` again to get a fresh URL.

## Cross-org note

If the user is adding an account from a different Google Workspace org than the one their `oauth_client.json` was created in, the consent flow will fail (Internal-type OAuth clients only accept identities from the owning Workspace).

In that case, walk them through the README's "Multi-org / cross-Workspace setup" section - they need a second OAuth client created inside the new Workspace and a way to switch between the two (the symlink-swap pattern documented in `docs/multi-org-setup.md`).

## Verification

After the flow completes, confirm the new credentials file was created.

**macOS / Linux:**
```bash
ls -la ~/.workspace-mcp/credentials/
```

**Windows (PowerShell):**
```powershell
Get-ChildItem "$env:USERPROFILE\.workspace-mcp\credentials\"
```

The newly-authenticated email should appear as a JSON file (e.g. `user@example.com.json`).

Suggest the user run `/scribe:auth-status` to verify all currently-authenticated accounts.

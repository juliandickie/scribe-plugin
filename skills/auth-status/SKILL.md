---
description: List all Google accounts authenticated with workspace-mcp and show their token status.
disable-model-invocation: true
last-validated: 2026-05-15
---

# Scribe - Auth Status

List authenticated accounts.

Check `~/.workspace-mcp/credentials/` for cached token files (one `<email>.json` per authenticated account). This is the canonical location set by `WORKSPACE_MCP_CREDENTIALS_DIR` in the plugin manifest.

**macOS / Linux:**

```bash
ls -la ~/.workspace-mcp/credentials/
```

**Windows (PowerShell):**

```powershell
Get-ChildItem "$env:USERPROFILE\.workspace-mcp\credentials\"
```

For each token file found, report -

- The email (from filename)

- File modification time (proxy for last refresh)

- File size (sanity check - empty or very small files indicate corruption)

For richer status (token expiry, scopes), open each JSON file and inspect its contents - the structure is the standard OAuth credentials JSON with `expiry`, `scopes`, and other fields. `workspace-mcp` does not expose a dedicated "list accounts" MCP tool; the credentials directory is the authoritative source.

If the directory is empty or does not exist, no accounts are authenticated. Suggest running `/scribe:auth-init` to set up the OAuth client and authenticate the first account, or `/scribe:auth-add EMAIL` to add another account once init has been done.

## Token health

Tokens auto-refresh on use (the workspace-mcp server handles refresh-token exchange transparently). If a tool call fails with "token expired" or "invalid grant," the user needs to re-authenticate that account via `/scribe:auth-add EMAIL`.

## Multi-org note

Tokens are self-contained per account file - the active OAuth client at the time of authentication is encoded in the token. Switching the active OAuth client (e.g. via `scripts/switch.sh` for multi-org setups) does NOT invalidate previously-cached tokens. See `docs/multi-org-setup.md`.

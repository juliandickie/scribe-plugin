---
description: Walk through first-run Google Cloud Project setup and OAuth consent for workspace-mcp.
disable-model-invocation: true
---

# Scribe - Auth Init

Guide the user through the one-time setup to authenticate workspace-mcp against their Google account.

This skill is the prerequisite for `/scribe:auth-add` and `/scribe:push`. After completing this skill, Claude Code can read and write Google Drive, Docs, Gmail, and Calendar on behalf of the authenticated account.

## Prerequisites - Install uvx

This skill requires `uvx` (the `uv` Python tool runner). Verify it is installed before proceeding:

```bash
uvx --version
```

If the command is not found, install `uv` now - then restart your terminal before continuing.

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**Windows note:** If the installer reports an execution policy error, run this first, then retry the installer:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

## 1. Create a Google Cloud Project

Visit https://console.cloud.google.com and sign in with the Google account that will own the OAuth consent screen.

Suggest project name `scribe-personal` for personal use, or `scribe-{org}` if setting up for a specific Google Workspace organisation. Note - for Workspace orgs, this project must be created INSIDE the org (signed in as a member of that Workspace).

## 2. Enable required APIs

Under **APIs & Services > Library**, enable -

- **Google Drive API** (mandatory)

- **Google Docs API** (mandatory)

- **Gmail API** (optional, only if the user wants Gmail access)

- **Google Calendar API** (optional, only if the user wants Calendar access)

## 3. Configure the OAuth consent screen

Under **APIs & Services > OAuth consent screen** -

- User type - choose **Internal** if all authenticating accounts are inside the same Google Workspace org. Choose **External** for personal Gmail accounts or mixed-org access.

- App name - "Scribe" or similar.

- Support and developer email - the user's own.

- Scopes - leave default (the consent flow asks for the scopes the server actually needs at runtime).

## 4. Create OAuth 2.0 Client ID

Under **APIs & Services > Credentials** -

- Click **Create Credentials > OAuth client ID**.

- Application type - **Desktop app**.

- Name - "Scribe desktop client" or similar.

- Click Create, then download the JSON file.

## 5. Save the credentials at the canonical path

The plugin's manifest points the MCP server at `~/.workspace-mcp/oauth_client.json`. The downloaded JSON MUST be saved at exactly that path (not the default filename Google assigns it).

**macOS / Linux:**
```bash
mkdir -p ~/.workspace-mcp
mv ~/Downloads/client_secret_*.apps.googleusercontent.com.json ~/.workspace-mcp/oauth_client.json
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.workspace-mcp"
$src = Get-ChildItem "$env:USERPROFILE\Downloads\client_secret_*.json" | Select-Object -First 1
Copy-Item $src.FullName "$env:USERPROFILE\.workspace-mcp\oauth_client.json"
```

If the user prefers a different path, they can set `GOOGLE_CLIENT_SECRET_PATH` in their `~/.claude/settings.json` MCP env config to override the manifest default - but the canonical path works without any config edits.

## 6. Authenticate via Claude Code

The workspace-mcp server is already running in the background (Claude Code starts it automatically via the plugin manifest). There is no need to run it manually.

Ask the user which Google email address they want to authenticate. Then call the `start_google_auth` MCP tool:

- `user_google_email` - the email the user provided

- `service_name` - use `"drive"` (this also covers Docs scope; calling once is sufficient for both Drive and Docs access)

The tool returns a Google authorization URL. Present it to the user as a clickable link and instruct them to -

1. Click the link - it opens a Google consent screen in their browser.

2. Sign in if prompted, then click **Allow** to grant the requested permissions.

3. Wait for the browser to show a success or redirect page before closing it.

The token is then written automatically to `~/.workspace-mcp/credentials/<email>.json`. The server uses it from this point forward without further prompts (the token auto-refreshes).

**Important:** Complete the browser consent before the auth session expires (usually a few minutes). If the authorization URL has expired before the user clicks Allow, call `start_google_auth` again to get a fresh URL.

## What happens after this skill

Once the user has authenticated their first account -

- Run `/scribe:auth-add EMAIL` to authenticate additional accounts

- Run `/scribe:push FILE` to upload markdown to Drive

- Use Claude in conversation - "push this markdown to my iDD Drive folder" - and the auto-activated `workspace` skill will route the call

## Multi-org note

If the user has multiple Google Workspace orgs (e.g. one for agency, one for institute), they need ONE OAuth client PER org, because Internal consent screens only accept identities from the owning Workspace. See the README's "Multi-org / cross-Workspace setup" section for the symlink-swap pattern.

## Troubleshooting

- "OAuth client credentials not found" - the credentials JSON is not at `~/.workspace-mcp/oauth_client.json`. Move or rename it and try again.

- "Scope not authorized" - the user accepted a narrower set of scopes than the server requests. Call `start_google_auth` again and accept all requested scopes on the consent screen.

- "Access blocked: This app's request is invalid" - usually means the OAuth consent screen was not fully configured (missing app name or, for External apps, the authenticating account is not listed as a test user). Go back to Step 3.

- "Missing required argument: service_name" - the `start_google_auth` tool requires both `user_google_email` and `service_name`. Valid values for `service_name` are `drive`, `docs`, `gmail`, `calendar`. Use `drive` for the initial setup.

- **Windows - credentials or client file not found after setup:** The plugin uses `${HOME}` to locate files. On some Windows systems `HOME` is not set as a standard environment variable. If credential or client-file path errors persist after placing the JSON correctly, add these overrides to your project `.claude/settings.json` under `mcpServers.scribe.env`, replacing `C:\Users\YourName` with your actual home directory path:
  ```json
  "GOOGLE_CLIENT_SECRET_PATH": "C:\\Users\\YourName\\.workspace-mcp\\oauth_client.json",
  "WORKSPACE_MCP_CREDENTIALS_DIR": "C:\\Users\\YourName\\.workspace-mcp\\credentials"
  ```

If the user hits any other friction, walk them through it. Refer them to the plugin README for screenshots and the multi-org appendix.

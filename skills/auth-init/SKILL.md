---
description: Walk through first-run Google Cloud Project setup and OAuth consent for workspace-mcp.
disable-model-invocation: true
---

# Scribe - Auth Init

Guide the user through the one-time setup to authenticate workspace-mcp against their Google account.

This skill is the prerequisite for `/scribe:auth-add` and `/scribe:push`. The plugin's manifest already points the MCP server at `~/.workspace-mcp/oauth_client.json` for OAuth client credentials, so the setup below ends at "save your downloaded credentials JSON to that exact path."

Explain, in order -

## 1. Create a Google Cloud Project

Visit https://console.cloud.google.com and sign in with the Google account that will own the OAuth consent screen.

Suggest project name `scribe-personal` for personal use, or `scribe-{org}` if setting up for a specific Google Workspace organisation. Note - for Workspace orgs, this project must be created INSIDE the org (signed in as a member of that Workspace).

## 2. Enable required APIs

Under **APIs & Services > Library**, enable -

- **Google Drive API** (mandatory)

- **Google Docs API** (mandatory)

- **Gmail API** (optional, only if user wants Gmail access)

- **Google Calendar API** (optional, only if user wants Calendar access)

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

- Click Create, then download the JSON.

## 5. Save the credentials at the canonical path

Critical - the plugin's manifest points the MCP server at `~/.workspace-mcp/oauth_client.json`. The downloaded JSON MUST be saved at exactly that path (not the default Downloads filename Google gives it).

```bash
mkdir -p ~/.workspace-mcp
mv ~/Downloads/client_secret_*.apps.googleusercontent.com.json ~/.workspace-mcp/oauth_client.json
```

If the user prefers a different path, they can set `GOOGLE_CLIENT_SECRET_PATH` in their `~/.claude/settings.json` MCP config to override the manifest default - but the canonical path works without any config edits.

## 6. Run the OAuth consent flow for the primary account

```bash
USER_GOOGLE_EMAIL=your-email@domain.com uvx --from git+https://github.com/juliandickie/google_workspace_mcp.git@fork-extension workspace-mcp --single-user --tools drive docs
```

A browser opens. Click "Allow." The token is cached at `~/.workspace-mcp/credentials/<email>.json` and the server exits or remains running depending on the user's setup.

After this step, the MCP server invocations from Claude Code work without further OAuth prompts (token auto-refreshes).

## What happens after this skill

Once the user has saved their credentials and authenticated their first account, they can -

- Run `/scribe:auth-add EMAIL` to authenticate additional accounts (each launches a fresh browser consent for that email)

- Run `/scribe:push FILE` to upload markdown to Drive

- Use Claude in conversation - "push this markdown to my iDD Drive folder" - and the auto-activated `workspace` skill will route the call

## Multi-org note

If the user has multiple Google Workspace orgs (e.g. one for agency, one for institute), they need ONE OAuth client PER org, because Internal consent screens only accept identities from the owning Workspace. See the README's "Multi-org / cross-Workspace setup" section for the symlink-swap pattern.

## Troubleshooting

- "OAuth client credentials not found" - the credentials JSON is not at `~/.workspace-mcp/oauth_client.json`. Move/rename it.

- "Scope not authorized" - the user accepted a narrower set of scopes than the server requests. Re-run the consent flow and accept all requested scopes.

- "Access blocked: This app's request is invalid" - usually means the OAuth consent screen wasn't fully configured (missing app name or test users for External). Go back to step 3.

If the user hits any other friction, walk them through it. Refer them to the plugin README for screenshots and the multi-org appendix.

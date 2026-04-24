# gworkspace-plugin

Claude Code plugin for Google Workspace automation - wraps the workspace-mcp server with a skill and slash commands.

## What this plugin does

This plugin wraps the `juliandickie/google_workspace_mcp` fork (our extension of taylorwilsdon's `google_workspace_mcp`) and adds a Claude Code skill plus five slash commands so Claude can read and write Google Docs (including specific tabs), upload and manage Drive files, search Gmail, and read Calendar events. The skill teaches Claude when and how to invoke the MCP server, and the commands give you quick shortcuts for OAuth setup, pushing markdown to Drive, and resolving client identifiers in AHPRA-style repos.

## Installation

Two commands in Claude Code -

    /plugin marketplace add juliandickie/gworkspace-plugin

    /plugin install gworkspace

The post-install hook will pip-install `workspace-mcp` from the `fork-extension` branch of the fork repo. If you have `uv` on your PATH it is installed as a uv tool; otherwise the hook falls back to `python3 -m pip install --user`.

## Google Cloud Project setup

Before authenticating, you need an OAuth client JSON from a Google Cloud Project.

1. Visit console.cloud.google.com and sign in with the Google account you want to automate against

2. Click the project selector at the top and choose "New Project" - suggest `gworkspace-personal` or similar

3. Under "APIs & Services > Library", enable these APIs -

   - Google Drive API (mandatory)

   - Google Docs API (mandatory)

   - Gmail API (optional)

   - Google Calendar API (optional)

4. Under "APIs & Services > Credentials", click "Create Credentials > OAuth client ID" and select application type "Desktop app"

5. Click the download button next to your new client ID to save the JSON credentials file

6. Save the file to `~/.workspace-mcp/oauth_client.json`. If you prefer a different path, export `GOOGLE_CLIENT_SECRET_PATH` pointing at your chosen location.

## First-run OAuth

**Option A - guided** - run the slash command inside Claude Code -

    /gws-auth-init

Claude walks you through each step, including the consent flow.

**Option B - manual** - run the server directly with the env vars set -

    export GOOGLE_CLIENT_SECRET_PATH=~/.workspace-mcp/oauth_client.json
    export USER_GOOGLE_EMAIL=your@email.com
    uvx workspace-mcp --single-user --tools drive docs

Your browser opens, you grant consent, the server caches the token, done. Subsequent MCP tool calls refresh automatically.

## Slash command reference

- `/gws-auth-init` - walk through first-run Google Cloud Project setup and OAuth consent

- `/gws-auth-add` - authenticate an additional Google account so multiple accounts can be used interchangeably

- `/gws-auth-status` - list all authenticated accounts and show token status

- `/gws-push` - push a local markdown file to Drive as a new or updated Google Doc

- `/gws-client-resolve` - resolve an AHPRA-style CLIENT-ID to its Google account email and Drive folder from profile.md frontmatter

## Troubleshooting

- **"No cached token"** - the server cannot find a token for the requested account. Run `/gws-auth-init` to complete the OAuth flow, or `/gws-auth-add` to add another account.

- **Token expired** - the MCP server auto-refreshes tokens in the background. If the refresh fails persistently, re-run the auth flow for that account.

- **"Invalid grant" or "unauthorized"** - the OAuth consent may have been revoked or the refresh token invalidated. Visit myaccount.google.com/permissions, remove the entry for your OAuth app, then re-auth.

- **API quota exceeded** - Google limits each user to 60 requests per minute by default (Drive API baseline). If you hit this, throttle the request rate or request a quota increase in the Cloud Console.

- **Multiple accounts** - the MCP server stores tokens for any number of accounts. To route a tool call to a specific account, pass the `user_google_email` parameter. The `/gws-client-resolve` command pulls this from the client's `profile.md` frontmatter in AHPRA-style repos.

## License

MIT - see LICENSE for the full text.

## Source

This plugin wraps the `juliandickie/google_workspace_mcp` fork, `fork-extension` branch. Bug reports and PRs welcome on that repo.

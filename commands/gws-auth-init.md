---
name: gws-auth-init
description: Walk through first-run Google Cloud Project setup and OAuth consent for workspace-mcp.
---

Guide the user through the one-time setup to authenticate workspace-mcp against their Google account -

Explain, in order -

1. Create a Google Cloud Project at console.cloud.google.com (suggest project name gworkspace-personal or similar)

2. Enable the following APIs in the new project - Google Drive API, Google Docs API, Gmail API (optional), Google Calendar API (optional)

3. Create an OAuth 2.0 Client ID of type "Desktop app" under APIs & Services > Credentials

4. Download the JSON credentials file

5. Save the file to ~/.workspace-mcp/oauth_client.json (or any path, then point the GOOGLE_CLIENT_SECRET_PATH env var at it)

6. Run the OAuth consent flow - on macOS -

       export GOOGLE_CLIENT_SECRET_PATH=~/.workspace-mcp/oauth_client.json
       export USER_GOOGLE_EMAIL=your-email@domain.com
       uvx workspace-mcp --single-user --tools drive docs

7. Browser opens for consent. Once consent is given, the MCP server is ready to use.

If the user hits any step's friction point, offer to walk them through it. Refer them to the plugin README for screenshots.

---
description: Authenticate an additional Google account with workspace-mcp so multiple accounts can be used interchangeably.
---

Add a new Google account to the workspace-mcp token cache.

Ask the user for the email address to authenticate.

Then run -

    USER_GOOGLE_EMAIL=<email> uvx workspace-mcp --single-user --tools drive docs

A browser opens for consent. Once complete, the account is cached at the fork's token storage path alongside any other authenticated accounts. Subsequent MCP tool calls can target this account by passing its email as the user_google_email parameter.

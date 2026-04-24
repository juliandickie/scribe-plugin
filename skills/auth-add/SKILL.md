---
description: Authenticate an additional Google account with workspace-mcp so multiple accounts can be used interchangeably.
disable-model-invocation: true
---

# Scribe - Auth Add

Add a new Google account to the workspace-mcp token cache.

If the user provided an email address in $ARGUMENTS, use that. Otherwise ask the user for the email address to authenticate.

Then run -

    USER_GOOGLE_EMAIL=<email> uvx workspace-mcp --single-user --tools drive docs

A browser opens for consent. Once complete, the account is cached at the fork's token storage path alongside any other authenticated accounts. Subsequent MCP tool calls can target this account by passing its email as the user_google_email parameter.

---
description: Authenticate an additional Google account with workspace-mcp so multiple accounts can be used interchangeably.
disable-model-invocation: true
---

# Scribe - Auth Add

Add a new Google account to the workspace-mcp token cache.

## Precondition check (do this FIRST)

Before running the OAuth flow, verify the OAuth client credentials are in place. If they are NOT, the auth flow will fail with a confusing "credentials not found" error.

```bash
test -f ~/.workspace-mcp/oauth_client.json && echo "OAuth client present" || echo "MISSING - run /scribe:auth-init first"
```

If the file is missing, STOP and tell the user -

> No OAuth client configured at `~/.workspace-mcp/oauth_client.json`. You need to run `/scribe:auth-init` first to set up your Google Cloud credentials. This is a one-time, ~5-minute process. After that, return here to add accounts.

Do NOT proceed past this point if the credentials file is missing.

## If preconditions pass - run the OAuth flow

If the user provided an email address in $ARGUMENTS, use that. Otherwise ask the user which email to authenticate.

```bash
USER_GOOGLE_EMAIL=<email> uvx --from git+https://github.com/juliandickie/google_workspace_mcp.git@fork-extension workspace-mcp --single-user --tools drive docs
```

A browser opens for consent. Once complete, the account's refresh token is cached at `~/.workspace-mcp/credentials/<email>.json` alongside any other authenticated accounts. Subsequent MCP tool calls can target this account by passing its email as the `user_google_email` parameter.

## Cross-org note

If the user is adding an account from a different Google Workspace org than the one their `oauth_client.json` was created in, the consent flow will fail (Internal-type OAuth clients only accept identities from the owning Workspace).

In that case, walk them through the README's "Multi-org / cross-Workspace setup" section - they need a SECOND OAuth client created inside the new Workspace and a way to switch between the two (the symlink-swap pattern documented in `docs/multi-org-setup.md`).

## Verification

After the flow completes, confirm by checking -

```bash
ls -la ~/.workspace-mcp/credentials/
```

The newly-authenticated email should appear as a JSON file (e.g. `julian@example.com.json`).

Suggest the user run `/scribe:auth-status` to verify all currently-authenticated accounts.

---
name: gws-auth-status
description: List all Google accounts authenticated with workspace-mcp and show their token status.
---

List authenticated accounts.

Check `~/.workspace-mcp/cli-tokens/` (the fork's encrypted token store) or the alternate spike token at `~/.workspace-mcp/spike_token.json`. Report -

- Which accounts have cached tokens

- Token expiry times (if readable)

- Any tokens that need refresh or re-auth

If no tokens exist, suggest running /gws-auth-init first.

---
description: {Trigger phrase a user would type, naming this service's specific nouns. Must be distinct from other service skills. Max 1024 chars. Use service-specific verbs like "search Gmail," "list events," "read spreadsheet rows."}
last-validated: 2026-05-15
---

# Scribe - {Service name}

{One sentence describing what this skill enables.}

## When to use

Use this skill when the user's request involves -

- {Specific user-facing scenario 1}

- {Specific user-facing scenario 2}

- {Specific user-facing scenario 3}

## MCP tool reference

The following tools are exposed by workspace-mcp for {service}. Pass `user_google_email` on every call (see workspace/SKILL.md for account selection rules).

### {tool_name_1}

{One-line purpose.}

Parameters:

- `param1` - {description}

- `param2` - {description, mark optional if so}

Returns: {return shape summary}

### {tool_name_2}

{...repeat for each tool the service exposes...}

## Common patterns

### {Pattern name 1}

1. {First tool call with parameters}

2. {Second tool call with parameters}

3. {Outcome}

### {Pattern name 2}

{...}

## Gotchas

- {Service-specific quirk 1, e.g. timezone handling, ID vs name distinction, pagination behaviour}

- {Service-specific quirk 2}

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing." Quick reference:

- Explicit user mention - use it

- Multi-account intent ("both inboxes," "all accounts") - auto-loop

- Client context - check profile.md or Contacts

- Single authenticated account - use it

- Ambiguous + multiple accounts - prompt once

## Cross-service handoff

When a request spans services, this skill's role ends after the {service} operation. The orchestration layer in workspace/SKILL.md handles chaining to other services.

## Source

This skill wraps `workspace-mcp` tools for {service}. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

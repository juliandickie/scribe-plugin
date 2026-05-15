---
description: Use when the user's request involves Google Chat - sending messages to spaces, reading channel history, managing Google Chat threads. Triggers on Google Chat, Chat message, Chat space, gchat. Does NOT trigger on Slack - that goes to the Slack plugin if present.
last-validated: 2026-05-15
---

# Scribe - Chat

Enables Claude to send and read messages in Google Chat spaces.

## When to use

Use this skill when the user's request involves -

- Sending a message to a Google Chat space

- Reading recent messages in a space

- Posting a workflow summary to a Chat channel

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### send_chat_message

Send a message to a space.

Parameters:

- `space_id` - format `spaces/ABCDEF`

- `text` (or rich content)

- `thread_key` (optional, to reply in thread)

- `user_google_email`

### read_chat_messages

Get messages from a space.

Parameters: `space_id`, `time_min`/`time_max` (optional), `user_google_email`.

### list_chat_spaces

List spaces the user is in.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Post a workflow summary

1. After a workflow completes, `send_chat_message` to a designated space with a one-line summary and any artifact URLs.

### Read recent activity

1. `read_chat_messages` for a space over a time window.

2. Surface as structured summary with sender, timestamp, content excerpt.

## Gotchas

- Google Chat is the Workspace messaging product. Distinct from Slack and Microsoft Teams. If the user's team uses Slack primarily, use the Slack plugin instead per the cross-plugin composition pattern.

- Chat space IDs are different from regular email addresses. They look like `spaces/ABCDEF`.

- Bot/app messages may be subject to additional permissions in some Workspace orgs.

## Account selection

Pass `user_google_email` on every call. The account must be a member of the target space.

## Cross-service handoff

When posting a workflow result to Chat, this skill handles the message send. The orchestration layer composed the message content from other services.

## Source

This skill wraps `workspace-mcp` tools for Google Chat. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

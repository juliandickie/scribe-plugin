---
description: Use when the user's request involves Google Chat - sending messages to spaces, reading channel history, managing Google Chat threads, searching messages, reactions. Triggers on Google Chat, Chat message, Chat space, gchat. Does NOT trigger on Slack - that goes to the Slack plugin if present.
last-validated: 2026-05-15
---

# Scribe - Chat

Enables Claude to send, read, and search messages in Google Chat spaces, plus manage reactions and attachments.

## When to use

Use this skill when the user's request involves -

- Sending a message to a Google Chat space

- Reading recent messages in a space

- Searching for messages by keyword across spaces

- Posting a workflow summary to a Chat channel

- Adding a reaction to a message

- Downloading a Chat attachment

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Google Chat. Pass `user_google_email` on every call.

### list_spaces

List Chat spaces the user is a member of.

Parameters: `user_google_email`, optional pagination.

### get_messages

Get messages from a space.

Parameters:

- `space_id` - format `spaces/ABCDEF`

- Optional time/cursor filters

- `user_google_email`

### send_message

Send a message to a space.

Parameters:

- `space_id`

- `text` (or rich content)

- `thread_key` (optional, to reply in a thread)

- `user_google_email`

### search_messages

Search messages by keyword across spaces the user has access to.

Parameters: `query`, optional space filter, `user_google_email`.

### create_reaction

Add an emoji reaction to a specific message.

Parameters: `message_name`, `emoji`, `user_google_email`.

### download_chat_attachment

Download an attachment from a Chat message.

Parameters: attachment reference, `user_google_email`.

## Common patterns

### Post a workflow summary to a space

1. After a workflow completes, `send_message` to a designated space with a one-line summary and any artifact URLs.

### Read recent activity

1. `get_messages` for a space over a time window.

2. Surface as structured summary with sender, timestamp, content excerpt.

### Find a discussion by topic

1. `search_messages` with the topic as query.

2. For relevant hits, `get_messages` to read the surrounding context.

### Acknowledge a workflow result

1. After `send_message` posts a summary, `create_reaction` to add a thumbs-up so participants know action was taken.

## Gotchas

- Google Chat is the Workspace messaging product. Distinct from Slack and Microsoft Teams. If the user's team uses Slack primarily, use the Slack plugin instead per the cross-plugin composition pattern.

- Chat space IDs use the `spaces/ABCDEF` format. They are not regular email addresses or random short IDs.

- Tool names do NOT have a `chat_` prefix - just `list_spaces`, `get_messages`, `send_message`, etc. Don't try `send_chat_message` - it doesn't exist.

- Bot/app messages may be subject to additional permissions in some Workspace orgs. If `send_message` fails with a permission error, the user's org may restrict app-posted messages.

- `search_messages` searches across spaces the user has access to. If results are empty, confirm the space is one the authenticated account is a member of.

## Account selection

Pass `user_google_email` on every call. The account must be a member of the target space.

## Cross-service handoff

When posting a workflow result to Chat, this skill handles the message send. The orchestration layer composed the message content from other services.

## Source

This skill wraps `workspace-mcp` tools for Google Chat. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

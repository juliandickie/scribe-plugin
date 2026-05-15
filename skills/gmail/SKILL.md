---
description: Use when the user's request involves Gmail - reading emails, searching threads, sending or drafting messages, managing labels, batch label modifications, or any inbox operation. Triggers on words like email, inbox, message, thread, label, draft, send, reply, forward, archive.
last-validated: 2026-05-15
---

# Scribe - Gmail

Enables Claude to read, search, draft, send, and organise Gmail messages and threads through the workspace-mcp server.

## When to use

Use this skill when the user's request involves -

- Reading or searching emails by sender, subject, date, label, or content

- Drafting, sending, or scheduling email replies and new messages

- Managing labels, applying or removing labels in bulk

- Filtering or organising the inbox

- Reading attachments from a message

## MCP tool reference

The following tools are exposed by workspace-mcp for Gmail. Pass `user_google_email` on every call (see workspace/SKILL.md for account selection rules).

### search_gmail_messages

Search Gmail with Gmail query syntax (`from:`, `subject:`, `is:unread`, etc.).

Parameters:

- `query` - Gmail search query string

- `user_google_email` - account to search

- `max_results` (optional) - cap the number of returned messages

Returns: list of message metadata (id, thread_id, subject, snippet, from, date).

### get_gmail_message_content

Fetch full content of one message by ID.

Parameters:

- `message_id`

- `user_google_email`

Returns: full message body (text or HTML), headers, attachment metadata.

### get_gmail_messages_content_batch

Batch fetch multiple messages.

Parameters:

- `message_ids[]` - array of IDs

- `user_google_email`

Returns: parallel results array with success/failure per ID.

### get_gmail_thread_content

Fetch all messages in a thread.

Parameters:

- `thread_id`

- `user_google_email`

Returns: ordered list of messages in the thread.

### get_gmail_threads_content_batch

Batch fetch multiple threads.

### search_gmail_threads

Thread-level search.

Parameters:

- `query` (Gmail query syntax)

- `user_google_email`

### get_gmail_attachment_content

Download attachment content.

Parameters:

- `message_id`

- `attachment_id`

- `user_google_email`

Returns: attachment bytes or saved-to-disk reference.

### send_gmail_message

Send a new message.

Parameters:

- `to`, `subject`, `body` (required)

- `cc`, `bcc` (optional)

- `user_google_email`

### draft_gmail_message

Create a draft. Same parameter shape as send.

### modify_gmail_message_labels

Apply or remove labels on a single message.

Parameters:

- `message_id`

- `add_labels[]`

- `remove_labels[]`

- `user_google_email`

### batch_modify_gmail_message_labels

Bulk label changes across many messages in one call.

### list_gmail_labels

List available labels (system + user).

### manage_gmail_label

Create, update, or delete labels.

### list_gmail_filters

List current Gmail filters.

### manage_gmail_filter

Create or delete filters.

## Common patterns

### Find recent unread from a sender

1. `search_gmail_messages` with `query="from:sender@x.com is:unread newer_than:7d"`.

2. For each result, `get_gmail_thread_content` to read the full thread.

### Draft a reply

1. `get_gmail_message_content` to read the original message.

2. `draft_gmail_message` with `to`/`subject`/`body` derived from context. Always draft, never send unprompted unless the user explicitly says "send."

### Bulk archive read promotions

1. `search_gmail_messages` with `query="label:promotions is:read"`, collect IDs.

2. `batch_modify_gmail_message_labels` with `remove_labels=["INBOX"]`.

## Gotchas

- Gmail query syntax is its own DSL. Use `is:unread`, `from:`, `to:`, `subject:`, `newer_than:7d`, `has:attachment`. Don't try SQL-style or natural language; it won't work.

- Label IDs and label names are different. `INBOX` is a system label; user labels have format `Label_XXXX`. `list_gmail_labels` shows both.

- Sending requires `gmail:send` scope. If you see permission errors on send/draft, the user authenticated with a narrower scope set - they need to re-run `start_google_auth` with `gmail` service.

- Batch operations return per-item success/failure. Always check the response for partial failures before reporting success.

- Email body can be plain text or HTML. Detect by content; the tool accepts either via `body` param.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing." Quick reference:

- Explicit user mention - use it

- Multi-account intent ("both inboxes," "all accounts") - auto-loop

- Client context - check profile.md or Contacts

- Single authenticated account - use it

- Ambiguous + multiple accounts - prompt once

## Cross-service handoff

When a request spans services, this skill's role ends after the Gmail operation. The orchestration layer in workspace/SKILL.md handles chaining to other services (e.g. saving an email to a Doc, attaching a thread context to a Sheet row).

## Source

This skill wraps `workspace-mcp` tools for Gmail. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

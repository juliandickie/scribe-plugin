---
description: Use when the user's request involves Gmail - reading emails, searching threads, sending or drafting messages, managing labels, batch label modifications, or any inbox operation. Triggers on words like email, inbox, message, thread, label, draft, send, reply, forward, archive.
last-validated: 2026-08-28
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

- `include_headers` (optional) - adds Subject, From, and Date to each result row, so triage does not need a second content call. Default output is unchanged when omitted.

Returns: list of message metadata (id, thread_id, subject, snippet, from, date).

### get_gmail_message_content

Fetch full content of one message by ID.

Parameters:

- `message_id`

- `user_google_email`

- `full` (optional) - return the complete message with no truncation limit. In the stdio deployment Scribe uses, a large body is saved to the attachments directory and the file path returned. Works with all `body_format` values including `raw` (byte-exact `.eml`).

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

Batch fetch multiple threads by IDs.

Note: there is no dedicated thread-level search tool. To find threads, use `search_gmail_messages` (results include `thread_id`) and then call `get_gmail_thread_content` or `get_gmail_threads_content_batch` to fetch the full thread content for the IDs you care about.

### get_gmail_attachment_content

Download attachment content.

Parameters:

- `message_id`

- `attachment_id`

- `user_google_email`

Returns: attachment bytes or saved-to-disk reference.

### send_gmail_message

Send a new message, reply, or forward. For a plain new message pass `to`, `subject`, `body`, `user_google_email`. The schema no longer hard-requires `to`/`subject`/`body` because replies and forwards can derive them - still treat them as required for a plain send.

Key optional params (the live tool schema carries the full list and defaults; these are the ones that change behaviour) -

- `body_format` - `plain` (default) or `html`. Use `html` to send a formatted HTML email.

- `cc`, `bcc` - additional recipients.

- `from_email` plus `from_name` - send from a configured Gmail Send As alias (set up under Settings > Accounts > Send mail as). `from_name` sets the display name, producing a `Name <email>` From header.

- `include_signature` - defaults true and appends the Gmail signature. Set false when the body already carries its own sign-off, otherwise the message gets a double signature.

- `attachments` - see the Attachments subsection below.

- `thread_id`, `in_reply_to`, `references`, `quote_original` - reply threading. `quote_original` requires `thread_id`. Given only `thread_id`, the reply targets the latest non-draft, non-trash message in the thread.

- `reply_all` - derive recipients from the thread (your own address and Send As alias excluded). With `reply_all`, `to` becomes optional.

- `forward_message_id` plus `include_forwarded_attachments` - forward an existing message, attachments included.

### draft_gmail_message

Create a draft. Same surface as `send_gmail_message`. `to` is optional for a draft (you can save a recipient-less draft); for a plain send, still supply it. This is the default for any reply you are not explicitly told to send. Drafted replies attach to their thread and appear inline in the original conversation.

### Attachments (send and draft)

`attachments` is a list; each item is one of three shapes. Pick by where the file already is -

- Already in Drive or on an email - pass `{"url": "<mcp-url>"}` using the URL returned by `get_drive_file_download_url` or `get_gmail_attachment_content`. No local staging needed.

- A genuinely-local file (for example on the Desktop) - pass `{"path": "<file>"}`. The `path` mode is the only one bound by the `ALLOWED_FILE_DIRS` sandbox, so the file must already live in `~/.workspace-mcp/attachments` or a configured allowed dir. See "File and attachment handling" in `workspace/SKILL.md` for the map and `push/SKILL.md` for the staging decision tree.

- Bytes already in memory - pass `{"content": "<base64>", "filename": "<name>"}` (standard base64, not urlsafe).

- An inline image to embed in an HTML body - add a `content_id` key to the attachment and reference it from the `body` (with `body_format: html`) as `cid:<content_id>` inside an `<img>` tag. Needs workspace-mcp 1.21.1 or newer.

Optional `mime_type` per item is auto-detected if omitted.

### modify_gmail_message_labels

Apply or remove labels on a single message.

Parameters:

- `message_id`

- `add_labels[]`

- `remove_labels[]`

- `user_google_email`

### batch_modify_gmail_message_labels

Bulk label changes across many messages in one call. Optional `verify` re-reads the messages afterwards and reports what Gmail actually changed rather than echoing the request (Gmail silently no-ops some label changes).

### list_gmail_labels

List available labels (system + user). Optional `prefix`, `compact`, and `include_system` filter the label tree - on label-heavy accounts a prefix filter cuts the response from tens of KB to under one.

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

- Attachments have three modes (url / path / content). Only `path` hits the `ALLOWED_FILE_DIRS` sandbox. For a file already in Drive or on an email, pass its `url` from `get_drive_file_download_url` / `get_gmail_attachment_content` and skip staging entirely.

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

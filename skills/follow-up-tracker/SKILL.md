---
description: Find sent emails with no reply after N days; surface them with optional draft follow-ups. Invoke via /scribe:follow-up-tracker.
disable-model-invocation: true
argument-hint: [--days 7] [--account email] [--draft-replies]
last-validated: 2026-05-15
---

# Scribe - Follow-up tracker

Identifies sent emails that haven't received a reply after a configurable threshold (default 7 days). Optionally drafts polite follow-up replies for each.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--days N` (optional, default 7) - how many days without reply before flagging.

- `--account email` (optional) - single account. Default - all accounts.

- `--draft-replies` (optional flag) - also draft a follow-up reply for each.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Per account - sent emails in window** - `search_gmail_messages` with `query="in:sent older_than:<days>d newer_than:<days+30>d"` (cap at 30 days back to avoid an unbounded scan).

3. **Per message - check for reply** - `get_gmail_thread_content` to see whether a reply came after the original sent message.

4. **Filter** - to those with no reply (threads where the latest message is the user's sent one, with no incoming after).

5. **Optional draft** - if `--draft-replies`, `draft_gmail_message` per item with a polite follow-up referencing the original.

6. **Return** - list with subject, recipient, days-since-sent, and (if drafted) draft URLs.

## Multi-account behaviour

Loops all accounts by default.

## Cross-plugin composition

- **ClickUp plugin** - for follow-ups that look task-related (e.g. follow-up on a quote, proposal, deliverable), create a "follow up" task with the email URL.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "What emails am I waiting on replies to?"

- "Find emails I sent two weeks ago that haven't been answered, draft follow-ups"

Explicit args:

- `/scribe:follow-up-tracker --days 14 --draft-replies`

- `/scribe:follow-up-tracker --account julian@idd`

## Failure modes

- **No unanswered emails** - report clean inbox.

- **Thread structure ambiguous** (user replied to self after sending) - filter heuristic should ignore self-replies as "no reply received."

- **Recipients with autoresponders** - autoresponder text may look like a reply. Treat single-message responses with "out of office" patterns as non-replies.

## Output

Always return:

- One-line summary - "X emails awaiting reply older than Y days"

- List of emails with subject, recipient, days-since

- Draft URLs if drafted

- Cross-plugin steps skipped

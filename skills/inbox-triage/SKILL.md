---
description: Scan all authenticated Gmail inboxes, categorise unread by urgency and sender type, apply labels, and draft replies to flagged threads. Invoke via /scribe:inbox-triage.
disable-model-invocation: true
argument-hint: [--account email] [--since 1d|7d|...] [--no-drafts]
last-validated: 2026-05-15
---

# Scribe - Inbox triage

Triages the user's Gmail inbox(es). Categorises unread messages into Action (needs a reply), FYI (just read), and Noise (archive candidate). Applies appropriate labels. For Action items, drafts a reply in the user's voice (saved as draft, never sent automatically).

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (optional) - single account. Default - all authenticated accounts.

- `--since 7d` (optional) - time window. Default - 24 hours.

- `--no-drafts` (optional flag) - skip the draft-reply step.

## Tool call sequence

1. **Resolve accounts** - `--account` if specified, otherwise `list_authenticated_accounts`.

2. **Per account - fetch unread** - `search_gmail_messages` with `query="is:unread newer_than:<since>"`.

3. **Per message - read content** - `get_gmail_message_content` for body and headers.

4. **Classify each message** - Action / FYI / Noise based on sender, subject patterns, and content cues. Examples - direct questions to user = Action; newsletters = FYI; "unsubscribe" footers prominent = Noise.

5. **Label setup** - `list_gmail_labels` to find or create `Triage/Action`, `Triage/FYI`, `Triage/Noise`. Use `manage_gmail_label` to create any missing.

6. **Apply labels** - `batch_modify_gmail_message_labels` to apply categorisation in one call per account.

7. **Draft replies** (unless `--no-drafts`) - for each Action message, `draft_gmail_message` with a contextual reply.

8. **Return summary** - counts per category, list of drafted replies with links to drafts.

## Multi-account behaviour

Loops across all authenticated accounts by default. Single account when `--account` is specified.

## Cross-plugin composition

- **ClickUp plugin** - for Action items that look like task creation requests, create a ClickUp task and link the email URL.

- **Slack plugin** - post a one-line triage summary to a designated channel ("Triaged 47 emails - 8 Action, 12 FYI, 27 Noise").

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Triage my inbox"

- "Sort my unread from the last week"

- "Inbox triage but don't draft replies"

Explicit args:

- `/scribe:inbox-triage --since 3d --no-drafts`

- `/scribe:inbox-triage --account julian@idd`

## Failure modes

- **Label creation forbidden** - some Workspace orgs restrict label creation. Fall back to categorisation in the output without applying labels.

- **Draft creation fails** - the user's scope may be readonly. Surface what would have been drafted as text in the response.

- **No unread** - report clean inbox.

## Output

Always return:

- Category counts per account

- Drafted replies with draft URLs

- Any cross-plugin steps skipped

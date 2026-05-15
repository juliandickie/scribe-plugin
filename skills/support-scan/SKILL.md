---
description: Scan a designated support inbox for new inquiries, log each to a tracking sheet, draft initial response. Invoke via /scribe:support-scan.
disable-model-invocation: true
argument-hint: [--account email] [--sheet-id ID] [--since 1d]
last-validated: 2026-05-15
---

# Scribe - Support inquiry scan

Designed for support inbox triage. Scans a specified account's inbox for new inquiries in the time window, classifies each (general inquiry, complaint, refund, course-question, other), logs each row to a designated tracking sheet, and drafts an initial response in the support team's voice.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (required if user has multiple accounts) - the support inbox to scan.

- `--sheet-id ID` (required first time) - the tracking sheet ID. Cached in conversation for repeat invocations.

- `--since 1d` (optional) - time window. Default - 1 day.

If `--sheet-id` is missing, ask the user once.

## Tool call sequence

1. **Validate parameters** - if `--sheet-id` missing, ask user. If user has multiple accounts and no `--account`, ask which.

2. **Scan inbox** - `search_gmail_messages` with `query="is:unread newer_than:<since>"` on the support account.

3. **Per message - read thread** - `get_gmail_thread_content` for full context including any prior reply.

4. **Classify intent** - rule-based or LLM judgment in prose. Categories - inquiry, complaint, refund, course-question, other.

5. **Per inquiry - log to sheet** - append row with `[timestamp, sender, subject, classification, thread_url, status="new"]`.

6. **Per inquiry - draft response** - `draft_gmail_message` with a context-aware reply that acknowledges and asks any clarifying questions.

7. **Return summary** - counts per category, sheet URL with rows added, list of drafted responses with draft URLs.

## Multi-account behaviour

Single account (the designated support inbox). Requires `--account` if the user has multiple authenticated accounts.

## Cross-plugin composition

- **ClickUp plugin** - for inquiries classified as bugs/complaints, create a ClickUp task in the support list with the email URL.

- **Slack plugin** - post new urgent inquiries (complaints, refund requests) to a `#support` channel.

- **Spiffy plugin** - for refund or credit inquiries, look up purchase history and credit balance before drafting the response. Include the lookup result in the draft.

- **AC Builder plugin** - enrich sender info with AC tags before classification (e.g. "this contact is in the Course - Implant 2026 list").

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Scan our support inbox"

- "Run support triage on julian@idd, log to the support tracker"

Explicit args:

- `/scribe:support-scan --account support@idd --sheet-id 1AB...XYZ --since 12h`

## Failure modes

- **Sheet not found** - prompt user for correct sheet ID or offer to create one.

- **No new inquiries** - report "No new inquiries in window" and exit clean.

- **Classification ambiguous** - default to "other" and surface for human review in the sheet status column.

## Output

Always return:

- One-line summary - "Logged X new inquiries, drafted Y responses"

- Sheet URL

- Per-category counts

- Draft URLs

- Cross-plugin steps skipped

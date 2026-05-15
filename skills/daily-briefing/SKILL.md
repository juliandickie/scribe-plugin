---
description: Scan all authenticated Gmail inboxes for unread or flagged messages today, pull today's calendar events from all accounts, and surface urgent items with context. Invoke via /scribe:daily-briefing.
disable-model-invocation: true
argument-hint: [--account email] [--date YYYY-MM-DD]
last-validated: 2026-05-15
---

# Scribe - Daily briefing

Compiles a daily morning briefing across all the user's authenticated Google accounts. Scans inboxes for unread/flagged messages received in the last 24 hours, pulls today's calendar events from every account's primary calendar, and surfaces anything tagged urgent or from named-VIP senders. Output is a short, scannable summary the user can read in 60 seconds.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (optional) - restrict to a single account. Default - loop across all authenticated accounts.

- `--date YYYY-MM-DD` (optional) - the day to brief on. Default - today in user's local timezone.

If a parameter is missing and required, ask the user once.

## Tool call sequence

1. **Enumerate accounts** - call `list_authenticated_accounts` to get the set of accounts to scan (skip if `--account` was specified).

2. **Per account - unread email scan** - `search_gmail_messages` with `query="(is:unread OR is:starred) newer_than:1d"`. Capture top 10 by recency.

3. **Per account - today's calendar** - `get_events` with `calendar_id="primary"`, `time_min=<date 00:00>`, `time_max=<date 23:59>`. Capture all events.

4. **Compose the briefing** - structured output with sections: Today's Calendar (per account), Unread/Flagged Email (per account), Anything Urgent (VIPs or marked urgent in subject/body).

5. **Return** - the briefing as a markdown response. Do NOT save to Drive unless the user asks.

## Multi-account behaviour

Loops across all authenticated accounts by default. Single account when `--account` is specified. This is explicit multi-account intent ("daily briefing" implies the whole picture), so auto-loop without prompting.

## Cross-plugin composition

After the Scribe tool chain completes, check whether these plugins are installed and chain accordingly:

- **ClickUp plugin** - if installed, also surface any tasks due today across configured ClickUp lists.

- **Slack plugin** - if installed, surface DMs or @mentions from the last 24 hours.

- **AC Builder plugin** - if installed, enrich unread emails from new contacts with AC tag info (e.g. "from a Lead - Course tag contact").

If a referenced plugin is not available, skip its step silently and note it in the final summary ("ClickUp plugin not installed, no task list pulled").

## Example invocations

Natural language:

- "What's on my plate today?"

- "Give me a daily briefing"

- "Daily briefing for julian@idd only"

Explicit args:

- `/scribe:daily-briefing --account julian@idd`

- `/scribe:daily-briefing --date 2026-05-16`

## Failure modes

- **No accounts authenticated** - direct to `/scribe:auth-init`.

- **Some accounts fail** (token expired for one) - skip those, note in summary, continue with the rest. Don't fail the whole briefing because of one bad account.

- **No emails or events** - produce a "Quiet day" briefing rather than empty output.

## Output

Always return:

- A short one-line summary ("3 accounts scanned, 12 unread, 4 events today, 1 urgent")

- Per-section content (Calendar, Unread, Urgent)

- A note for any cross-plugin steps that were skipped or any accounts that errored

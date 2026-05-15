---
description: Compile the past week's emails, calendar events, and Drive document activity into a summary report doc. Invoke via /scribe:weekly-wrap.
disable-model-invocation: true
argument-hint: [--week current|last|N] [--output-folder ID] [--account email]
last-validated: 2026-05-15
---

# Scribe - Weekly wrap

Generates a weekly summary report compiling all the user's activity across Gmail, Calendar, and Drive into a structured doc. Sections include emails sent and received, meetings attended, docs created or significantly edited.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--week current|last|N` (optional) - default `last`. `current` = this week so far, `last` = last full week, `N` = N weeks ago.

- `--output-folder ID` (optional) - destination Drive folder. Default - "Weekly wraps" folder under My Drive, created if absent.

- `--account email` (optional) - single account. Default - all accounts.

## Tool call sequence

1. **Compute week date range** - based on `--week`. "last" = previous Monday-Sunday window in user's timezone.

2. **Resolve accounts** - all unless `--account` specified.

3. **Per account - email received** - `search_gmail_messages` with `query="newer_than:<7d> older_than:<0d>"` (adjusted for the chosen week).

4. **Per account - email sent** - same, with `in:sent` filter.

5. **Per account - calendar events** - `get_events` for the week's range.

6. **Drive activity** - `search_drive_files` for files modified in the week's range owned by the user.

7. **Resolve output folder** - `search_drive_files` for "Weekly wraps", `create_drive_folder` if absent.

8. **Create wrap doc** - `create_doc` titled `Weekly wrap - <week-of-date>` in output folder.

9. **Populate doc** - sections - Activity overview (counts), Notable emails sent and received, Meetings attended, Documents created and edited.

10. **Return** - the doc URL plus a one-line summary.

## Multi-account behaviour

Loops all accounts by default. The output doc surfaces per-account breakdowns in each section.

## Cross-plugin composition

- **ClickUp plugin** - include tasks completed and tasks created in the week from configured lists.

- **Spiffy plugin** - include the week's enrollment, refund, and credit activity.

- **Slack plugin** - include count of messages sent in monitored channels.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Give me a weekly wrap"

- "Compile last week's activity into a report"

- "Weekly wrap for two weeks ago"

Explicit args:

- `/scribe:weekly-wrap --week last --output-folder ABC...`

- `/scribe:weekly-wrap --week 2`

## Failure modes

- **No activity** - produce a doc anyway with "Quiet week" sections.

- **Output folder creation fails** - save to My Drive root with a fallback name.

- **Some accounts fail** - skip those, note in the doc.

## Output

Always return:

- The wrap doc URL

- One-line summary - "Compiled X emails, Y events, Z docs from N accounts"

- Cross-plugin steps skipped

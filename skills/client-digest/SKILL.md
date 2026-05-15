---
description: Aggregate emails, calendar events, and Drive activity (comments, suggested edits, recent changes) for a named client or contact. Invoke via /scribe:client-digest.
disable-model-invocation: true
argument-hint: <client-or-contact> [--since 7d] [--account email]
last-validated: 2026-05-15
---

# Scribe - Client digest

Builds a comprehensive activity digest for a specific client, contact, or company. Surfaces all email threads, calendar events, and Drive document activity (comments, suggested edits, recent modifications) related to that entity within the time window.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `<client-or-contact>` (positional, required) - name, email, or AHPRA CLIENT-ID.

- `--since 7d` (optional) - time window. Default - 7 days.

- `--account email` (optional) - account to scope to. Default - all accounts.

If positional arg missing, ask user.

## Tool call sequence

1. **Resolve the contact** - if AHPRA CLIENT-ID, use the client-resolve skill. If name, search Contacts. If email, use directly.

2. **Resolve accounts** - all unless `--account` specified.

3. **Per account - email scan** - `search_gmail_messages` with `query="from:<email> OR to:<email> newer_than:<since>"`.

4. **Per account - calendar scan** - `get_events` with `q=<contact-name>` or filter events with the contact as attendee.

5. **Drive search** - `search_drive_files` for docs that mention the contact's name or are shared with their email.

6. **Per matching doc - comment activity** - `list_document_comments` to surface comment activity in the time window.

7. **Assemble digest** - sections - Emails (per account), Calendar events, Drive activity (modified, shared, commented).

8. **Return** - as markdown summary OR save to a doc if user prefers (ask once if not specified).

## Multi-account behaviour

Loops all accounts by default. Single account if `--account` specified.

## Cross-plugin composition

- **AC Builder plugin** - include the contact's AC tags, list memberships, and recent automation history.

- **Slack plugin** - search Slack channels for mentions of the contact or company name.

- **Spiffy plugin** - if the contact is a customer, include purchase history, course progress, and credit balance.

- **ClickUp plugin** - surface any open ClickUp tasks tied to the contact (search for the contact name in task titles or descriptions).

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Tell me everything about Sarah Smith"

- "Client digest for IDD-ED-007 over the last 30 days"

- "What's been happening with john@example.com lately?"

Explicit args:

- `/scribe:client-digest "sarah@example.com" --since 30d`

## Failure modes

- **No matches** - report "No activity found in window for <contact>".

- **Multiple contacts match a name** - prompt user to pick by listing options with disambiguating info (organisation, last contact date).

## Output

Always return:

- One-line summary - "Found X emails, Y events, Z Drive docs with activity for <contact>"

- Per-section content

- Cross-plugin steps skipped

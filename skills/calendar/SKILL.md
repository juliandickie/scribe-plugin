---
description: Use when the user's request involves Google Calendar - reading events, creating meetings, checking availability, managing focus time or out-of-office, listing calendars, or any scheduling operation. Triggers on calendar, event, meeting, schedule, availability, free/busy, OOO, focus time.
last-validated: 2026-05-15
---

# Scribe - Calendar

Enables Claude to read, create, update, and reason about Google Calendar events across one or more authenticated accounts.

## When to use

Use this skill when the user's request involves -

- Reading today's, upcoming, or past calendar events

- Creating new events or meetings

- Checking free/busy across attendees

- Managing focus time blocks or out-of-office responder

- Listing or describing calendars the user has access to

## MCP tool reference

The following tools are exposed by workspace-mcp for Calendar. Pass `user_google_email` on every call.

### get_events

List events from a calendar.

Parameters:

- `calendar_id` - use `"primary"` for the user's main calendar

- `time_min`, `time_max` - RFC 3339 datetimes with timezone

- `max_results` (optional)

- `user_google_email`

Returns: list of event metadata (id, summary, start, end, attendees, location, description).

### manage_event

Create, update, or delete an event.

Parameters:

- `action` - `"create"`, `"update"`, or `"delete"`

- `event_id` - required for update/delete

- Event fields: `summary`, `start`, `end`, `attendees`, `description`, `location`

- `calendar_id`

- `user_google_email`

### query_freebusy

Check availability across calendars.

Parameters:

- `time_min`, `time_max`

- `calendar_ids[]`

- `user_google_email`

Returns: busy intervals per calendar (NOT free intervals - compute free = window minus busy).

### list_calendars

Enumerate calendars the user can read.

Parameters:

- `user_google_email`

### create_calendar

Create a new calendar.

Parameters:

- `summary`, `description`

- `user_google_email`

### manage_focus_time

Read or manage focus time blocks.

Parameters:

- `action`

- `start`, `end`

- `user_google_email`

### manage_out_of_office

Read or set OOO auto-reply.

## Common patterns

### Today's agenda

1. `get_events` with `calendar_id="primary"`, `time_min=<today 00:00>`, `time_max=<today 23:59>` in the user's timezone.

### Schedule a meeting respecting availability

1. `query_freebusy` with attendees' calendars to find a free slot.

2. `manage_event` `action="create"` with attendees, summary, time selected from the free slots.

### Multi-account day view

1. `list_authenticated_accounts` to enumerate accounts.

2. Per account, `get_events` for the day.

3. Merge results sorted by start time.

## Gotchas

- All event times use RFC 3339 with timezone (e.g. `2026-05-15T09:00:00+10:00` for Brisbane). The server does NOT auto-handle naive datetimes - always pass timezone.

- `calendar_id="primary"` is the user's main calendar. Other calendars need their full ID; get them via `list_calendars`.

- Recurring events return one entry per occurrence within the time range, not one master entry.

- `query_freebusy` returns busy intervals, not free intervals. Compute free = window minus busy.

- Attendees added in `manage_event` get an automatic invite email. To suppress, the upstream tool may have a flag; check current docs.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing." Quick reference:

- Explicit user mention - use it

- Multi-account intent ("both inboxes," "all accounts") - auto-loop

- Client context - check profile.md or Contacts

- Single authenticated account - use it

- Ambiguous + multiple accounts - prompt once

## Cross-service handoff

When a request spans services (e.g. building a meeting prep doc), this skill's role ends after the calendar operation. The orchestration layer in workspace/SKILL.md handles chaining to Gmail, Docs, etc.

## Source

This skill wraps `workspace-mcp` tools for Calendar. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

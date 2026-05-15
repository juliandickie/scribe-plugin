---
description: Pull a specific or next calendar event, find related emails from attendees, build a structured prep doc in Drive. Invoke via /scribe:meeting-prep.
disable-model-invocation: true
argument-hint: [--event "title"] [--event-id ID] [--account email] [--folder ID]
last-validated: 2026-05-15
---

# Scribe - Meeting prep

Builds a structured prep doc for a meeting. Pulls the calendar event (next upcoming OR specified by title or ID), looks up related emails from each attendee across the user's accounts, and assembles a doc with Attendees, Context, Discussion topics, and Open questions sections.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--event "title"` OR `--event-id ID` - specifies the event. If neither, use the next upcoming event on the primary calendar.

- `--account email` (optional) - account that owns the event. Default - resolved per the standard rules.

- `--folder ID` (optional) - Drive folder for the prep doc. Default - a folder named "Meeting briefings" under the user's My Drive, created if absent.

## Tool call sequence

1. **Resolve event** - `get_events` with appropriate `time_min`/`time_max` to find next upcoming, OR `get_events` with `event_id=<id>` if `--event-id` provided, OR `get_events` with `query=<title>` if `--event "title"` provided.

2. **Extract attendees** - parse attendee emails from the event.

3. **Per attendee - find recent threads** - `search_gmail_messages` with `query="from:<attendee> OR to:<attendee>"`, capture top 5 by recency. Loop across accounts if multiple.

4. **Resolve target folder** - `search_drive_files` for "Meeting briefings", `create_drive_folder` if absent.

5. **Create prep doc** - `create_doc` titled `Meeting prep - <event title> - <date>`.

6. **Populate the doc** - `manage_doc_tab populate_from_markdown` with sections - Attendees (names + emails + brief context), Meeting context (event description, location, time), Recent communication (links to top emails per attendee), Agenda (placeholder), Open questions (placeholder).

7. **Return** - the doc URL plus a one-line summary of attendees and recent context found.

## Multi-account behaviour

Uses the account that owns the event by default. Cross-account email search per attendee uses all authenticated accounts (an attendee might appear in either inbox).

## Cross-plugin composition

- **ClickUp plugin** - if the event title or description mentions a ClickUp task or list, link it in the prep doc.

- **AC Builder plugin** - enrich attendee context with AC tags and recent automation history.

- **Slack plugin** - find prior Slack discussions about the meeting topic or attendees, link in the doc.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Prep for my next meeting"

- "Meeting prep for the Q3 planning event"

- "Build a briefing doc for tomorrow's call with Sarah"

Explicit args:

- `/scribe:meeting-prep --event-id ABC123 --folder DEF456`

## Failure modes

- **No upcoming events** - tell user and offer to search by title.

- **Multiple events match a title query** - prompt user to pick.

- **Attendees list empty** (solo event) - skip the attendee section, build the doc with just the event context.

## Output

Always return:

- The prep doc URL

- A one-line summary ("Meeting prep doc created for 'Q3 planning' with 4 attendees, 18 related emails surfaced")

- Cross-plugin steps skipped

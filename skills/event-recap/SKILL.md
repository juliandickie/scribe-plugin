---
description: Post-meeting recap - pull emails from attendees since the event, create a notes/action-items doc, draft a follow-up email. Invoke via /scribe:event-recap.
disable-model-invocation: true
argument-hint: [--event-id ID] [--account email] [--folder ID]
last-validated: 2026-05-15
---

# Scribe - Event recap

Post-meeting workflow. Pulls the most recent past calendar event (or specified by ID), gathers any emails from attendees since the event happened, creates a notes and action-items doc, and drafts a follow-up email to attendees.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--event-id ID` (optional) - default - most recent past event.

- `--account email` (optional) - account that owns the event.

- `--folder ID` (optional) - destination for the recap doc. Default - "Meeting recaps" folder under My Drive.

## Tool call sequence

1. **Resolve event** - most recent past event via `get_events` with `time_max=<now>` (sort desc, take first), OR by ID via `get_events` with `event_id=<id>`.

2. **Extract metadata** - attendees, original event description, location, time range.

3. **Per attendee - find post-event emails** - `search_gmail_messages` with `query="from:<attendee> newer_than:<event-time-iso>"` for follow-up communication.

4. **Resolve recap folder** - `search_drive_files` for "Meeting recaps", `create_drive_folder` if absent.

5. **Create recap doc** - `create_doc` titled `Recap - <event title> - <date>`.

6. **Populate doc** - sections - Event summary (title, time, attendees, original description), Attendees (with their post-event emails linked), Notes (placeholder), Action items (placeholder), Post-meeting emails (links).

7. **Draft follow-up** - `draft_gmail_message` to all attendees with the doc link and a brief summary.

8. **Return** - doc URL plus draft URL.

## Multi-account behaviour

Single account (the event owner's).

## Cross-plugin composition

- **ClickUp plugin** - for action items detected or added later in the notes section, offer to create ClickUp tasks (this is more of a "next step" suggestion than an automatic action).

- **Slack plugin** - post the recap doc link to a designated channel.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Recap my last meeting"

- "Build a recap doc from this morning's call"

Explicit args:

- `/scribe:event-recap --event-id ABC123`

- `/scribe:event-recap --folder DEF456`

## Failure modes

- **No recent past event** - prompt user to specify.

- **Multi-day or recurring event** - clarify which occurrence to recap.

- **No attendees** (solo blocked time) - skip the follow-up draft.

## Output

Always return:

- Recap doc URL

- Follow-up draft URL (if attendees present)

- One-line summary

- Cross-plugin steps skipped

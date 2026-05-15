# Scribe Services Reference

Detailed reference for the 10 service skills in Scribe v1.0. Each section enumerates the MCP tools available for that service, their parameter shapes, common patterns, and gotchas.

For shorter prose loaded into Claude at runtime, see the individual `skills/<service>/SKILL.md` files.


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

Returns: list of message metadata (id, thread_id, subject, snippet, from, date).

### get_gmail_message_content

Fetch full content of one message by ID.

Parameters:

- `message_id`

- `user_google_email`

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

Batch fetch multiple threads.

### search_gmail_threads

Thread-level search.

Parameters:

- `query` (Gmail query syntax)

- `user_google_email`

### get_gmail_attachment_content

Download attachment content.

Parameters:

- `message_id`

- `attachment_id`

- `user_google_email`

Returns: attachment bytes or saved-to-disk reference.

### send_gmail_message

Send a new message.

Parameters:

- `to`, `subject`, `body` (required)

- `cc`, `bcc` (optional)

- `user_google_email`

### draft_gmail_message

Create a draft. Same parameter shape as send.

### modify_gmail_message_labels

Apply or remove labels on a single message.

Parameters:

- `message_id`

- `add_labels[]`

- `remove_labels[]`

- `user_google_email`

### batch_modify_gmail_message_labels

Bulk label changes across many messages in one call.

### list_gmail_labels

List available labels (system + user).

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

---


# Scribe - Docs

Enables Claude to read, write, and structure Google Docs - including the tabbed document model and high-fidelity markdown-to-Docs writing.

## When to use

Use this skill when the user's request involves -

- Reading the content of a specific Google Doc (full or single tab)

- Pushing markdown content into a Doc or a specific tab

- Performing find-and-replace operations across a Doc

- Inspecting tab structure or managing tabs (create, rename, delete, populate)

- Updating headers, footers, or paragraph styles

## MCP tool reference

The following tools are exposed by workspace-mcp for Docs. Pass `user_google_email` on every call.

### get_doc_content

Read full doc text.

Parameters: `document_id`, `user_google_email`.

### get_doc_as_markdown

Read doc as markdown.

Parameters: `document_id`, `user_google_email`.

### inspect_doc_structure

Enumerate tabs, headings, structure.

Parameters: `document_id`, `user_google_email`. Returns: tab list with IDs and titles, heading hierarchy.

### manage_doc_tab

Create, rename, delete, or populate_from_markdown a tab.

Parameters:

- `action` - `"create"`, `"rename"`, `"delete"`, `"populate_from_markdown"`

- `document_id`

- `tab_id` - required for actions other than create

- `title` - for create/rename

- `markdown_text` - for populate_from_markdown

- `index` - tab position for create

- `replace_existing` (boolean) - for populate_from_markdown; true wipes the tab before writing

- `user_google_email`

### create_doc

Create a new doc.

Parameters: `title`, `parent_folder_id` (optional), `user_google_email`.

### import_to_google_doc

Convert and import a local file into a new Google Doc.

Parameters:

- `file_path` - sandbox-bound (see push/SKILL.md)

- `source_format` - `"md"`, `"txt"`, `"html"`, `"docx"`, `"odt"`, `"rtf"`

- `parent_folder_id` (optional)

- `user_google_email`

### batch_update_doc

Apply multiple operations in one atomic call.

Parameters: `document_id`, `requests[]`, `user_google_email`.

### find_and_replace_doc

Replace text occurrences.

Parameters: `document_id`, `find_text`, `replace_text`, `tab_id` (optional), `user_google_email`.

### modify_doc_text

Direct text modifications at specific positions.

### insert_doc_elements

Insert structural elements (headings, lists, etc.).

### insert_doc_image

Insert an image into the doc.

### create_table_with_data

Create a table populated from a 2D array.

### update_paragraph_style

Apply paragraph styling.

### update_doc_headers_footers

Manage headers and footers.

### manage_document_comment

Read or manage comments on a doc.

### list_document_comments

List comments on a doc.

### export_doc_to_pdf

Export to PDF.

### debug_docs_runtime_info / debug_table_structure

Diagnostics tools.

## Common patterns

### Update a specific tab from markdown

1. `inspect_doc_structure` to find tab_id by title.

2. `manage_doc_tab` with `action="populate_from_markdown"`, `replace_existing=true`.

### Create a new tab and populate it

1. `manage_doc_tab` with `action="create"`, `index`, `title` - response contains the new `tab_id`.

2. `manage_doc_tab` again with `action="populate_from_markdown"`, the new `tab_id`, and the markdown content.

### Bulk find/replace

- Use `find_and_replace_doc` once per term, OR `batch_update_doc` with multiple find/replace requests for atomic application.

## Gotchas

- Docs use a tab structure now. A doc without explicit tabs has a single default tab; tab_id is still needed for `manage_doc_tab` calls.

- `inspect_doc_structure` is the source of truth for tab IDs - don't guess.

- `import_to_google_doc` uses the sandbox at `~/.workspace-mcp/attachments`. Files outside fail. See push/SKILL.md for the auto-copy decision tree.

- `populate_from_markdown` with `replace_existing=true` wipes the tab before writing. With false it appends.

- `batch_update_doc` is atomic - if any operation fails, none are applied. Use for invariant-critical updates.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing."

## Cross-service handoff

When a request spans services (e.g. saving an email thread to a doc), this skill's role ends after the docs operation. The orchestration layer handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Docs. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Drive

Enables Claude to read, organise, share, and upload files in Google Drive - including folder structure management and permission controls.

## When to use

Use this skill when the user's request involves -

- Creating, copying, moving, or listing files and folders

- Uploading files from the local sandbox

- Sharing files with specific people or making them public

- Checking file permissions or public-access status

- Searching Drive by name, type, owner, or content

## MCP tool reference

The following tools are exposed by workspace-mcp for Drive. Pass `user_google_email` on every call.

### search_drive_files

Search by query.

Parameters:

- `query` - Drive query syntax like `name contains 'X' and mimeType = 'application/vnd.google-apps.folder'`

- `user_google_email`

### list_drive_items

List contents of a folder.

Parameters: `folder_id`, `user_google_email`, optional pagination.

### list_docs_in_folder

Convenience tool to list Docs in a folder.

### get_drive_file_content

Read file content for supported types.

### get_drive_file_download_url

Get a download URL for a file.

### read_file_content / download_file_content

Lower-level read operations.

### create_drive_folder

Create a folder.

Parameters:

- `name`

- `parent_folder_id`

- `user_google_email`

### create_drive_file

Create a Drive file from content.

### copy_drive_file

Copy a file.

Parameters: `file_id`, `destination_folder_id`, `new_name` (optional).

### update_drive_file

Update file metadata.

### manage_drive_access

Share with users or groups.

Parameters:

- `file_id`

- `email`

- `role` - `"reader"`, `"writer"`, `"commenter"`, or `"owner"`

- `send_notification` (optional boolean)

### set_drive_file_permissions

Set or modify permissions.

### get_drive_file_permissions / check_drive_file_public_access

Read permissions; check whether a file is publicly accessible.

### get_drive_shareable_link

Get a shareable URL for a file.

### get_file_metadata / get_file_permissions

Inspect metadata and permissions.

### search_files / list_recent_files

Variants of search and list.

## Common patterns

### Bootstrap a client folder

1. `create_drive_folder` for the parent.

2. 3-4 calls for subfolders (e.g. curriculum, planning, recordings).

### Find a folder by name

1. `search_drive_files` with `query="name = 'X' and mimeType = 'application/vnd.google-apps.folder'"`.

2. Take the first result.

### Share a doc for review

1. `manage_drive_access` with `email`, `role="commenter"`, `send_notification=true`.

### Audit a folder's external sharing

1. `list_drive_items` to enumerate the folder.

2. Per file, `get_drive_file_permissions`.

3. Surface any files shared externally (outside the user's primary domain).

## Gotchas

- Drive uses MIME types for file kinds. `application/vnd.google-apps.folder` is a folder; `application/vnd.google-apps.document` is a Google Doc; `application/vnd.google-apps.spreadsheet` is a Sheet; etc.

- Folder IDs and file IDs look identical from the URL. Both are random strings.

- Permission changes can take seconds to propagate; if a follow-up call fails, retry once.

- `search_drive_files` requires Drive query syntax (different from Gmail query). See https://developers.google.com/drive/api/guides/search-files.

- The Shared Drive distinction matters - files in Shared Drives have a `driveId` and different sharing semantics from My Drive files.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing."

## Cross-service handoff

When a request spans services (e.g. saving email attachments to Drive), this skill's role ends after the drive operation. The orchestration layer handles chaining to Gmail, Docs, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Drive. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Sheets

Enables Claude to read and write Google Sheets - ranges, individual cells, full sheets, formulas, and structured data tables.

## When to use

Use this skill when the user's request involves -

- Reading data from a specific Sheet or range

- Appending rows to a tracking sheet

- Updating cells with computed values or formulas

- Creating new sheets or duplicating templates

- Exporting structured data into a Sheet

## MCP tool reference

The exact tool names exposed for Sheets depend on the workspace-mcp version. At runtime, inspect the available MCP tools panel for the current set. The typical operations exposed are:

### read_range / get_sheet_values

Return cell values for an A1-notated range.

Parameters:

- `spreadsheet_id`

- `range` - A1 notation, e.g. `"Sheet1!A1:C10"`

- `user_google_email`

Returns: 2D array of cell values.

### write_range / update_sheet_values

Overwrite cell values for a range.

Parameters:

- `spreadsheet_id`

- `range`

- `values[][]` - 2D array

- `user_google_email`

### append_row / append_values

Add a new row at the bottom of the data region.

Parameters:

- `spreadsheet_id`

- `sheet_name` (or range with sheet specified)

- `values[]` - row contents

- `user_google_email`

### create_spreadsheet

Create a new spreadsheet (new file in Drive).

Parameters: `title`, `parent_folder_id` (optional), `user_google_email`.

### create_sheet / add_sheet

Add a new tab (sheet) to an existing spreadsheet.

### clear_range

Empty cells without deleting the structure.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel and update this section.** The patterns below describe the conceptual operations regardless of exact tool names.

## Common patterns

### Log a support inquiry

1. Read header row to confirm column layout (e.g. `range="Tracker!A1:F1"`).

2. Append row with `[timestamp, sender, subject, link_to_thread, classification, status]`.

### Read a config sheet

1. Read named range like `Config!A1:B20`.

2. Parse rows into key-value pairs.

### Bulk update

- Prefer batched range writes over per-cell calls for performance. One write to a 10x10 range is much faster than 100 individual cell writes.

## Gotchas

- Sheets use A1 notation (`Sheet1!A1:B10`) - not R1C1. Always include the sheet name when working with a multi-sheet spreadsheet.

- Empty cells return as missing values, not empty strings. Be defensive when parsing rows - check for `None` or undefined.

- Sheet IDs (`gid` in URLs) are different from spreadsheet IDs. The spreadsheet ID is the long random string in the URL; the sheet ID is the small numeric `gid` parameter.

- Append-row finds the first empty row in a sheet, not necessarily after the last data row. If a sheet has gaps, append may slot into a gap. For strict append-at-end behaviour, read the last-row index first and write to that row + 1.

- Date and time values are returned as serial numbers unless the column is formatted as date. Format the column or convert in-prose.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing."

## Cross-service handoff

When a request spans services (e.g. logging an email to a sheet), this skill's role ends after the sheet operation. The orchestration layer handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Sheets. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Slides

Enables Claude to read, create, and update Google Slides presentations - slide content, layout, and text.

## When to use

Use this skill when the user's request involves -

- Reading the content of an existing deck

- Creating new presentations from a structure or outline

- Adding or updating slides within a deck

- Modifying text on specific slides

## MCP tool reference

The exact tool names exposed for Slides depend on the workspace-mcp version. At runtime, inspect the available MCP tools panel for the current set. Typical operations:

### read_presentation / get_presentation

Returns all slide contents.

Parameters: `presentation_id`, `user_google_email`.

### create_presentation

Create a new presentation in Drive.

Parameters: `title`, `parent_folder_id` (optional), `user_google_email`.

### add_slide

Add a slide to an existing presentation.

Parameters: `presentation_id`, `layout` (e.g. `"TITLE"`, `"TITLE_AND_BODY"`), `index` (optional position), `user_google_email`.

### update_slide_content

Modify text or elements on a specific slide.

Parameters: `presentation_id`, `slide_id`, content updates, `user_google_email`.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel and update this section.**

## Common patterns

### Generate a deck from an outline

1. `create_presentation` with the deck title.

2. Per outline section, `add_slide` with the appropriate layout.

3. `update_slide_content` to set title and body text per slide.

### Read existing deck and summarise

1. `read_presentation` to fetch all slides.

2. Surface slide titles and key text content as a structured summary.

## Gotchas

- Slides has rich layout primitives (text boxes, shapes, images). Don't assume a slide is just a title and bullets.

- Layouts are template-driven. Changing a slide's layout often requires understanding the master slide structure.

- Slide IDs are different from page numbers. Always work with IDs returned from `read_presentation` or `add_slide`.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` for account selection rules.

## Cross-service handoff

When generating a deck from a Doc or other source, this skill handles the slide creation. The orchestration layer handles chaining to other services.

## Source

This skill wraps `workspace-mcp` tools for Google Slides. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Contacts

Enables Claude to read and create Google Contacts via the People API - useful for resolving names to emails, enriching contact info, and creating new contact entries.

## When to use

Use this skill when the user's request involves -

- Looking up a contact by name to find their email

- Looking up by email to find their name and other metadata

- Creating a new contact

- Listing contacts in a specific group

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### read_contact / get_contact

Look up a contact by ID or email.

Parameters: `contact_id` or `email`, `user_google_email`.

Returns: contact metadata (name, email(s), phone, organisation, notes).

### search_contacts

Search by name or query.

Parameters: `query`, `user_google_email`.

### list_contacts

List contacts.

Parameters: `user_google_email`, optional pagination.

### create_contact

Create a new contact entry.

Parameters: `name`, `email`, optional fields (phone, organisation, notes), `user_google_email`.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Resolve a name to an email

1. `search_contacts` with the name as query.

2. Return the matching email(s). If multiple matches, prompt user to disambiguate.

### Enrich an email

1. Given an email, `read_contact` (or search by email).

2. Surface name, organisation, phone if present.

## Gotchas

- The People API distinguishes between contacts (people you've explicitly added) and "other contacts" (people you've emailed but not added). Both may be searchable.

- Workspace org contacts (directory) are separate from personal contacts. The API exposes both differently - some tools return one, some both.

- Display names can differ from primary email's display field. Treat name and email as separate identity facets.

## Account selection

Pass `user_google_email` on every call. Note that contacts are per-account - a contact in julian@idd is not visible to julian@pro. If looking up across accounts, loop over accounts.

## Cross-service handoff

When resolving a contact for a downstream operation (drafting email, looking up calendar history), this skill ends after returning the contact metadata. The orchestration layer chains to Gmail, Calendar, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Contacts (People API). Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Tasks

Enables Claude to read, create, and complete items in Google Tasks - the lightweight to-do system separate from external PM tools.

## When to use

Use this skill when the user's request involves -

- Reading what's on the user's Google Tasks lists

- Creating new tasks from email or doc content

- Marking tasks complete

- Managing or listing task lists

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### list_task_lists

Enumerate the user's task lists.

Parameters: `user_google_email`.

### read_tasks_in_list / get_tasks

Read tasks in a specific list.

Parameters: `task_list_id`, optional filters (`completed`, `due_before`), `user_google_email`.

### create_task

Create a new task.

Parameters:

- `task_list_id`

- `title`

- `notes` (optional)

- `due` (optional, RFC 3339)

- `user_google_email`

### update_task

Update task fields - mark complete, change due date, edit title.

Parameters: `task_list_id`, `task_id`, fields to update, `user_google_email`.

### delete_task

Delete a task.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Convert action items from a doc to tasks

1. Read the doc content (use the docs skill).

2. Parse action items.

3. `create_task` per item against the user's default task list.

### Daily task surfacing

1. `list_task_lists` to find the default list.

2. `read_tasks_in_list` filtered by `completed=false` and `due_before=tomorrow`.

3. Surface incomplete items due today or overdue.

## Gotchas

- Google Tasks is the simple to-do system inside Gmail/Calendar UI. Not to be confused with Google Workspace Admin API "tasks" (different surface used in admin contexts).

- If the user uses ClickUp (or another PM system) as primary, defer task creation to that plugin per the cross-plugin composition pattern in workspace/SKILL.md. Don't double-write tasks across systems.

- Task lists are per-account.

- Subtasks exist but require working with parent_task_id; check the API surface if subtasks matter.

## Account selection

Pass `user_google_email` on every call. Tasks are per-account.

## Cross-service handoff

When converting from a Doc to tasks, this skill handles the task creation. The orchestration layer handles the doc reading.

## Source

This skill wraps `workspace-mcp` tools for Google Tasks. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Forms

Enables Claude to read responses from existing Google Forms and create new forms programmatically.

## When to use

Use this skill when the user's request involves -

- Reading responses to a specific form

- Creating a new form with questions

- Aggregating or summarising survey results

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### read_form / get_form

Read form structure (questions, layout).

Parameters: `form_id`, `user_google_email`.

### read_form_responses / get_form_responses

Fetch responses for a form.

Parameters: `form_id`, optional pagination, `user_google_email`.

Returns: list of response entries with per-question values.

### create_form

Create a new form.

Parameters: `title`, `description`, `questions[]`, `user_google_email`.

### update_form

Modify an existing form's questions or settings.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Summarise survey responses

1. `read_form_responses` to fetch all responses.

2. Group by question, return distribution and free-text excerpts.

### Create a form from a spec

1. Given a list of questions, `create_form`.

2. Use the drive skill to share the resulting form for collection.

## Gotchas

- Form response data structure varies by question type. Multi-select returns arrays; grid questions return nested structures. Be defensive when parsing.

- New forms default to private. Sharing requires Drive API calls (use the drive skill alongside).

- Edit URL and respond URL are different - know which one the user needs.

## Account selection

Pass `user_google_email` on every call. Forms are per-account in the owner sense, though responses can come from anyone with the form URL.

## Cross-service handoff

When creating a form, sharing it is a Drive operation. When analysing responses, summarising into a doc or sheet is a separate service. The orchestration layer chains these.

## Source

This skill wraps `workspace-mcp` tools for Google Forms. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Chat

Enables Claude to send and read messages in Google Chat spaces.

## When to use

Use this skill when the user's request involves -

- Sending a message to a Google Chat space

- Reading recent messages in a space

- Posting a workflow summary to a Chat channel

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### send_chat_message

Send a message to a space.

Parameters:

- `space_id` - format `spaces/ABCDEF`

- `text` (or rich content)

- `thread_key` (optional, to reply in thread)

- `user_google_email`

### read_chat_messages

Get messages from a space.

Parameters: `space_id`, `time_min`/`time_max` (optional), `user_google_email`.

### list_chat_spaces

List spaces the user is in.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Post a workflow summary

1. After a workflow completes, `send_chat_message` to a designated space with a one-line summary and any artifact URLs.

### Read recent activity

1. `read_chat_messages` for a space over a time window.

2. Surface as structured summary with sender, timestamp, content excerpt.

## Gotchas

- Google Chat is the Workspace messaging product. Distinct from Slack and Microsoft Teams. If the user's team uses Slack primarily, use the Slack plugin instead per the cross-plugin composition pattern.

- Chat space IDs are different from regular email addresses. They look like `spaces/ABCDEF`.

- Bot/app messages may be subject to additional permissions in some Workspace orgs.

## Account selection

Pass `user_google_email` on every call. The account must be a member of the target space.

## Cross-service handoff

When posting a workflow result to Chat, this skill handles the message send. The orchestration layer composed the message content from other services.

## Source

This skill wraps `workspace-mcp` tools for Google Chat. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---

## Cross-service patterns

These patterns chain multiple services. They mirror the orchestration logic in `skills/workspace/SKILL.md`.

### Email to Doc

Gmail (`get_gmail_thread_content`) → optional Gmail (`get_gmail_attachment_content`) → optional Drive (`create_drive_file`) → Docs (`create_doc` + `manage_doc_tab populate_from_markdown`).

### Calendar to prep Doc

Calendar (`get_events`) → Gmail (`search_gmail_messages` per attendee) → Docs (`create_doc`).

### Sheet logging

Sheets (read header row to confirm structure) → Sheets (append row).

### Drive activity scan

Drive (`list_drive_items` + `get_drive_file_permissions`) → Docs (`list_document_comments`).

For full multi-service workflows, see `docs/workflows.md`.

## Authoring new service skills

Add a new service skill in v1.1+ by copying `docs/skill-templates/service-skill-template.md` to `skills/<service>/SKILL.md`, filling in the placeholders with the service-specific MCP tools, and adding the slug to the validation loop in `Makefile`.

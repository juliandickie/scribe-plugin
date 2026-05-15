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

Batch fetch multiple threads by IDs.

Note: there is no dedicated thread-level search tool. To find threads, use `search_gmail_messages` (results include `thread_id`) and then call `get_gmail_thread_content` or `get_gmail_threads_content_batch` to fetch the full thread content for the IDs you care about.

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

- `action` - `"create"`, `"update"`, `"delete"`, or `"rsvp"`

- `event_id` - required for update, delete, and rsvp

- Event fields: `summary`, `start_time`, `end_time`, `attendees`, `description`, `location`, `timezone`, etc.

- `response` - for `rsvp` action only: `"accepted"`, `"declined"`, `"tentative"`, `"needsAction"`

- `send_updates` - `"all"` (default), `"externalOnly"`, or `"none"` to control notification emails

- `calendar_id` (defaults to `"primary"`)

- `user_google_email`

Note: `manage_event` does NOT support a `"read"` action. To read a specific event by ID, use `get_events` with `event_id=<id>` instead.

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

1. Enumerate authenticated accounts by scanning `~/.workspace-mcp/credentials/*.json` filenames (see workspace/SKILL.md "Enumerating authenticated accounts").

2. Per account, `get_events` for the day.

3. Merge results sorted by start time.

## Gotchas

- All event times use RFC 3339 with timezone (e.g. `2026-05-15T09:00:00+10:00` for Brisbane). The server does NOT auto-handle naive datetimes - always pass timezone.

- `calendar_id="primary"` is the user's main calendar. Other calendars need their full ID; get them via `list_calendars`.

- Recurring events return one entry per occurrence within the time range, not one master entry.

- `query_freebusy` returns busy intervals, not free intervals. Compute free = window minus busy.

- Attendees added in `manage_event` get an automatic invite email by default. To control this, pass `send_updates` - `"all"` (default), `"externalOnly"` (only external attendees notified), or `"none"` (no emails sent). Useful when batch-creating internal-only events or syncing existing schedules.

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

### import_to_google_doc

Convert and import a local file as a new Google Doc.

Parameters: `file_path` (sandbox-bound to `~/.workspace-mcp/attachments`), `source_format`, `parent_folder_id` (optional), `user_google_email`. See `skills/push/SKILL.md` for the sandbox auto-copy decision tree.

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

Enables Claude to read and write Google Sheets - ranges, individual cells, full sheets, formulas, structured data tables, and formatting.

## When to use

Use this skill when the user's request involves -

- Reading data from a specific Sheet or range

- Appending rows to a tracking sheet (using a structured table)

- Updating cells with computed values or formulas

- Creating new spreadsheets or sheets (tabs)

- Formatting cells, ranges, or applying conditional formatting

- Listing spreadsheets, sheets, or tables

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Sheets. Pass `user_google_email` on every call.

### list_spreadsheets

List spreadsheets visible to the user (paginates Drive for Sheet-type files).

### get_spreadsheet_info

Get metadata for a spreadsheet (title, sheets list with IDs, named ranges).

Parameters: `spreadsheet_id`, `user_google_email`.

### read_sheet_values

Read cell values for an A1-notated range.

Parameters: `spreadsheet_id`, `range` (e.g. `"Sheet1!A1:C10"`), `user_google_email`.

Returns: 2D array of cell values.

### modify_sheet_values

Write cell values for a range. Supports overwrite and append modes.

Parameters: `spreadsheet_id`, `range`, `values` (2D array), `user_google_email`, and a mode/option to control overwrite vs. append.

### format_sheet_range

Apply formatting (font, color, borders, number formats) to a range.

### manage_conditional_formatting

Add, update, or remove conditional formatting rules.

### create_spreadsheet

Create a new spreadsheet (new file in Drive).

Parameters: `title`, optional `parent_folder_id`, `user_google_email`.

### create_sheet

Add a new sheet (tab) to an existing spreadsheet.

Parameters: `spreadsheet_id`, `title`, `user_google_email`.

### list_sheet_tables

List structured tables defined within a spreadsheet (named tables, not raw data regions).

### append_table_rows

Append one or more rows to a structured table. This is the canonical pattern for tracking sheets where you want strict append semantics.

Parameters: `spreadsheet_id`, `table_name` (or table reference), `rows[][]`, `user_google_email`.

### resize_sheet_dimensions

Resize rows or columns (e.g. set column widths).

### move_sheet_rows

Move rows within a sheet.

## Common patterns

### Log a support inquiry into a tracking table

1. `list_sheet_tables` (or `get_spreadsheet_info`) to confirm the target table exists.

2. `append_table_rows` with `[timestamp, sender, subject, link_to_thread, classification, status]`.

If the target sheet is not a structured table, use `modify_sheet_values` instead to write the row at the next empty row found via `read_sheet_values` on the relevant column.

### Read a config sheet

1. `read_sheet_values` with `range="Config!A1:B20"`.

2. Parse rows into key-value pairs in prose.

### Bulk update

- Prefer batched range writes via `modify_sheet_values` over per-cell calls. One write to a 10x10 range is much faster than 100 individual cell writes.

## Gotchas

- Sheets use A1 notation (`Sheet1!A1:B10`) - not R1C1. Always include the sheet name when working with a multi-sheet spreadsheet.

- Empty cells return as missing values, not empty strings. Be defensive when parsing rows - check for `None` or undefined.

- Sheet IDs (`gid` in URLs) are different from spreadsheet IDs. The spreadsheet ID is the long random string in the URL; the sheet ID is the small numeric `gid` parameter.

- `append_table_rows` requires a structured table. If the sheet is just raw data without a defined table, use `modify_sheet_values` and compute the target row manually. The structured-table path is more robust for tracking sheets created specifically for logging.

- Date and time values are returned as serial numbers unless the column is formatted as date. Format via `format_sheet_range` or convert in prose.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` "Multi-account routing" for the selection rules.

## Cross-service handoff

When a request spans services (e.g. logging an email to a sheet), this skill's role ends after the sheet operation. The orchestration layer in workspace/SKILL.md handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Sheets. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Slides

Enables Claude to read, create, and update Google Slides presentations. All structural updates flow through `batch_update_presentation` with a list of requests (mirroring the Google Slides API's batchUpdate pattern).

## When to use

Use this skill when the user's request involves -

- Reading the content of an existing deck

- Creating new presentations from a structure or outline

- Adding or updating slides within a deck

- Modifying text on specific slides

- Getting thumbnails of specific slides

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Slides. Pass `user_google_email` on every call.

### create_presentation

Create a new presentation (new file in Drive).

Parameters: `title`, optional `parent_folder_id`, `user_google_email`.

### get_presentation

Read a presentation's full structure - all pages (slides), all elements, layouts.

Parameters: `presentation_id`, `user_google_email`.

### batch_update_presentation

The workhorse mutation tool. Accepts a list of update requests. All slide creation, deletion, text edits, image inserts, layout changes go through this.

Parameters:

- `presentation_id`

- `requests[]` - list of update request objects. Each follows the Google Slides API batchUpdate shape (e.g. `{"createSlide": {...}}`, `{"insertText": {...}}`, `{"deleteObject": {...}}`).

- `user_google_email`

### get_page

Read a single slide (page) by ID.

### get_page_thumbnail

Get a thumbnail image of a specific slide.

## Common patterns

### Generate a deck from an outline

1. `create_presentation` with the deck title - returns the new presentation ID and the default first slide ID.

2. `batch_update_presentation` with a request list that adds one slide per outline section. For each new slide, also include `insertText` requests to populate title and body placeholders. Batch them in one call where possible - it's atomic and faster.

### Read existing deck and summarise

1. `get_presentation` to fetch all slides.

2. Walk the pages array; for each page surface its title and key text content as a structured summary.

### Add a slide at a specific position

1. `batch_update_presentation` with a `createSlide` request including `insertionIndex` and `slideLayoutReference`.

### Replace text on a specific slide

1. `batch_update_presentation` with a `replaceAllText` request scoped to the specific page object ID, or with `deleteText` + `insertText` requests targeting a specific element.

## Gotchas

- All structural changes flow through `batch_update_presentation`. There is NO separate `add_slide` or `update_slide_content` tool - those operations are individual request objects within a batchUpdate call.

- Layouts are template-driven. Use `slideLayoutReference` with predefined layout IDs (e.g. `TITLE_AND_BODY`, `TITLE`, `SECTION_HEADER`) when creating slides. Custom layouts have their own IDs visible in `get_presentation` output.

- `batch_update_presentation` is atomic - if any request in the list fails, none are applied. Group operations that should succeed-or-fail together.

- Slide IDs are different from indexes. The first slide is at index 0 but its object ID is a random string (or "p" prefix for default). Always use IDs from `get_presentation` rather than guessing.

- Placeholders (title, body, etc.) have their own object IDs distinct from the slide's ID. To insert text into a title placeholder, target the placeholder's object ID, not the slide ID.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` for account selection rules.

## Cross-service handoff

When generating a deck from a Doc or other source, this skill handles the slide creation. The orchestration layer handles chaining to other services (e.g. reading the source Doc first).

## Source

This skill wraps `workspace-mcp` tools for Google Slides. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Contacts

Enables Claude to read, create, search, and manage Google Contacts via the People API - useful for resolving names to emails, enriching contact info, creating new contact entries, and grouping contacts.

## When to use

Use this skill when the user's request involves -

- Looking up a contact by name to find their email

- Looking up by email to find their name and other metadata

- Creating, updating, or deleting a contact entry

- Listing contacts in a specific contact group

- Bulk-managing many contacts at once

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Contacts. Pass `user_google_email` on every call. Mutations (create/update/delete) flow through `manage_contact` or `manage_contacts_batch` with action verbs.

### list_contacts

List the user's contacts.

Parameters: `user_google_email`, optional pagination, optional field mask.

### get_contact

Read a specific contact by resource name (returned from search/list as something like `people/c12345`).

Parameters: `resource_name`, `user_google_email`, optional field mask.

### search_contacts

Search contacts by name, email, or other fields.

Parameters: `query`, `user_google_email`.

Returns: list of matching contacts with resource names.

### manage_contact

Create, update, or delete a single contact - action-based interface.

Parameters:

- `action` - `"create"`, `"update"`, or `"delete"`

- `resource_name` - required for update/delete

- Contact fields - `names`, `email_addresses`, `phone_numbers`, `organizations`, `biographies`, etc. (passed as structured data for create/update)

- `user_google_email`

### list_contact_groups

List contact groups (labels/categories).

### get_contact_group

Read a single contact group, including member contacts.

### manage_contact_group

Create, update, or delete a contact group.

Parameters: `action`, group fields, `user_google_email`.

### manage_contacts_batch

Apply create/update/delete to many contacts in a single batched call.

Parameters: `action`, list of contact payloads (each with its own fields and, for update/delete, resource_name), `user_google_email`.

## Common patterns

### Resolve a name to an email

1. `search_contacts` with the name as query.

2. Inspect the results' `email_addresses` field. If multiple matches, prompt user to disambiguate.

### Enrich an email

1. `search_contacts` with the email as query (works because the API matches across fields).

2. From the matching contact, surface name, organisation, phone numbers if present.

### Create a new contact

1. `manage_contact` with `action="create"`, populated `names`, `email_addresses`, and any other fields the user provided.

2. The response includes the new contact's `resource_name`.

### Add a contact to a group

1. `manage_contact_group` (or specific membership operations exposed by upstream) - check `get_contact_group` for membership semantics in the current API surface.

## Gotchas

- The People API uses **resource names** like `people/c12345` for contact identifiers, not raw IDs. Always pass the full resource_name returned by list/search/get.

- The People API distinguishes between contacts (people you've explicitly added) and "other contacts" (people you've emailed but not added). `search_contacts` searches your saved contacts by default; "other contacts" may need a different field mask or call.

- Workspace org contacts (directory) are separate from personal contacts. Within an org, the directory is searchable via the same People API but the result set may differ depending on org settings.

- All mutations route through `manage_contact` (or `manage_contacts_batch` for bulk). There is no separate `create_contact` or `delete_contact` tool.

## Account selection

Pass `user_google_email` on every call. Contacts are per-account - a contact saved under julian@idd is not visible to julian@pro. For cross-account lookups, loop over accounts using the credentials directory scan.

## Cross-service handoff

When resolving a contact for a downstream operation (drafting email, looking up calendar history), this skill ends after returning the contact metadata. The orchestration layer chains to Gmail, Calendar, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Contacts (People API). Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Tasks

Enables Claude to read, create, and complete items in Google Tasks - the lightweight to-do system separate from external PM tools. All mutations flow through `manage_task` and `manage_task_list` with action verbs.

## When to use

Use this skill when the user's request involves -

- Reading what's on the user's Google Tasks lists

- Creating new tasks from email or doc content

- Marking tasks complete, updating, or deleting them

- Listing or managing task lists

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Tasks. Pass `user_google_email` on every call.

### list_task_lists

Enumerate the user's task lists. Returns each list's ID and title.

Parameters: `user_google_email`.

### get_task_list

Read metadata for a specific task list.

Parameters: `task_list_id`, `user_google_email`.

### manage_task_list

Create, update, or delete a task list.

Parameters:

- `action` - `"create"`, `"update"`, or `"delete"`

- `task_list_id` - required for update/delete

- `title` - required for create/update

- `user_google_email`

### list_tasks

Read tasks within a list, with filters.

Parameters:

- `task_list_id`

- `show_completed` (optional bool)

- `show_hidden` (optional bool)

- `due_min`, `due_max` (optional, RFC 3339)

- `updated_min` (optional)

- `user_google_email`

### get_task

Read a single task by ID.

Parameters: `task_list_id`, `task_id`, `user_google_email`.

### manage_task

Create, update, or delete a task - action-based interface.

Parameters:

- `action` - `"create"`, `"update"`, or `"delete"`

- `task_list_id`

- `task_id` - required for update/delete

- `title` - required for create

- `notes` (optional)

- `due` (optional, RFC 3339)

- `status` - `"needsAction"` or `"completed"` (use this to mark complete via update)

- `user_google_email`

## Common patterns

### Convert action items from a doc to tasks

1. Read the doc content (use the docs skill).

2. Parse action items from the text.

3. `list_task_lists` to find the target list. If none specified, use the user's default (first list).

4. `manage_task` with `action="create"` per item.

### Daily task surfacing

1. `list_task_lists` to find the default list.

2. `list_tasks` with `show_completed=false`, `due_max=<end of today>`.

3. Surface incomplete items due today or overdue.

### Mark a task complete

1. `manage_task` with `action="update"`, `task_id`, `status="completed"`.

## Gotchas

- Google Tasks is the simple to-do system inside Gmail/Calendar UI. Not to be confused with Google Workspace Admin API "tasks" (different surface used in admin contexts).

- All CRUD operations on tasks flow through `manage_task`. There is no separate `create_task`, `update_task`, or `delete_task` tool - the action verb selects the operation.

- Task lists are per-account.

- To mark a task complete, call `manage_task` with `action="update"` and `status="completed"`. There is no dedicated "complete" action.

- If the user uses ClickUp (or another PM system) as primary, defer task creation to that plugin per the cross-plugin composition pattern in workspace/SKILL.md. Don't double-write tasks across systems.

## Account selection

Pass `user_google_email` on every call. Tasks are per-account.

## Cross-service handoff

When converting from a Doc to tasks, this skill handles the task creation. The orchestration layer handles the doc reading.

## Source

This skill wraps `workspace-mcp` tools for Google Tasks. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Forms

Enables Claude to read responses from existing Google Forms, create new forms, and modify form structure. All form mutations flow through `batch_update_form`.

## When to use

Use this skill when the user's request involves -

- Reading responses to a specific form (single response or paginated list)

- Creating a new form

- Modifying form questions, sections, or settings

- Publishing or unpublishing a form

- Aggregating or summarising survey results

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Forms. Pass `user_google_email` on every call.

### create_form

Create a new form.

Parameters:

- `title`

- `description` (optional)

- `document_title` (optional)

- `user_google_email`

Returns: the new form's ID and edit URL. The created form starts empty; use `batch_update_form` to add questions.

### get_form

Read a form's metadata and full question structure.

Parameters: `form_id`, `user_google_email`.

### set_publish_settings

Publish or unpublish a form, control who can respond.

Parameters: `form_id`, settings fields, `user_google_email`.

### get_form_response

Read a single response by response ID.

Parameters: `form_id`, `response_id`, `user_google_email`.

### list_form_responses

List responses for a form, with pagination.

Parameters: `form_id`, optional pagination cursor, `user_google_email`.

### batch_update_form

The workhorse mutation tool. Accepts a list of update requests (mirroring the Google Forms API's batchUpdate). All question additions, edits, deletions, and section changes flow through this.

Parameters:

- `form_id`

- `requests[]` - list of update request objects (e.g. `{"createItem": {...}}`, `{"updateItem": {...}}`, `{"deleteItem": {...}}`)

- `user_google_email`

## Common patterns

### Create a form from a spec

1. `create_form` with the title and optional description.

2. `batch_update_form` with `createItem` requests for each question, ordered.

3. (Optional) `set_publish_settings` to publish or share.

4. (Optional) Use the drive skill to share the form file for collection.

### Summarise survey responses

1. `list_form_responses` (paginate as needed) to fetch all responses.

2. Optionally `get_form` to map question IDs to question text.

3. Group answers by question, return distribution and free-text excerpts.

### Add a question to an existing form

1. `get_form` to inspect current structure and pick an insertion index.

2. `batch_update_form` with a `createItem` request including the index.

## Gotchas

- Form response data structure varies by question type. Multi-select returns arrays; grid questions return nested structures. Inspect the question type from `get_form` before parsing responses.

- All form mutations flow through `batch_update_form`. There is no separate `update_form` tool - you build a list of typed request objects.

- `batch_update_form` is atomic - if any request fails, none are applied. Group operations that should succeed-or-fail together.

- New forms default to private. Sharing requires Drive API calls (use the drive skill alongside) OR `set_publish_settings`.

- Edit URL and respond URL are different - the edit URL is returned by `create_form`; the respond URL comes from form metadata after publishing.

## Account selection

Pass `user_google_email` on every call. Forms are per-account in the owner sense, though responses can come from anyone with the respond URL.

## Cross-service handoff

When creating a form, sharing it is a Drive operation. When analysing responses, summarising into a doc or sheet is a separate service. The orchestration layer chains these.

## Source

This skill wraps `workspace-mcp` tools for Google Forms. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

---


# Scribe - Chat

Enables Claude to send, read, and search messages in Google Chat spaces, plus manage reactions and attachments.

## When to use

Use this skill when the user's request involves -

- Sending a message to a Google Chat space

- Reading recent messages in a space

- Searching for messages by keyword across spaces

- Posting a workflow summary to a Chat channel

- Adding a reaction to a message

- Downloading a Chat attachment

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Google Chat. Pass `user_google_email` on every call.

### list_spaces

List Chat spaces the user is a member of.

Parameters: `user_google_email`, optional pagination.

### get_messages

Get messages from a space.

Parameters:

- `space_id` - format `spaces/ABCDEF`

- Optional time/cursor filters

- `user_google_email`

### send_message

Send a message to a space.

Parameters:

- `space_id`

- `text` (or rich content)

- `thread_key` (optional, to reply in a thread)

- `user_google_email`

### search_messages

Search messages by keyword across spaces the user has access to.

Parameters: `query`, optional space filter, `user_google_email`.

### create_reaction

Add an emoji reaction to a specific message.

Parameters: `message_name`, `emoji`, `user_google_email`.

### download_chat_attachment

Download an attachment from a Chat message.

Parameters: attachment reference, `user_google_email`.

## Common patterns

### Post a workflow summary to a space

1. After a workflow completes, `send_message` to a designated space with a one-line summary and any artifact URLs.

### Read recent activity

1. `get_messages` for a space over a time window.

2. Surface as structured summary with sender, timestamp, content excerpt.

### Find a discussion by topic

1. `search_messages` with the topic as query.

2. For relevant hits, `get_messages` to read the surrounding context.

### Acknowledge a workflow result

1. After `send_message` posts a summary, `create_reaction` to add a thumbs-up so participants know action was taken.

## Gotchas

- Google Chat is the Workspace messaging product. Distinct from Slack and Microsoft Teams. If the user's team uses Slack primarily, use the Slack plugin instead per the cross-plugin composition pattern.

- Chat space IDs use the `spaces/ABCDEF` format. They are not regular email addresses or random short IDs.

- Tool names do NOT have a `chat_` prefix - just `list_spaces`, `get_messages`, `send_message`, etc. Don't try `send_chat_message` - it doesn't exist.

- Bot/app messages may be subject to additional permissions in some Workspace orgs. If `send_message` fails with a permission error, the user's org may restrict app-posted messages.

- `search_messages` searches across spaces the user has access to. If results are empty, confirm the space is one the authenticated account is a member of.

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

Sheets (`get_spreadsheet_info` or `list_sheet_tables` to confirm structure) → Sheets (`append_table_rows` for structured tables, or `modify_sheet_values` for raw ranges).

### Drive activity scan

Drive (`list_drive_items` + `get_drive_file_permissions`) → Docs (`list_document_comments`).

For full multi-service workflows, see `docs/workflows.md`.

## Authoring new service skills

Add a new service skill in v1.1+ by copying `docs/skill-templates/service-skill-template.md` to `skills/<service>/SKILL.md`, filling in the placeholders with the service-specific MCP tools, and adding the slug to the validation loop in `Makefile`.

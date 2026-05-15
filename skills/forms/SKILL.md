---
description: Use when the user's request involves Google Forms - reading form responses, creating new forms, modifying form structure, analysing survey results. Triggers on form, survey, response, questionnaire, form responses.
last-validated: 2026-05-15
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

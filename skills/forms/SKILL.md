---
description: Use when the user's request involves Google Forms - reading form responses, creating new forms, analysing survey results. Triggers on form, survey, response, questionnaire, form responses.
last-validated: 2026-05-15
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

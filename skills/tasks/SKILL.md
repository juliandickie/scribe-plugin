---
description: Use when the user's request involves Google Tasks - reading or creating to-do items, managing checklists, marking tasks complete, working with task lists. Triggers on task, to-do, checklist, action item, google tasks. Does NOT trigger on ClickUp or other PM-system tasks - those go to their respective plugins.
last-validated: 2026-05-15
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

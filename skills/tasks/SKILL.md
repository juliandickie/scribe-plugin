---
description: Use when the user's request involves Google Tasks - reading or creating to-do items, managing checklists, marking tasks complete, working with task lists. Triggers on task, to-do, checklist, action item, google tasks. Does NOT trigger on ClickUp or other PM-system tasks - those go to their respective plugins.
last-validated: 2026-05-15
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

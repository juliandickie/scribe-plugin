---
description: Use when the user's request involves Google Drive - folders, files, file uploads, file sharing, permissions, public access checks, or any Drive content operation. Triggers on Drive, folder, file, upload, share, permissions, Drive URL, file ID.
last-validated: 2026-05-15
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

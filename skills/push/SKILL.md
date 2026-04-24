---
description: Push a local markdown file to Google Drive as a new or updated Google Doc. Use when the user asks to push markdown to Drive, update a Doc tab with markdown content, or sync a markdown file to a specific Google Doc.
---

# Scribe - Push

Push a markdown file to Google Drive via the workspace-mcp server.

User input arrives in $ARGUMENTS as free-form text. Parse it for -

- **File path** (positional, required) - the local markdown file to push

- **`--folder <id>`** (optional) - Drive folder ID where a new Doc should be created

- **`--doc-id <id>`** (optional) - existing Google Doc ID to update instead of creating new

- **`--tab-id <id>`** (optional, requires --doc-id) - specific tab within the doc to write into

- **`--account <email>`** (optional) - Google account to use (overrides default)

Routing logic -

- If `--tab-id` is present - call `update_tab_from_markdown` with `document_id`, `tab_id`, the file content, and `replace_existing=true`

- If `--doc-id` is present but no `--tab-id` - fetch the doc's primary tab and update that via `update_tab_from_markdown`

- If neither `--doc-id` nor `--tab-id` - create a new Google Doc via `drive_upload_file` + convert to Doc in the specified `--folder`

Always pass `user_google_email` (either the --account override or the resolved default for the current context - check the nearest clients/{CLIENT-ID}/profile.md if working in an AHPRA-style repo).

After the operation completes, surface the resulting Google Doc URL and the tab name or doc title that was affected.

If the user has not authenticated yet ("No cached token" error), direct them to run /scribe:auth-init.

---
description: Push a local markdown file to Google Drive as a new or updated Google Doc.
argument-hint: <file> [--folder <id>] [--doc-id <id>] [--tab-id <id>] [--account <email>]
---

Push the markdown file named in `$ARGUMENTS` to Google Drive.

Parse `$ARGUMENTS` for the following optional flags -

- `--folder <id>` - Drive folder ID to put the Doc in

- `--doc-id <id>` - Existing Google Doc ID to update (instead of creating new)

- `--tab-id <id>` - Specific tab to write into (requires `--doc-id`)

- `--account <email>` - Google account email to use (overrides default)

Routing logic -

- If `--tab-id` is in `$ARGUMENTS`, call `update_tab_from_markdown` with document_id, tab_id, and the file content. Always pass `replace_existing=true`.

- If `--doc-id` is in `$ARGUMENTS` but no `--tab-id`, fetch the doc's primary tab and update that.

- If neither, create a new Google Doc via drive_upload_file + convert_to_doc in the folder named by `--folder`.

Always pass `user_google_email` equal to the `--account` value (or the resolved default). Surface the resulting doc URL and tab name.

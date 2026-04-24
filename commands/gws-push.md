---
name: gws-push
description: Push a local markdown file to Google Drive as a new or updated Google Doc.
arguments:
  - name: file
    description: Local path to the markdown file
    required: true
  - name: folder
    description: Drive folder ID to put the Doc in
    required: false
  - name: doc_id
    description: Existing Google Doc ID to update (instead of creating new)
    required: false
  - name: tab_id
    description: Specific tab to write into (requires doc_id)
    required: false
  - name: account
    description: Google account email to use (overrides default)
    required: false
---

Push the specified markdown file to Google Drive.

Routing logic -

- If `tab_id` is provided, call `update_tab_from_markdown` with document_id, tab_id, and the file content. Always pass `replace_existing=true`.

- If `doc_id` is provided but no `tab_id`, fetch the doc's primary tab and update that.

- If neither, create a new Google Doc via drive_upload_file + convert_to_doc in the specified `folder`.

Always pass `user_google_email={account}` (or the resolved default). Surface the resulting doc URL and tab name.

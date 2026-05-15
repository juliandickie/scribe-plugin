---
description: Use when the user's request involves Google Docs - reading or updating document content, working with specific tabs, batch updates, find-and-replace, headers/footers, or document structure. Triggers on Google Doc, document, doc tab, tab structure, find and replace, doc URL.
last-validated: 2026-05-15
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

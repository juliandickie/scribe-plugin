---
description: Use when the user's request involves Google Docs - reading or updating document content, working with specific tabs, filling a tab from a markdown file, batch updates, find-and-replace, headers/footers, or document structure. Triggers on Google Doc, document, doc tab, tab structure, tab URL, sync markdown to a doc, find and replace, doc URL.
last-validated: 2026-10-01
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

Parameters: `document_id`, `user_google_email`, optional `tab_id`, `detailed`. Returns: tab list with IDs and titles, heading hierarchy.

Without `tab_id` it reports the FIRST tab's statistics (including up to 100 `empty_paragraph_ranges`) alongside the `tabs` list. When you only need tab ids and titles, call it with no `tab_id` and `detailed=false` and read only `tabs`; from the shell, the helper's `--list-tabs` prints just the ids, titles and tab URLs (see "Populate a tab from a file" below).

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

`markdown_text` is inline only, so the whole tab passes through the session's context. For content that already sits in a file, use the helper below instead.

The `create` result carries the new `tab_id` but its `link` is the plain Doc URL. A tab's shareable URL is the Doc URL plus `?tab=<tab id>`, for example `https://docs.google.com/document/d/<doc id>/edit?tab=t.abc123`. Build it yourself whenever a tab link goes into a task, an email or a report.

### create_doc

Create a new doc.

Parameters: `title`, optional `content` (plain text), `user_google_email`. There is no folder parameter on the pinned 1.26.1 - the Doc lands in My Drive root, so move it with `update_drive_file` (`add_parents`, `remove_parents`) when it belongs in a folder.

The new Doc has a single tab titled "Tab 1" (`t.0`). If the Doc will hold named tabs, rename it with `manage_doc_tab rename` rather than leaving "Tab 1" in place.

### import_to_google_doc

Convert and import a local file into a new Google Doc.

Parameters:

- `file_name` (required) - name of the new Doc (any extension is ignored)

- `file_path` - sandbox-bound (see push/SKILL.md); or `file_url` (http/https), or inline `content`

- `source_format` - `"md"`, `"txt"`, `"html"`, `"docx"`, `"odt"`, `"rtf"` (auto-detected from the file name when omitted)

- `folder_id` (optional, defaults to `root`)

- `user_google_email`

Like `create_doc`, the imported Doc arrives with a single tab titled "Tab 1". Rename it when the Doc is meant to carry named tabs.

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

Create a table populated from a 2D array. Optional `header_rows` pins the leading N rows so they repeat after every page break. Reports PARTIAL SUCCESS (with the effective index) when the table is created but a follow-up styling step does not fully apply - check the response, not just the absence of an error.

### update_paragraph_style

Apply paragraph styling. Supports per-edge border control via `border_edges`, `border_color`, `border_width`, `border_dash`, and `border_padding`.

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

## Populate a tab from a file - the helper

Scribe ships `scripts/doc-tab-populate`, which fills an EXISTING tab from a markdown file on disk. It runs the server's own converter on the file and sends exactly the requests `populate_from_markdown` sends (verified structurally identical on 1.26.1), so the text never passes through the session's context and nothing is retyped. It also reads the tab back and checks it.

Use it when -

- the markdown already sits in a file larger than about 8 KB, or

- you are syncing more than one Doc or tab in the session, or

- the content must land verbatim (a render, a generated report, anything a person wrote).

Keep inline `populate_from_markdown` for small content you are composing in the conversation.

Run it with Bash. The wrapper picks the workspace-mcp version the plugin pins, via uvx, so it needs no setup beyond an authenticated account -

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/doc-tab-populate" --account <email> --doc <doc id> --list-tabs
"${CLAUDE_PLUGIN_ROOT}/scripts/doc-tab-populate" --account <email> --doc <doc id> --tab <tab id> --file <path.md>
"${CLAUDE_PLUGIN_ROOT}/scripts/doc-tab-populate" --account <email> --doc <doc id> --tab <tab id> --file <path.md> --write --check
```

If that path does not resolve, find the installed copy with `ls -d ~/.claude/plugins/cache/*/scribe/*/scripts/doc-tab-populate` and use the one for the installed Scribe version. On Windows call `uvx --from workspace-mcp==<pinned version> python <plugin>/scripts/doc-tab-populate.py` with the same arguments.

- No mode flag is a dry run (reads the Doc, confirms the tab, prints the request count). `--write` replaces the tab (`replace_existing=true`), `--append` adds after the existing content (`replace_existing=false`), `--list-tabs` prints tab ids, titles and URLs.

- Every write is followed by the read-back check, and `--check` runs it alone. It confirms every text block of the file is in the tab, in order (after an `--append`, only in the appended part), and prints the tab URL. It checks TEXT, not layout - it also prints `WARN` lines for flattened tables, flattened nested lists and emoji, and `--strict` turns those into exit 3.

- Exit codes - 0 all text landed, 1 text missing (listed), 2 error and nothing written, 3 a `WARN` under `--strict`, 4 a write was sent but its outcome is unknown or the read-back failed. On 4, run `--check` before anything else and never re-run an `--append` blindly.

- Built-in refusals - a file with no text (it would blank the tab; `--allow-empty` overrides), a file with emoji or other characters outside the Basic Multilingual Plane (see Gotchas; `--allow-astral` overrides), and a write under a workspace-mcp other than the pinned one. The write carries the Doc's revision id, so a Doc edited between the read and the write fails loudly instead of being cleared at stale offsets. When appending to a tab whose last paragraph has text, the helper inserts a paragraph break first (see Gotchas).

- The file can live anywhere readable (a repo, a render folder); unlike `import_to_google_doc`, the helper does not require `~/.workspace-mcp/attachments`. Pass `--sandbox` to apply that restriction anyway. Secret locations (the credentials folder, `.env`, `.ssh` and similar) are always refused.

### Replace a tab's content from a file, keeping the old version

1. `manage_doc_tab create` with a title and `index` - note the new `tab_id`.

2. Helper with `--write --check` into the new tab. Fix anything the check reports before going on.

3. If a `WARN - tables flattened` line appears, run the table repair pass (Gotchas) on the new tab.

4. `manage_doc_tab rename` the original tab (for example to "Archive - original") if the user is replacing it, and hand back the new tab's URL.

To overwrite a tab in place instead, skip step 1 and point `--tab` at the existing tab id.

## Common patterns

### Update a specific tab from markdown

1. `inspect_doc_structure` to find tab_id by title.

2. Content in a file and larger than about 8 KB, or more than one Doc in the sync - the helper with `--write --check` (above). Otherwise `manage_doc_tab` with `action="populate_from_markdown"`, `replace_existing=true`.

3. Verify - the helper's `--check` against the source file is the standard read-back, whichever path wrote the tab. Report the push complete only on a clean check.

### Create a new tab and populate it

1. `manage_doc_tab` with `action="create"`, `index`, `title` - response contains the new `tab_id`.

2. `manage_doc_tab` again with `action="populate_from_markdown"`, the new `tab_id`, and the markdown content - or, when the content is in a file, the helper with `--write --check`.

### Bulk find/replace

- Use `find_and_replace_doc` once per term, OR `batch_update_doc` with multiple find/replace requests for atomic application.

## Gotchas

- Docs use a tab structure now. A doc without explicit tabs has a single default tab; tab_id is still needed for `manage_doc_tab` calls.

- `inspect_doc_structure` is the source of truth for tab IDs - don't guess.

- `import_to_google_doc` uses the sandbox at `~/.workspace-mcp/attachments`. Files outside fail. See push/SKILL.md for the auto-copy decision tree.

- `populate_from_markdown` with `replace_existing=true` wipes the tab before writing. With false it appends.

- `batch_update_doc` is atomic - if any operation fails, none are applied. Use for invariant-critical updates.

- Tables - MANDATORY post-populate verification. `import_to_google_doc` renders GFM tables natively (it goes through Drive's file conversion). `populate_from_markdown` renders tables natively only once the workspace-mcp converter fix (2026-07, table support in the markdown writer, upstream PR #929) is in the pinned version; every released version through at least 1.30.0 (checked 2026-10-01; the current pin is 1.26.1) flattens every table to a single paragraph of raw pipe text while still returning success - a newer pin does NOT mean fixed until that PR merges. Because the failure is silent, after EVERY populate of table-bearing markdown run detailed `inspect_doc_structure` on the tab and check two things - the table count matches the source markdown, and no paragraph text starts with `| `. If a table flattened, run the repair pass - working bottom-up so indexes stay valid, for each pipe-text table replace the range `[start_index, end_index - 1]` with a single space via `modify_doc_text`, then `create_table_with_data` at `start_index + 1` with the 2D array parsed from the source markdown (always pass `tab_id`), then re-inspect to confirm table count matches and zero pipe paragraphs remain. Procedure proven 7-for-7 on 2026-07-13. Full history in `docs/issues/populate-from-markdown-table-rendering.md`.

- Nested lists flatten - the converter emits every list item at nesting level 0 under one bullet style, so a two-level list becomes one flat list and a numbered list nested under bullets becomes bullets. Confirmed live on 1.26.1 (2026-10-01), unchanged through 1.30.0. When hierarchy matters, rewrite the nested items as a flat list with the parent named in each item, or apply nesting afterwards with `batch_update_doc`. The helper's check prints `WARN - nested lists flattened` when this happens.

- Silent drops - three markdown constructs vanish on `populate_from_markdown` with a success response, confirmed live on 1.26.1. Indented (four-space) code blocks, top-level raw HTML blocks such as `<div>...</div>`, and every paragraph after the first inside a list item. Use fenced code blocks, avoid raw HTML, and keep list items to one paragraph. The helper's read-back check lists any such text as missing.

- Emoji break styles - any character outside the Basic Multilingual Plane (emoji, some symbols) makes the converter's offsets drift by one per character, because it counts one index where Google Docs counts two. Every insert after it lands a character early, so each later paragraph inherits the previous paragraph's style and inline bold, italic and links shift. Live on 1.26.1 (2026-10-01), one emoji in an H1 turned every later paragraph in the tab into an H1, with a success response. Strip emoji before `populate_from_markdown`, or use `import_to_google_doc` for a new Doc (Drive's conversion is not affected). The helper refuses such files unless `--allow-astral`. Upstream PR #929 also fixes the offset counting.

- Append glues onto a non-empty last paragraph - `populate_from_markdown` with `replace_existing=false` inserts just before the tab's final newline, so when the tab's last paragraph has text (typed by hand, or written by another tool) the first appended paragraph joins it ("...last lineFirst appended line"). Confirmed live on 1.26.1. Tabs written by `populate_from_markdown` end with an empty spacer paragraph, so appending after them is fine. Otherwise first add a newline at the end of the tab (`modify_doc_text` with `end_of_segment=true` and `text="\n"`), or use the helper's `--append`, which does it for you.

- Markdown's single newline is a soft break, so consecutive lines collapse into one paragraph in the Doc even though they look line-per-line in the source. For a real bulleted or numbered list, use a consistent marker (`- ` or `1. `) with a blank line before and after the list; tight items then render as real Doc bullets. For separate plain paragraphs (no bullets), put a blank line between each line. Do not force content into a list just to stop the collapse - separate paragraphs only need the blank line. A single paragraph where several lines were expected means a soft-break collapse.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing."

## Cross-service handoff

When a request spans services (e.g. saving an email thread to a doc), this skill's role ends after the docs operation. The orchestration layer handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Docs. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

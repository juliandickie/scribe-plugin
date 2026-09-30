---
description: Push a local markdown file to Google Drive as a new or updated Google Doc. Use when the user asks to push markdown to Drive, update a Doc tab with markdown content, or sync a markdown file to a specific Google Doc.
last-validated: 2026-10-01
---

# Scribe - Push

Push a markdown file to Google Drive via the workspace-mcp server.

User input arrives in $ARGUMENTS as free-form text. Parse it for -

- **File path** (positional, required) - the local markdown file to push

- **`--folder <id>`** (optional) - Drive folder ID where a new Doc should be created

- **`--doc-id <id>`** (optional) - existing Google Doc ID to update instead of creating new

- **`--tab-id <id>`** (optional, requires --doc-id) - specific tab within the doc to write into

- **`--account <email>`** (optional) - Google account to use (overrides default)

## File-path sandbox - read this BEFORE invoking `import_to_google_doc`

The sandbox applies to the new-Doc route (`import_to_google_doc`). The tab routes below use the Scribe helper, which reads the file where it is, so they need no copy step.

The MCP server enforces a directory sandbox for file uploads via the `ALLOWED_FILE_DIRS` environment variable. The plugin's manifest sets this to `~/.workspace-mcp/attachments`. Files OUTSIDE that directory cannot be uploaded.

Important behaviour -

- **Symlinks do not bypass the sandbox.** The server uses `os.path.realpath()` before the sandbox check, so a symlink in attachments pointing at the real file in a project repo gets rejected.

- **Subdirectories of attachments are fine.** `~/.workspace-mcp/attachments/my-project/file.md` works.

- **Project repo paths fail** by default. `/Users/X/code/my-repo/content.md` is outside the sandbox.

### Decision tree before calling `import_to_google_doc`

1. Read the user's file path. If it is already inside `~/.workspace-mcp/attachments/`, proceed directly.

2. If it is OUTSIDE that directory, do NOT just call the tool - the call will fail with a confusing sandbox error. Instead -

   a. Tell the user - "Your file is outside the MCP server's allowed directory. I'll copy it into `~/.workspace-mcp/attachments/scribe-session/` first, then upload from there. OK?"

   b. On confirmation, run `mkdir -p ~/.workspace-mcp/attachments/scribe-session && cp <user-file> ~/.workspace-mcp/attachments/scribe-session/`

   c. Use the copy as the upload source.

3. For batch uploads (e.g. "push all markdown in this directory"), copy the whole tree into a per-session subdirectory of attachments before iterating.

4. If the user wants persistent broader access (e.g. always allow uploads from a specific project root), tell them to override `ALLOWED_FILE_DIRS` in their `~/.claude/settings.json` MCP config -

   ```json
   "mcpServers": {
     "scribe": {
       "env": {
         "ALLOWED_FILE_DIRS": "${HOME}/.workspace-mcp/attachments:${HOME}/code/my-project"
       }
     }
   }
   ```

   Multiple directories are colon-separated on macOS/Linux, semicolon-separated on Windows.

## Routing logic

- If `--tab-id` is present - run the Scribe helper against that tab, from wherever the file already is -

  ```bash
  "${CLAUDE_PLUGIN_ROOT}/scripts/doc-tab-populate" --account <email> --doc <doc-id> --tab <tab-id> --file <path> --write --check
  ```

  It sends exactly what `manage_doc_tab populate_from_markdown` with `replace_existing: true` sends, but the file never passes through your context. Full usage is in the docs skill under "Populate a tab from a file". For a small file (under about 8 KB) inline `manage_doc_tab populate_from_markdown` is acceptable; for anything larger, or a batch of files, use the helper.

- If `--doc-id` is present but no `--tab-id` - list the tabs (`--list-tabs` on the helper, or `inspect_doc_structure` without `tab_id`, reading only `tabs`), pick the primary tab, then write it as above.

- If neither `--doc-id` nor `--tab-id` - call `import_to_google_doc` with `file_name` (the Doc's title) and `file_path` (NOT `content`) pointing at the file. Pass `source_format: "md"` and `folder_id: <--folder>` if specified. Using `file_path` instead of `content` avoids loading large files into the calling agent's context window. The new Doc has a single tab titled "Tab 1"; rename it with `manage_doc_tab rename` if the Doc will carry named tabs.

Always pass `user_google_email` (either the --account override or the resolved default for the current context - check the nearest clients/{CLIENT-ID}/profile.md if working in an AHPRA-style repo).

## Verify the push - MANDATORY after any tab route

Read the tab back against the source file before reporting success -

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/doc-tab-populate" --account <email> --doc <doc-id> --tab <tab-id> --file <path> --check
```

(A helper `--write` already runs this.) Exit 0 means every text block of the file is in the tab. Exit 1 lists what is missing - most often content the converter drops silently (indented code blocks, raw HTML blocks, second paragraphs inside a list item; see the docs skill Gotchas), which needs rewriting in the source and a re-push. The check is on text, not layout, and it prints `WARN` lines for the two layout failures it can see - flattened tables (handled below) and flattened nested lists.

## Table integrity check - MANDATORY after any populate route

Both tab routes above (`--tab-id`, and `--doc-id` without `--tab-id`) go through the converter behind `manage_doc_tab populate_from_markdown` (the helper uses the same one), whose table rendering fails SILENTLY on workspace-mcp pins that predate the 2026-07 converter table fix - every GFM table flattens to one paragraph of raw pipe text and the tool still reports success. The `import_to_google_doc` route is unaffected (Drive's native conversion renders tables correctly).

If the source markdown contains any GFM table (a separator row like `|---|---|`), then after the populate succeeds -

1. Run detailed `inspect_doc_structure` on the tab that was written.

2. Check that the reported table count matches the number of tables in the source markdown AND that no paragraph text starts with `| `.

3. If any table flattened, run the repair pass from the docs skill Gotchas - bottom-up per pipe-text table, `modify_doc_text` replaces `[start_index, end_index - 1]` with a single space, then `create_table_with_data` at `start_index + 1` with the 2D array parsed from the source markdown (always pass `tab_id`) - and re-inspect to confirm.

Do not report the push complete until this check has passed. A re-synced Doc with flattened tables is the single most recurrent defect on this path.

## Auth precondition

If the user has not authenticated any account yet, the call will fail with "No cached token" or similar. In that case, direct them to `/scribe:auth-init`.

If the user has authenticated some accounts but not the one this push needs (e.g. they're pushing to an iDD folder but only have their Pro Marketing token), direct them to `/scribe:auth-add EMAIL`.

## After success

Surface the resulting Google Doc URL and the tab name or doc title that was affected. For a tab, give the tab's own URL - the Doc URL plus `?tab=<tab-id>` (the helper prints it after `WRITTEN -`). For batch pushes, summarize - "Pushed N files to <folder name>" with a list.

## Multi-org caveat

If the user is pushing to a Drive folder owned by a different Workspace org than their currently-active OAuth client supports, the call will fail. See README's "Multi-org / cross-Workspace setup" section.

## Tool selection note for large files

Prefer `import_to_google_doc` with `file_path` over `content` when uploading from disk. The `content` parameter loads the file into the calling agent's context window which is wasteful for any non-trivial file size. `file_path` works for all supported formats (MD, TXT, HTML, DOCX, ODT, RTF) and is preferred for batch operations.

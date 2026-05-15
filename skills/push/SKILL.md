---
description: Push a local markdown file to Google Drive as a new or updated Google Doc. Use when the user asks to push markdown to Drive, update a Doc tab with markdown content, or sync a markdown file to a specific Google Doc.
last-validated: 2026-05-15
---

# Scribe - Push

Push a markdown file to Google Drive via the workspace-mcp server.

User input arrives in $ARGUMENTS as free-form text. Parse it for -

- **File path** (positional, required) - the local markdown file to push

- **`--folder <id>`** (optional) - Drive folder ID where a new Doc should be created

- **`--doc-id <id>`** (optional) - existing Google Doc ID to update instead of creating new

- **`--tab-id <id>`** (optional, requires --doc-id) - specific tab within the doc to write into

- **`--account <email>`** (optional) - Google account to use (overrides default)

## File-path sandbox - read this BEFORE invoking any tool

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

Once the file is in an allowed location -

- If `--tab-id` is present - call `manage_doc_tab` with `action: "populate_from_markdown"`, `document_id`, `tab_id`, the markdown content, and `replace_existing: true`

- If `--doc-id` is present but no `--tab-id` - call `inspect_doc_structure` to find the primary tab_id, then call `manage_doc_tab` with `action: "populate_from_markdown"` against that tab

- If neither `--doc-id` nor `--tab-id` - call `import_to_google_doc` with `file_path` parameter (NOT `content`) pointing at the file. Pass `source_format: "md"` and `parent_folder_id: <--folder>` if specified. Using `file_path` instead of `content` avoids loading large files into the calling agent's context window.

Always pass `user_google_email` (either the --account override or the resolved default for the current context - check the nearest clients/{CLIENT-ID}/profile.md if working in an AHPRA-style repo).

## Auth precondition

If the user has not authenticated any account yet, the call will fail with "No cached token" or similar. In that case, direct them to `/scribe:auth-init`.

If the user has authenticated some accounts but not the one this push needs (e.g. they're pushing to an iDD folder but only have their Pro Marketing token), direct them to `/scribe:auth-add EMAIL`.

## After success

Surface the resulting Google Doc URL and the tab name or doc title that was affected. For batch pushes, summarize - "Pushed N files to <folder name>" with a list.

## Multi-org caveat

If the user is pushing to a Drive folder owned by a different Workspace org than their currently-active OAuth client supports, the call will fail. See README's "Multi-org / cross-Workspace setup" section.

## Tool selection note for large files

Prefer `import_to_google_doc` with `file_path` over `content` when uploading from disk. The `content` parameter loads the file into the calling agent's context window which is wasteful for any non-trivial file size. `file_path` works for all supported formats (MD, TXT, HTML, DOCX, ODT, RTF) and is preferred for batch operations.

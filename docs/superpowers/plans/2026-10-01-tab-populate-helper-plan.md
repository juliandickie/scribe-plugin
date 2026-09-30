# Tab populate helper and 1 October friction fixes - Plan

Written 1 October 2026 at the start of an unattended overnight run. Source brief - the "Prompt for the Scribe plugin session" block in `~/code/idd-world/handoffs/idd-world/SESSION-HANDOFF-2026-09-30-me-objectives-and-writeback.md`. Julian lifted that brief's "show me a plan and wait" gate for this run, so this plan is recorded here and executed straight after.

## Goal

Make the working iDD prototype `academy-site/scripts/doc-tab-populate.py` available to everyone who installs Scribe, teach the skills when to use it, and fold in the smaller skill-prose fixes found on 30 September. Separately, draft (not ship) the real upstream fix, a file-path parameter on `manage_doc_tab populate_from_markdown`.

## Gates for this run

- Track 1 - commits on branch `tab-populate-helper`, push that branch, open ONE PR against `juliandickie/scribe-plugin` main with the patch version bump included. No merge, no tag, no release (the outfit marketplace installs Scribe from the unpinned git URL, so a merge to main is a release).

- Track 2 - research and a local branch in `~/code/repos/taylorwilsdon/google_workspace_mcp` only. No fork push, no upstream PR or issue, no message to the maintainer. Draft PR text goes in `docs/upstream/`.

- Live tests - one scratch Doc titled "Scribe helper scratch - delete me", nothing else in Drive touched.

## Track 1 - plugin level

### 1. The helper

`scripts/doc-tab-populate.py` plus a one-command wrapper `scripts/doc-tab-populate`.

- Arguments - `--account`, `--doc`, `--tab`, `--file`, with `--write` (replace the tab, the tool's `replace_existing=true`), `--append` (the `replace_existing=false` path), `--check` (read back), `--list-tabs` (tab ids, titles and tab URLs only), `--sandbox` (opt-in parity with `ALLOWED_FILE_DIRS`), `--strict` (structure warnings fail the run). Dry run by default.

- Interpreter - the wrapper reads the pinned version from `.claude-plugin/plugin.json` and runs `uvx --from workspace-mcp==<pin> python doc-tab-populate.py`. Verified on 1 October that this lands in the exact cached environment the running server uses (`~/.cache/uv/archive-v0/<hash>/bin/python`, `workspace-mcp` 1.26.1), so no process grepping. Windows users call the same `uvx` line directly.

- Environment - the Python reads the `mcpServers.scribe.env` block of the manifest and sets each variable only when it is not already set, so the helper sees the same `WORKSPACE_MCP_CREDENTIALS_DIR` and `ALLOWED_FILE_DIRS` as the server. A user who overrode them in `~/.claude/settings.json` exports the same value in their shell or passes `--credentials-dir`.

- Credentials - loaded through the server's own `auth.credential_store.get_credential_store()`, so filename encoding and legacy names match the server exactly. Read-only use, a refreshed access token is not written back, nothing credential-shaped is printed.

- Private function guard - the prototype imported the private `gdocs.docs_tools._find_tab_end_index`. The helper carries its own equivalent (it only walks the public Docs API response shape, including child tabs), and the offline tests assert it agrees with the server's copy whenever that exists. The one server function the helper depends on, `gdocs.docs_markdown_writer.markdown_to_docs_requests`, is checked for existence and for its `tab_id` and `start_index` keywords at start-up, with a clear error naming the installed version if either is missing. The pin-bump checklist in CLAUDE.md gains a line to re-run the helper's tests.

- Sandbox decision - NOT enforced by default, `--sandbox` opts in. Reason - `ALLOWED_FILE_DIRS` bounds what the MCP server process may read on behalf of a tool call, a path Claude Code's permission prompts never see. The helper runs through Bash, where Claude Code's own permission layer shows the full command line, file path included, and the user's shell can already read the file. Enforcing it would bring back the copy-into-attachments step the helper exists to remove. The helper still always refuses the obvious secret locations (the credentials directory, `.env` files, `.ssh`, `.aws`, `.gnupg`, `.kube`, gcloud config, and well-known credential filenames). The upstream parameter in Track 2 runs inside the server, so it MUST enforce the sandbox, exactly as `import_to_google_doc` does.

- The check - parses the source with markdown-it (the writer's own parser) and collects every text-bearing block, headings, paragraphs, list items at any depth, blockquotes, fenced and indented code, HTML blocks and table cells, rendered to plain text the way the writer renders inline tokens. Each block must appear in the tab's text, which is walked through paragraphs, tables and child elements. Missing text exits 1. Structure is reported as warnings - source tables against native tables and pipe-text paragraphs, and nested list items in the source against nested bullets in the tab. `--strict` turns warnings into exit 3. The check is on text, not layout, and says so.

### 2. Teach the skills

`skills/docs`, `skills/push` and `skills/workspace`, plus `docs/services.md`.

- For a tab whose markdown already sits in a file larger than about 8 KB, or any sync of more than one Doc, create the tab with `manage_doc_tab create`, run the helper with `--write --check`, then rename the original tab if the user is replacing one. Keep `populate_from_markdown` inline for small generated content.

- The read-back check becomes the standard "verify the push" step, stated as a text check, with the table and nesting warnings routed to the existing repair guidance.

### 3. Small prose fixes

- Tab URL is the Doc URL plus `?tab=<tab id>` - docs and push skills.

- Nested lists flatten on `populate_from_markdown` - confirm live on 1.26.1 with a two-level list in the scratch Doc, then add to the docs skill Gotchas and to `docs/issues/populate-from-markdown-table-rendering.md` as an adjacent observation, alongside the other silent drops found by reading the writer (indented code blocks, top-level HTML blocks, second paragraphs of list items).

- `import_to_google_doc` gives a single tab titled "Tab 1" - say so where the skills create Docs. Confirm live.

- `inspect_doc_structure` returns up to 100 `empty_paragraph_ranges` - tell the skills which call to use when only tab ids and titles are needed (the helper's `--list-tabs`, or `inspect_doc_structure` without `tab_id` if that proves lighter). Confirm live.

### 4. The Shared Drive search puzzle

Reproduce with one variable at a time against a known Shared Drive Doc - the grouped OR and AND query without `corpora`, the same query with `corpora: allDrives`, and a simple query without `corpora`. If `corpora` is the cause, the drive skill says to pass `allDrives` for Shared Drive searches. Read-only.

### 5. `manage_sheet_tab`

Document it in `skills/sheets/SKILL.md` and `docs/services.md` from the tool's live schema.

### 6. Release plumbing

Patch bump to 1.3.1 in both manifests (plugin.json is 1.3.0 and untagged, marketplace.json still says 1.2.0, so both move to 1.3.1 and the drift is fixed). `make validate` gains a check for the two helper files and a `make test` target runs the offline tests under the pinned interpreter. CLAUDE.md "Current state" and the README brought current. Run `make validate`, `make test`, `make check-upstream`, `make release-notes`, `make orient`, the dash grep, and the `plugin-dev:plugin-validator` agent.

## Track 2 - upstream draft

7. Research first (existing issue or PR, PR #929 state, PyPI delta 1.26.1 to latest). Then, in the reference clone, a local branch off current upstream main adding `markdown_file_path` to `manage_doc_tab`, mutually exclusive with `markdown_text`, resolved through `core.utils.validate_file_path` exactly as `import_to_google_doc` does, with tests beside the existing tab tests. Commit locally only. Draft PR text in `docs/upstream/`.

8. Retirement plan for the helper in `docs/upstream/`, the trigger being a PyPI release that contains the parameter plus a pin bump.

## Out of scope

Any change to the idd-world prototype, bumping the pin, merging, tagging, releasing, or touching a Doc other than the scratch Doc.

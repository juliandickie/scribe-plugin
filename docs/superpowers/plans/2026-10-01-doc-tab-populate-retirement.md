# Retiring scripts/doc-tab-populate - Plan

Written 1 October 2026. The helper in `scripts/doc-tab-populate` exists because `manage_doc_tab populate_from_markdown` only takes inline `markdown_text`. The real fix is upstream, a `markdown_file_path` parameter on that tool, drafted on 1 October on a local branch in the reference clone and not yet proposed (see the 2026-10-01 session handoff for its state). This plan says when and how the plugin moves off the helper, so a future session does not have to rediscover it.

## Trigger

All three must be true before any retirement work starts.

1. An upstream `workspace-mcp` release on PyPI contains `markdown_file_path` (or whatever name the maintainer chooses) on `manage_doc_tab populate_from_markdown`. Check with `make check-upstream`, then read the tool's signature at the released tag, not the PR - `git show v<ver>:gdocs/docs_tools.py` in the reference clone.

2. The plugin pin in `.claude-plugin/plugin.json` has been bumped to that release or later, following the CLAUDE.md "Pinning to a new upstream version" checklist.

3. A live test on that pin in a scratch Doc passes - the tool with the file parameter, then the helper's `--check` against the same file, exit 0.

Until then, nothing in this plan applies and the helper is the primary path.

## What changes at retirement

### Stage 1 - the tool becomes primary, the helper becomes the check (same release as the pin bump)

- `skills/docs/SKILL.md` "Populate a tab from a file" - lead with `manage_doc_tab` `action="populate_from_markdown"`, `markdown_file_path=<path>`. Note that the tool's file parameter is bound by `ALLOWED_FILE_DIRS` like `import_to_google_doc`, so files outside `~/.workspace-mcp/attachments` need the push skill's staging step or an `ALLOWED_FILE_DIRS` override - the one real advantage the helper keeps.

- `skills/push/SKILL.md` routing - the `--tab-id` and `--doc-id` routes call the tool with the file parameter after the existing sandbox decision tree, instead of the helper.

- `skills/workspace/SKILL.md` "Markdown files to Doc tabs" - same switch.

- KEEP the helper's `--check` as the standard read-back step. The tool reports success on silent drops (flattened tables, flattened nesting, dropped code and HTML blocks, dropped list-item paragraphs) and the upstream parameter does not change that. The check is the part of the helper with lasting value.

- KEEP `--write` and `--append` documented as the fallback for files outside the sandbox, and for anyone pinned to an older `workspace-mcp`.

### Stage 2 - retire the writer half (a later release, once Stage 1 has run cleanly for a while)

Only if the read-back check has moved somewhere else (an upstream verify option, or a separate check script), or the maintainer adds a post-write verification that covers text. Otherwise stop at Stage 1 - the helper stays, as a checker.

- Move `scripts/doc-tab-populate`, `scripts/doc-tab-populate.py` and `scripts/tests/` to `scripts/legacy/` with a one-line README (what, when, why), per the archive-over-delete rule. Do not delete them.

- Remove the helper-presence lines from `make validate` and point `make test` at whatever replaced the tests.

- Remove the helper sections from the three skills and `docs/services.md`, and the CLAUDE.md and README mentions.

## Also check at every pin bump, until retirement

The helper depends on one upstream function and one private behaviour. At every pin bump, before `make publish` -

- Run `make test`. It fails loudly if `gdocs.docs_markdown_writer.markdown_to_docs_requests` loses its `tab_id` or `start_index` keywords, and its parity test compares the helper's tab-end walk with the server's private `_find_tab_end_index` whenever that still exists.

- Diff `manage_doc_tab`'s populate branch between the old and new tags (`git diff v<old> v<new> -- gdocs/docs_tools.py`). If the request list it sends changed (for example a new clearing rule or a different append index), mirror it in `build_requests` and its tests.

- Run one live `--write --check` into a scratch Doc.

## If upstream declines the parameter

The helper stays as the primary path and this plan is closed with a note. The drafted branch lives in the reference clone; archive its PR text next to the other upstream drafts.

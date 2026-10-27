# Changelog

Releases before 1.3.3 are described on the [GitHub releases page](https://github.com/juliandickie/scribe-plugin/releases).

## 1.3.3 - 2026-10-27

This release ships the `workspace-mcp` 2.2.0 pin to installed copies. The pin merged to main in PR #6 at plugin version 1.3.2, and Claude Code only updates an installed plugin when its version changes, so 1.3.2 installs kept running 1.26.1. Nothing else changes in the plugin.

### Upstream - workspace-mcp 1.26.1 to 2.2.0

- 2.0.0 moves the server to FastMCP 4 and MCP Python SDK v2. Upstream says no tool migration is needed.
- 2.1.0 lets `draft_gmail_message` save a forward as a draft (`forward_message_id`), and restores the 60 second Google API timeout that 2.0 had halved.
- 2.1.1 never retries an ambiguous Gmail send. A timeout or dropped connection now returns an error that says to check Sent, instead of risking a second copy.
- 2.1.2 builds Gmail sends, drafts, replies and forwards the way Gmail web does (MIME layout, quoted reply trail, forwarded-message block). It rejects a `from_email` that is not a Send As identity, and an entity-escaped HTML body. It also renders Markdown tables as real Docs tables in `populate_from_markdown` (our upstream PR #929).
- 2.2.0 adds reply-all for Gmail sends and drafts. Replies sent without a subject now inherit the thread's subject, and the `Re:` prefix no longer piles up behind `[list]` or ticket tags.
- No version up to and including 2.2.1 has a tool to edit, delete or send an existing Gmail draft. Both draft paths in `gmail/gmail_tools.py` call `drafts().create` only (checked in the 2.2.0 and 2.2.1 source). To change a draft, create a new one and delete the old one in Gmail.

### Tool changes that touch Scribe's skills

- Removed in 2.2.0 - `get_page_thumbnail` (Slides, replaced by `render_page_to_image`, which returns the slide as image content) and `debug_docs_runtime_info` (Docs). PR #6 already updated the slides and docs skills and `docs/services.md`.
- Removed in 1.29 - 11 per-operation Apps Script tools, replaced by action-based tools (`get_script_project` with `action`, `manage_script_project`, `manage_script_content`, `manage_script_version`, `manage_script_trigger`, `get_script_version`, `list_script_deployments`, `get_script_activity`). No Scribe skill named the old tools.
- `insert_smart_chips` was added in 1.29 and removed in 1.30, where `modify_sheet_values` took over with `chips`. It was never in a Scribe pin, and no skill names it.
- Added - `manage_named_range` (Sheets, 1.28) and `render_page_to_image` (Slides, 2.2.0).
- The tool count goes from 123 to 119 across the plugin's 12 tool groups.

### OAuth

- Chat now asks for `chat.memberships.readonly` (1.27.1). An account authorised on 1.26.1 must run `start_google_auth` again before the Chat tools work. Other services keep working without re-consent.

### Verified on 2026-10-27

- `workspace-mcp@2.2.0` started over stdio with the plugin's own env and `--tools` list.
- `tools/list` returned 119 tools, including every Gmail, Drive and Docs tool the skills name.
- One read-only call, `search_gmail_messages` with `page_size` 1 on an authorised account, returned a result. No write calls were made.
- Not yet run - a live push into a scratch Doc and a live `doc-tab-populate --write --check`, which need a person at the OAuth consent screen.

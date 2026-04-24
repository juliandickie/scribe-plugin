---
description: Use when you need to interact with Google Workspace - read or write Google Docs (including document tabs), upload or manage Drive files, search Gmail, or read Calendar events. Triggers on mentions of specific Google Doc URLs, Drive folder IDs, Docs tabs, markdown push to Drive, or any request to update/read Google Workspace content.
---

# Scribe - Google Workspace

## What this skill does

Enables Claude to call the `workspace-mcp` MCP server for Google Workspace operations. The server is declared inline in this plugin's manifest and is auto-installed via `uvx` on first use. It exposes tools for Docs, Drive, Gmail, Calendar, Sheets, Slides, Forms, and Tasks.

## When to use

Use this skill when the user's request involves -

- Reading or updating content in a specific Google Doc (including specific tabs)

- Creating or listing Drive folders or files

- Uploading markdown as a new Google Doc

- Searching Gmail messages or threads

- Reading Calendar events

- Any other Google Workspace operation the MCP server exposes

## Authentication model

The MCP server uses OAuth 2.0. Before any tool call succeeds, the user must have -

1. A Google Cloud Project with Drive API, Docs API, etc. enabled

2. An OAuth 2.0 Desktop Client JSON downloaded to `~/.workspace-mcp/` (or equivalent env-var-configured path)

3. Authenticated at least one Google account via the OAuth flow

If the user has not completed this setup, direct them to run `/scribe:auth-init` before attempting any MCP tool call.

## Account selection

The MCP server supports multiple authenticated accounts. When calling MCP tools, pass the `user_google_email` parameter to select which account to act as. If the user is working in a client context (an AHPRA-style clients/{CLIENT-ID}/ folder), check the client's profile.md frontmatter for `google_account_email`.

## Common tool patterns

**Push a local markdown file to Drive as a new Google Doc** -

1. Call drive_upload_file with the markdown file content and folder_id

2. Call drive_convert_to_doc to convert the uploaded markdown to a Google Doc

**Update a specific tab in an existing Google Doc** -

1. Call list_doc_tabs to enumerate the doc's tabs

2. Identify the target tab_id by title

3. Call update_tab_from_markdown with document_id, tab_id, markdown_text, replace_existing=True

**Create a new tab and populate it** -

1. Call insert_doc_tab with document_id, title, index

2. Parse the returned tab_id from the confirmation string

3. Call update_tab_from_markdown with the new tab_id

## User-invoked skill quick-reference

Each of these is a slash-invokable skill in this plugin -

- `/scribe:auth-init` - first-run OAuth setup

- `/scribe:auth-add` - add another Google account to the token store

- `/scribe:auth-status` - list authenticated accounts

- `/scribe:push` - push a markdown file to Drive

- `/scribe:client-resolve` - resolve a CLIENT-ID to its account and Drive folder (AHPRA-style repos)

## Source

This skill wraps the `workspace-mcp` Python package. The extension supporting markdown-to-Docs conversion lives at `juliandickie/google_workspace_mcp` branch `fork-extension`. Bug reports and PRs to that repo.

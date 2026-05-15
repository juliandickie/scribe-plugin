---
description: Use when a user request mentions Google Workspace - any Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, or Chat operation. Also triggers on multi-service or multi-account requests, document URLs, folder IDs, and natural phrases like "across my accounts," "in my Drive," "from my inbox." Routes work to service-specific skills and workflow skills.
last-validated: 2026-05-15
---

# Scribe - Workspace orchestration router

This skill is the routing brain for Scribe. It loads on every Workspace-context turn and teaches Claude how to think about routing, multi-account selection, cross-service chaining, and cross-plugin composition. It does NOT contain per-service MCP tool details - those live in the ten service skills which auto-activate alongside this one.

## Multi-account routing rules

Scribe supports multiple authenticated Google accounts. Pass `user_google_email` on every MCP tool call to select the account. The selection logic:

1. **Explicit user mention wins.** "Use julian@idd to..." or "for my Pro Marketing account" - use that one.

2. **Explicit multi-account intent triggers auto-loop.** "Check both my inboxes," "across all my accounts," "for julian@idd and julian@pro" - enumerate authenticated accounts (see below), then iterate, accumulating results. Do NOT prompt for confirmation when intent is this explicit.

3. **Client or contact context implies an account.** If working in an AHPRA-style `clients/{CLIENT-ID}/` folder, check `profile.md` frontmatter for `google_account_email`. If the user names a contact, look them up in Contacts and use the matching account.

4. **Ambiguous intent + single account authenticated.** Use that account. Do not prompt.

5. **Ambiguous intent + multiple accounts authenticated.** ("check my inbox") - prompt ONCE for clarification: "Which account - julian@idd or julian@pro?" Remember the choice within the conversation.

## Cross-service chaining patterns

These are the canonical sequences for common multi-step shapes.

### Email to Doc

1. Gmail - `search_gmail_messages` to find the thread, then `get_gmail_thread_content` to pull the full text.

2. Drive - if attachments matter, `get_gmail_attachment_content` then `create_drive_file` to save them into a client/contact subfolder.

3. Docs - `import_to_google_doc` with the thread content, or `manage_doc_tab populate_from_markdown` if writing into an existing doc tab.

### Calendar to prep Doc

1. Calendar - `get_events` for the window. For free/busy queries across attendees, use `query_freebusy` (not `manage_event`).

2. Gmail - `search_gmail_messages` filtered by attendee emails to find prior threads.

3. Docs - `create_doc` with structured sections (Attendees, Context, Agenda, Action items).

### Sheet logging (append-row pattern)

1. Sheets - read the target sheet's structure if unknown.

2. Sheets - append a row with timestamp + source link + payload.

This is the canonical pattern for support intake, lead intake, enrollment tracking.

### Drive activity scan

1. Drive - `list_drive_items` filtered by recent modification.

2. Docs - `list_document_comments` per doc to surface review activity.

3. Surface to user with links and a one-line activity summary.

## Service skill delegation

For per-service MCP tool details, defer to the auto-activated service skills:

- Email, threads, drafts, labels - see the gmail skill

- Events, calendars, availability, OOO - see the calendar skill

- Documents, tabs, batch updates - see the docs skill

- Folders, files, sharing - see the drive skill

- Sheets, ranges, formulas - see the sheets skill

- Slide decks - see the slides skill

- Contacts and People API - see the contacts skill

- Task lists - see the tasks skill

- Forms and responses - see the forms skill

- Google Chat - see the chat skill

If multiple service skills are in scope, expect all of them to load. They give Claude per-service tool API depth; this skill provides the chaining logic.

## Cross-plugin composition

When another plugin's tools are available in the session, Scribe defers domain-appropriate work to it rather than trying to replicate. Common patterns:

- **ClickUp plugin available** - after logging a support inquiry to Sheets, also create a ClickUp task with the email URL. Don't try to replicate task management in Scribe.

- **Slack plugin available** - after a workflow completes, post a brief summary to the relevant Slack channel. Don't try to replicate messaging.

- **Spiffy plugin available** - if a workflow touches a course customer, defer purchase/credit/coupon lookups to Spiffy.

- **AC Builder (ActiveCampaign) plugin available** - defer contact enrichment, tag application, and automation lookups to it.

Scribe never imports or directly calls other plugins' tool namespaces. Reference plugins by their user-facing names in skill prose ("if the ClickUp plugin is installed...") so the prose stays robust to plugin renames.

## Sandbox and attachment rules

The MCP server enforces a directory sandbox for file uploads via `ALLOWED_FILE_DIRS`. The plugin's manifest sets this to `~/.workspace-mcp/attachments`. Files outside that directory are rejected.

- **Symlinks do not bypass the sandbox.** The server uses `realpath()` before checking.

- **Subdirectories of attachments are fine.** Use per-session or per-client subdirs.

- **Project repo paths fail.** Auto-copy files into `~/.workspace-mcp/attachments/scribe-session/` if they come from outside.

The push skill (`skills/push/SKILL.md`) documents the auto-copy decision tree in detail. For workflow skills that handle attachments, link to that pattern rather than re-stating it.

## Enumerating authenticated accounts

`workspace-mcp` does not expose a tool to list authenticated accounts. The authoritative source is the filesystem: each authenticated account has a JSON token file at `~/.workspace-mcp/credentials/<email>.json`.

To enumerate accounts, run a bash listing:

```bash
ls ~/.workspace-mcp/credentials/*.json 2>/dev/null | xargs -n1 basename | sed 's/\.json$//'
```

Each line of output is one authenticated email. Use these as `user_google_email` parameters on MCP tool calls.

Windows equivalent:

```powershell
Get-ChildItem "$env:USERPROFILE\.workspace-mcp\credentials\*.json" | ForEach-Object { $_.BaseName }
```

## Setup precondition check

Before any MCP tool call, if you have any doubt the user has set up OAuth, enumerate the credentials directory (see above). If it is empty or missing, do NOT attempt other tool calls - they will fail with confusing token errors. Instead direct the user to `/scribe:auth-init`.

## User-invokable workflow quick reference

Slash-invokable workflow skills in this plugin (full reference in `docs/workflows.md`):

- `/scribe:daily-briefing` - inbox + calendar sweep for today

- `/scribe:inbox-triage` - categorise, label, draft replies across inboxes

- `/scribe:support-scan` - scan support inbox, log to sheet, draft responses

- `/scribe:meeting-prep` - pull meeting, related emails, build prep doc

- `/scribe:thread-to-doc` - email thread to Doc + save attachments to folder

- `/scribe:client-digest` - aggregate emails + events + Drive activity for a client

- `/scribe:weekly-wrap` - week summary doc across all services

- `/scribe:follow-up-tracker` - find unanswered sent emails, draft follow-ups

- `/scribe:contact-onboard` - bootstrap Drive folder + Contact + Sheet row + welcome email

- `/scribe:doc-chase` - find shared docs with no review activity, nudge reviewers

- `/scribe:attach-vault` - organise email attachments into Drive folders

- `/scribe:event-recap` - post-meeting notes doc + follow-up email draft

- `/scribe:smart-reply` - contextual draft using prior email history

- `/scribe:educator-setup` - bootstrap educator's Drive + tracker sheet + welcome

## Source and contribution

This skill wraps the `workspace-mcp` Python package on PyPI, maintained by [taylorwilsdon](https://github.com/taylorwilsdon/google_workspace_mcp). Bug reports about MCP server behaviour go upstream; bug reports about Scribe (skills, workflows, install flow) go to https://github.com/juliandickie/scribe-plugin.

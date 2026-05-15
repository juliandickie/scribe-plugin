# Scribe

**Google Workspace orchestration for Claude Code. Multi-account, multi-service, all 12 Workspace tool groups, 14 named cross-service workflows.**

![Scribe hero](docs/images/hero.png)

---

**Version 1.0.0** | MIT licensed | Wraps [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp)

```bash
/plugin marketplace add juliandickie/scribe-plugin
/plugin install scribe
/scribe:auth-init
```

## What you can do

- Run named workflows that span services - daily briefing, inbox triage, meeting prep, weekly wrap, and 10 more

- Compose Workspace operations dynamically from natural-language prompts - "check both my inboxes for anything urgent and create a summary doc"

- Manage multiple Google accounts in one Claude session - personal Gmail and business Workspace, agency client and own org, all switchable per call

- Push markdown into Drive or specific Doc tabs with high fidelity (the original Scribe v0.x feature, still here and improved)

## The problem v1.0 solves

You live in Google Workspace. Email, calendar, docs, sheets, slides, contacts, tasks - all of it. Most of your day is shuffling between them.

Scribe v0.x focused on one piece of that grunt work - getting markdown into the right Doc with the right tab. v1.0 expands the scope to the whole Workspace surface, with named workflows for the patterns you'd otherwise hand-stitch every time.

![Before and after](docs/images/before-after.png)

## Workflows

14 named slash commands that compose multi-service operations. Each accepts natural-language invocation OR explicit flags.

- `/scribe:daily-briefing` - inbox + calendar morning sweep across all accounts

- `/scribe:inbox-triage` - categorise unread, label, draft replies across inboxes

- `/scribe:support-scan` - scan support inbox, log to tracking sheet, draft responses

- `/scribe:meeting-prep` - pull meeting + related emails into a structured prep doc

- `/scribe:thread-to-doc` - convert email thread to Doc, save attachments to client folder

- `/scribe:client-digest` - aggregate emails + calendar + Drive activity for one contact

- `/scribe:weekly-wrap` - compile a week's activity across services into a summary doc

- `/scribe:follow-up-tracker` - find sent emails with no reply, draft follow-ups

- `/scribe:contact-onboard` - bootstrap Drive folder + Contact + Sheet row + welcome email

- `/scribe:doc-chase` - find shared docs with no review activity, nudge reviewers

- `/scribe:attach-vault` - organise email attachments into Drive by sender or project

- `/scribe:event-recap` - post-meeting notes doc + follow-up email draft

- `/scribe:smart-reply` - draft a contextual email using prior history with the contact

- `/scribe:educator-setup` - bootstrap an educator's Drive folder structure and welcome

Detailed reference - [docs/workflows.md](docs/workflows.md).

## Services

10 service skills auto-activate when their service is in scope. They teach Claude the full MCP tool API for each Google service.

- **gmail** - search, read, draft, send, label management

- **calendar** - events, free/busy, focus time, OOO

- **docs** - tabs, batch updates, find/replace, structure

- **drive** - folders, files, sharing, permissions, public access

- **sheets** - ranges, formulas, append rows, table creation

- **slides** - presentations, slide content updates

- **contacts** - lookup by name or email, create contacts

- **tasks** - Google Tasks lists and items

- **forms** - read responses, create forms

- **chat** - send and read Google Chat messages

Detailed reference - [docs/services.md](docs/services.md).

## Architecture

Three-layer skill model:

![Architecture](docs/images/architecture.png)

1. **Orchestration router** (`workspace/SKILL.md`) - auto-loads on every Workspace request. Routes between accounts, services, and workflows.

2. **Service skills** (10 files) - auto-load when their specific service is in scope. Teach the MCP tool API for that service.

3. **Workflow skills** (14 files) - user-invoked via slash command. Each is a complete recipe for one cross-service operation.

This keeps each skill focused (under 500 lines), avoids token bloat, and lets the marketplace user pick what to invoke.

## Multi-org and multi-account

Scribe handles multiple OAuth clients (one per Workspace org if you need cross-org access). The token cache stores credentials per email; multi-account loops are first-class in the orchestration router. See [docs/multi-org-setup.md](docs/multi-org-setup.md) for the symlink-swap pattern.

## Setup

The first-run flow walks through Google Cloud Project setup and OAuth (5-10 minutes once per Workspace org):

```bash
/scribe:auth-init      # one-time per org
/scribe:auth-add EMAIL # add another account to the token cache
/scribe:auth-status    # list authenticated accounts
```

After that, just speak naturally - "check my inbox for anything urgent today" - or invoke a named workflow.

## Customisation

- `ALLOWED_FILE_DIRS` env var in your `.claude/settings.json` MCP config can extend the upload sandbox beyond `~/.workspace-mcp/attachments`.

- `--permissions SERVICE:LEVEL` override (in place of `--tools`) lets you restrict OAuth scopes per service. See `skills/auth-init/SKILL.md` "Restricting scopes (advanced)" section.

- Workflow skills are independent files - fork the repo and edit any to suit your workflow needs.

## License

MIT.

## Credits

Wraps [`workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) by [@taylorwilsdon](https://github.com/taylorwilsdon). The breadth of Scribe v1.0 is possible because of his work on the underlying MCP server.

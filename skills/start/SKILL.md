---
description: Orientation for Scribe - checks which Google accounts are authenticated and lists what the plugin can do. Run this first, or any time you want to see Scribe's workflows.
disable-model-invocation: true
last-validated: 2026-06-13
---

# Scribe - Start

A human-facing orientation screen. Run it on first use, or any time to remember what Scribe offers. It does not change anything.

## 1. Check authentication

Enumerate authenticated accounts by listing the credentials directory:

```bash
ls ~/.workspace-mcp/credentials/*.json 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/\.json$//'
```

Windows (PowerShell):

```powershell
Get-ChildItem "$env:USERPROFILE\.workspace-mcp\credentials\*.json" | ForEach-Object { $_.BaseName }
```

- If the directory is empty or missing - no accounts are authenticated. Tell the user, then point them to `/scribe:auth-init` to set up the OAuth client and authenticate the first account. One line on what that unlocks - read and write across Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, and Chat for that account. Stop here.

- If one or more accounts exist - list them, then continue to section 2.

For deeper token health (expiry, scopes), defer to `/scribe:auth-status`; do not duplicate that inspection here.

## 2. Show what Scribe can do

Present the workflow commands grouped by use case, then the plain-language option.

Daily operations -

- `/scribe:daily-briefing` - inbox plus calendar sweep for today

- `/scribe:inbox-triage` - categorise, label, draft replies across inboxes

- `/scribe:follow-up-tracker` - find unanswered sent emails, draft follow-ups

- `/scribe:weekly-wrap` - week summary doc across all services

Client and contact work -

- `/scribe:client-digest` - aggregate a client's emails, events, and Drive activity

- `/scribe:contact-onboard` - bootstrap Drive folder, Contact, Sheet row, welcome email

- `/scribe:meeting-prep` - pull a meeting, related emails, build a prep doc

- `/scribe:event-recap` - post-meeting notes doc plus follow-up draft

- `/scribe:educator-setup` - bootstrap an educator's Drive plus tracker sheet plus welcome

Email and documents -

- `/scribe:thread-to-doc` - email thread to a Doc plus save attachments to a folder

- `/scribe:smart-reply` - contextual draft using prior email history

- `/scribe:support-scan` - scan a support inbox, log to a sheet, draft responses

- `/scribe:doc-chase` - find shared docs with no review activity, nudge reviewers

- `/scribe:attach-vault` - organise email attachments into Drive folders

Setup and accounts -

- `/scribe:auth-add EMAIL` - authenticate another Google account

- `/scribe:auth-status` - list accounts and token health

- `/scribe:push FILE` - push a local markdown file to Drive as a Doc

Or just ask in plain English - Scribe routes most requests without a command. Examples - "summarise my unread email from this week" or "save this thread to my client folder and draft a reply."

## Source

This skill wraps `workspace-mcp` (taylorwilsdon/google_workspace_mcp). The workflow catalog above mirrors `docs/workflows.md` and the router quick reference in `workspace/SKILL.md`; keep the three in sync when workflows change.

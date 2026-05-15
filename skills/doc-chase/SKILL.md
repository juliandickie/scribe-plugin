---
description: Find Google Docs shared with reviewers that have no recent comment or edit activity; draft reminder emails to the reviewers. Invoke via /scribe:doc-chase.
disable-model-invocation: true
argument-hint: [--folder ID] [--days 7] [--account email] [--draft-reminders]
last-validated: 2026-05-15
---

# Scribe - Doc review chaser

Finds Google Docs that have been shared for review but haven't been touched (no comments, suggested edits, or content changes) within the time window. Drafts polite reminder emails to the inactive reviewers.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--folder ID` (optional) - scope to docs in this folder. Default - all docs owned by the user.

- `--days N` (optional, default 7) - inactivity threshold.

- `--account email` (optional) - single account.

- `--draft-reminders` (optional flag) - also draft reminder emails.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Find candidate docs** - `search_drive_files` (or `list_docs_in_folder` if folder specified) for Docs owned by the user, modified more than `--days` ago.

3. **Per doc - find reviewers** - `get_drive_file_permissions` to find users with commenter or writer role (not owner).

4. **Per doc - check activity** - `list_document_comments` to check for recent comment activity in the inactivity window.

5. **Filter** - to docs with reviewers AND no comment/edit activity.

6. **Draft reminders** (if `--draft-reminders`) - per doc, per inactive reviewer, `draft_gmail_message` with a polite nudge linking the doc.

7. **Return** - list of stale docs with reviewer emails and draft URLs.

## Multi-account behaviour

Single account by default unless explicit multi-account intent.

## Cross-plugin composition

- **Slack plugin** - for reviewers in shared Slack workspaces, optionally DM them instead of email (faster response loop for internal reviewers).

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "What docs am I waiting on review for?"

- "Chase up outstanding doc reviews from last week"

Explicit args:

- `/scribe:doc-chase --folder ABC --days 10 --draft-reminders`

## Failure modes

- **No stale docs** - report clean state.

- **Multiple reviewers per doc** - draft separate reminders per reviewer (each personalised).

- **Doc is in a Shared Drive with org-wide access** - skip "all org" reviewers, only nudge specific named reviewers.

## Output

Always return:

- One-line summary - "Found X stale docs with Y inactive reviewers"

- List of docs with reviewer emails

- Draft URLs if drafted

- Cross-plugin steps skipped

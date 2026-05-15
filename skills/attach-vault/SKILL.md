---
description: Scan Gmail inbox for emails with attachments, organise the attachments into Drive folders by sender or project. Invoke via /scribe:attach-vault.
disable-model-invocation: true
argument-hint: [--since 30d] [--by sender|project] [--vault-root ID] [--account email]
last-validated: 2026-05-15
---

# Scribe - Attachment vault

Periodic attachment archival. Scans Gmail for emails with attachments in the time window, downloads each attachment, and organises them into Drive folders by sender (default) or by project (heuristic on subject line).

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--since 30d` (optional) - time window. Default - 30 days.

- `--by sender|project` (optional) - organisation strategy. Default - `sender`.

- `--vault-root ID` (optional) - parent Drive folder. Default - "Attachment vault" under My Drive.

- `--account email` (optional) - single account or default to all.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Per account - find emails with attachments** - `search_gmail_messages` with `query="has:attachment newer_than:<since>"`.

3. **Per message - extract metadata** - sender, subject, attachment list (name, size).

4. **Resolve vault root** - `search_drive_files` for "Attachment vault", `create_drive_folder` if absent.

5. **Determine destination subfolder** per attachment - `Vault/<sender-domain>/<sender>` for sender mode; `Vault/<project-tag>` for project mode where project-tag is heuristic on subject (e.g. extract bracketed prefixes like `[Project X]`).

6. **Create subfolders** as needed - `create_drive_folder`.

7. **Download and save attachments** - `get_gmail_attachment_content` then `create_drive_file` into the appropriate subfolder.

8. **Return** - summary of counts per subfolder, total attachments archived, total bytes.

## Multi-account behaviour

Loops all accounts by default.

## Cross-plugin composition

None specific. This is a pure Workspace workflow.

## Example invocations

Natural language:

- "Archive all my email attachments from the last month"

- "Save attachments to a vault by sender"

Explicit args:

- `/scribe:attach-vault --since 60d --by project`

- `/scribe:attach-vault --vault-root ABC...`

## Failure modes

- **Very large attachments** - confirm before downloading anything over a threshold (e.g. 50MB single file or 1GB cumulative).

- **Duplicate filenames** - append `-<timestamp>` to disambiguate.

- **Sandbox issues** - attachments save to Drive (not local), so the sandbox doesn't apply. If a Drive operation fails, surface the error.

## Output

Always return:

- Summary of counts per subfolder

- Total attachments archived

- Total bytes (rough)

- Any download skips with reason

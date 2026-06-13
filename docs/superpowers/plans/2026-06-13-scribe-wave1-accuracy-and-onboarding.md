# Scribe Wave 1 - Accuracy and Onboarding - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Scribe's gmail and file-handling docs match the real tool surface, surface the Google-Doc rendering gotchas where Claude reads them, add a `/scribe:start` discoverability command, and tidy plus Windows-harden the auth onboarding.

**Architecture:** Plugin-level only. Every change is skill markdown, the plugin manifest, or a local docs move. No upstream `workspace-mcp` change. Verification is `make validate` + the `plugin-dev:plugin-validator` agent + a writing-style grep + manual smoke (run by Julian, since it needs a plugin reload and an authenticated account). There are no unit tests in this repo; do not invent a test framework.

**Tech Stack:** Claude Code plugin (`skills/<name>/SKILL.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`), `Makefile` `validate` target, `plugin-dev:plugin-validator` agent.

**Source spec:** `docs/superpowers/specs/2026-06-13-scribe-attachments-and-onboarding-design.md` (clusters A, B, C, D1, D2 are Wave 1; cluster E is Wave 2, a separate plan).

---

## Scope and relationship to Wave 2

This plan is Wave 1 of the spec. It is shippable on its own. Wave 2 (cluster E - error-recovery map, tool-index references file, service-skill description audit, param trim) is a separate plan written after this one lands, because E's description audit and param trim build on the skill content this plan finalizes.

One overlap is handled deliberately here - the gmail skill is rewritten in Task 1 in a curated-digest style (key params plus gotchas plus the attachment model, trusting the live schema for the exhaustive param list). That means gmail's eventual cluster-E treatment is done as part of Wave 1, and Wave 2 will skip gmail. Every other service skill keeps its current style until Wave 2.

## Working conventions for every task

- Branch is already `spec/attachments-onboarding` (created during brainstorming). Stay on it.

- Plugin house style applies to all edits - no em or en dashes, no colons in headings (use " - "), straight quotes only, strip trademark and ligature glyphs. Match each file's existing list style (the current skill files use blank-line-separated bullets; keep that within a file you are editing - do not reformat existing lists to tight in this wave).

- After any edit, run the style guard before committing:
  ```bash
  cd /Users/juliandickie/code/scribe-plugin && grep -rn $'[–—]' <changed-files> && echo "FAIL dashes" || echo "PASS"
  ```

- Commit messages follow the repo style (`component - description`) and end with the trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```

- Do NOT bump the plugin version or run `make publish` in this plan. Version 1.0.0 stays until an explicit, separately-approved release step. README and CLAUDE.md are updated to reflect new content (Task 8) but not the version number.

## File structure

Files this plan creates or modifies, each with one clear responsibility:

- `skills/gmail/SKILL.md` (modify) - accurate send/draft surface, the three attachment modes, a sandbox gotcha. [Task 1]

- `skills/workspace/SKILL.md` (modify) - the cross-service "File and attachment handling" map with the param-name table; one `populate_from_markdown` caution. [Task 2, Task 4]

- `skills/drive/SKILL.md` (modify) - a real `get_drive_file_download_url` entry. [Task 3]

- `skills/docs/SKILL.md` (modify) - the table/list/paragraph rendering gotchas. [Task 4]

- `skills/start/SKILL.md` (create) - the `/scribe:start` discoverability command. [Task 5]

- `.claude-plugin/plugin.json` (modify) - Windows `${HOME}` handling decision. [Task 6]

- `skills/auth-init/SKILL.md` (modify) - one callback-clarity line. [Task 6]

- `docs/issues/scribe-auth-init-issues.md` -> `docs/issues/legacy/` plus `docs/issues/legacy/README.md` (move/create, local-only, gitignored). [Task 7]

- `README.md` and `CLAUDE.md` (modify) - new skill, corrected skill count, corrected writing-style rule 3. [Task 8]

---

## Task 1 - Gmail skill accuracy (Cluster A)

**Files:**
- Modify: `skills/gmail/SKILL.md` (the `### send_gmail_message` and `### draft_gmail_message` entries near lines 98-112, a new Attachments subsection, and one Gotchas bullet)

- [ ] **Step 1: Replace the `send_gmail_message` entry**

Find this block:

```markdown
### send_gmail_message

Send a new message.

Parameters:

- `to`, `subject`, `body` (required)

- `cc`, `bcc` (optional)

- `user_google_email`
```

Replace with:

```markdown
### send_gmail_message

Send a new message. Required - `to`, `subject`, `body`, `user_google_email`.

Key optional params (the live tool schema carries the full list and defaults; these are the ones that change behaviour) -

- `body_format` - `plain` (default) or `html`. Use `html` to send a formatted HTML email.

- `cc`, `bcc` - additional recipients.

- `from_email` plus `from_name` - send from a configured Gmail Send As alias (set up under Settings > Accounts > Send mail as). `from_name` sets the display name, producing a `Name <email>` From header.

- `include_signature` - defaults true and appends the Gmail signature. Set false when the body already carries its own sign-off, otherwise the message gets a double signature.

- `attachments` - see the Attachments subsection below.

- `thread_id`, `in_reply_to`, `references`, `quote_original` - reply threading. `quote_original` requires `thread_id`.
```

- [ ] **Step 2: Replace the `draft_gmail_message` entry**

Find this block:

```markdown
### draft_gmail_message

Create a draft. Same parameter shape as send.
```

Replace with:

```markdown
### draft_gmail_message

Create a draft. Same surface as `send_gmail_message`, with one difference - `to` is optional for a draft (you can save a recipient-less draft) but required for send. This is the default for any reply you are not explicitly told to send.
```

- [ ] **Step 3: Add an Attachments subsection**

Insert this immediately after the `draft_gmail_message` entry (before `### modify_gmail_message_labels`):

```markdown
### Attachments (send and draft)

`attachments` is a list; each item is one of three shapes. Pick by where the file already is -

- Already in Drive or on an email - pass `{"url": "<mcp-url>"}` using the URL returned by `get_drive_file_download_url` or `get_gmail_attachment_content`. No local staging needed.

- A genuinely-local file (for example on the Desktop) - pass `{"path": "<file>"}`. The `path` mode is the only one bound by the `ALLOWED_FILE_DIRS` sandbox, so the file must already live in `~/.workspace-mcp/attachments` or a configured allowed dir. See "File and attachment handling" in `workspace/SKILL.md` for the map and `push/SKILL.md` for the staging decision tree.

- Bytes already in memory - pass `{"content": "<base64>", "filename": "<name>"}` (standard base64, not urlsafe).

Optional `mime_type` per item is auto-detected if omitted.
```

- [ ] **Step 4: Add a Gotchas bullet**

In the existing `## Gotchas` section, add this bullet:

```markdown
- Attachments have three modes (url / path / content). Only `path` hits the `ALLOWED_FILE_DIRS` sandbox. For a file already in Drive or on an email, pass its `url` from `get_drive_file_download_url` / `get_gmail_attachment_content` and skip staging entirely.
```

- [ ] **Step 5: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -n $'[–—]' skills/gmail/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: `make validate` reports success; style check prints `PASS style`.

- [ ] **Step 6: Commit**

```bash
git add skills/gmail/SKILL.md && git commit -m "gmail skill - document real send/draft surface and attachment modes (Cluster A)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2 - Cross-service file-handling map (Cluster B, router)

**Files:**
- Modify: `skills/workspace/SKILL.md` (replace the `## Sandbox and attachment rules` section, lines ~100-110)

- [ ] **Step 1: Replace the section**

Find this block:

```markdown
## Sandbox and attachment rules

The MCP server enforces a directory sandbox for file uploads via `ALLOWED_FILE_DIRS`. The plugin's manifest sets this to `~/.workspace-mcp/attachments`. Files outside that directory are rejected.

- **Symlinks do not bypass the sandbox.** The server uses `realpath()` before checking.

- **Subdirectories of attachments are fine.** Use per-session or per-client subdirs.

- **Project repo paths fail.** Auto-copy files into `~/.workspace-mcp/attachments/scribe-session/` if they come from outside.

The push skill (`skills/push/SKILL.md`) documents the auto-copy decision tree in detail. For workflow skills that handle attachments, link to that pattern rather than re-stating it.
```

Replace with:

```markdown
## File and attachment handling

Scribe references a file in three ways across tools. Pick by where the file already is, not by habit.

- **Already in Drive or on an email** - get an MCP URL from `get_drive_file_download_url` or `get_gmail_attachment_content` and pass it as the file reference. No local staging. This is the fast path for gmail attachments and for `create_drive_file`.

- **A genuinely-local file** (Desktop, a repo) - reference it by local path. This is the only mode bound by the `ALLOWED_FILE_DIRS` sandbox.

- **Bytes in memory** - pass the content inline.

The param name for each mode differs per tool, which is the easy thing to get wrong -

| Tool | Local-file param | Remote/URL param | Inline param |
|---|---|---|---|
| `send_gmail_message` / `draft_gmail_message` | `path` (in `attachments[]`) | `url` (in `attachments[]`) | `content` + `filename` |
| `create_drive_file` | `fileUrl` with `file://` | `fileUrl` (http/https) | `content` |
| `import_to_google_doc` | `file_path` (local or `file://`) | `file_url` (http/https) | `content` |

The `ALLOWED_FILE_DIRS` sandbox (manifest default `~/.workspace-mcp/attachments`) applies to the local-file modes. It is verified for the gmail `path` mode and `import_to_google_doc` `file_path`. For local-file reads it behaves as -

- **Symlinks do not bypass it.** The server uses `realpath()` before checking.

- **Subdirectories are fine.** Use per-session or per-client subdirs.

- **Project repo paths fail** by default. Stage the file into `~/.workspace-mcp/attachments/scribe-session/` first.

For a file already in Drive or Gmail, the URL mode above skips staging entirely. When creating a Drive file from a local source, prefer the URL or inline `content` mode to avoid the sandbox question. The push skill (`skills/push/SKILL.md`) has the full staging decision tree; link to it rather than re-stating it.
```

- [ ] **Step 2: Note the one unverified cell for the executor**

The `create_drive_file` `fileUrl` with `file://` sandbox behaviour is not verified against the live tool. The replacement prose above deliberately avoids asserting it (it steers to URL/content instead). If a later session confirms `file://` is sandbox-bound, no change is needed; if it is not, the steer still holds. Do not assert it without a live check.

- [ ] **Step 3: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -n $'[–—]' skills/workspace/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: success and `PASS style`.

- [ ] **Step 4: Commit**

```bash
git add skills/workspace/SKILL.md && git commit -m "workspace router - file and attachment handling map with param table (Cluster B)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3 - Drive get_drive_file_download_url entry (Cluster B, drive)

**Files:**
- Modify: `skills/drive/SKILL.md` (the `### get_drive_file_download_url` entry, lines ~53-55)

- [ ] **Step 1: Verify the return shape (needs an authenticated account)**

The send/draft schema says this tool returns a URL usable as an attachment `url`; a prior session observed it saving the file locally and returning a path. Confirm which before writing the entry. With an authed account, call `get_drive_file_download_url` on any small Drive file and inspect the returned value.

If no authed account is available in the working session, leave the entry as written in Step 2 (it is true for both shapes) and add a one-line note for Julian to confirm.

- [ ] **Step 2: Replace the entry**

Find this block:

```markdown
### get_drive_file_download_url

Get a download URL for a file.
```

Replace with:

```markdown
### get_drive_file_download_url

Get a reference to a Drive file's contents for a follow-up action.

Parameters: `file_id`, `user_google_email`.

Two follow-ups it enables -

- Attach the file - pass the returned reference as a gmail attachment `url` (the send and draft tools name this tool explicitly) or as a `create_drive_file` `fileUrl`. No staging.

- Read it locally - the file also lands in the managed attachments directory, so it can be read from disk after the call.

See "File and attachment handling" in `workspace/SKILL.md` for how this fits the cross-tool file-reference model.
```

- [ ] **Step 3: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -n $'[–—]' skills/drive/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: success and `PASS style`.

- [ ] **Step 4: Commit**

```bash
git add skills/drive/SKILL.md && git commit -m "drive skill - real get_drive_file_download_url entry (Cluster B)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4 - Doc rendering gotchas (Cluster C)

**Files:**
- Modify: `skills/docs/SKILL.md` (add to the `## Gotchas` section, near line 158)
- Modify: `skills/workspace/SKILL.md` (one caution in the `### Email to Doc` pattern, near line 33)

- [ ] **Step 1: Add the docs-skill Gotchas bullets**

In `skills/docs/SKILL.md`, in the `## Gotchas` section, add these two bullets:

```markdown
- `populate_from_markdown` and `import_to_google_doc` render GFM tables as raw pipe text, not real Doc tables. Express tabular data as a properly-formatted list, or build a real table with `create_table_with_data`. Verify with `inspect_doc_structure(detailed=true)` - `tables: 0` means the table did not render.

- Markdown's single newline is a soft break, so consecutive lines collapse into one paragraph in the Doc even though they look line-per-line in the source. For a real bulleted or numbered list, use a consistent marker (`- ` or `1. `) with a blank line before and after the list; tight items then render as real Doc bullets. For separate plain paragraphs (no bullets), put a blank line between each line. Do not force content into a list just to stop the collapse - separate paragraphs only need the blank line. A single paragraph where several lines were expected means a soft-break collapse.
```

- [ ] **Step 2: Add the router caution**

In `skills/workspace/SKILL.md`, in the `### Email to Doc` pattern, find:

```markdown
3. Docs - `import_to_google_doc` with the thread content, or `manage_doc_tab populate_from_markdown` if writing into an existing doc tab.
```

Replace with:

```markdown
3. Docs - `import_to_google_doc` with the thread content, or `manage_doc_tab populate_from_markdown` if writing into an existing doc tab. Mind the rendering gotchas - tables become raw pipe text, and single-newline lines collapse into one paragraph (see the docs skill Gotchas for the list and paragraph patterns).
```

- [ ] **Step 3: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -n $'[–—]' skills/docs/SKILL.md skills/workspace/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: success and `PASS style`.

- [ ] **Step 4: Commit**

```bash
git add skills/docs/SKILL.md skills/workspace/SKILL.md && git commit -m "docs skill - table, list, and paragraph rendering gotchas (Cluster C)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5 - New discoverability command (Cluster D1)

**Files:**
- Create: `skills/start/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `skills/start/SKILL.md` with this exact content:

```markdown
---
description: Orientation for Scribe - checks which Google accounts are authenticated and lists what the plugin can do. Run this first, or any time you want to see Scribe's workflows.
disable-model-invocation: true
argument-hint: ""
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
```

- [ ] **Step 2: Validate structure with make validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -n $'[–—]' skills/start/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: `make validate` reports the new skill is present and well-formed; `PASS style`.

- [ ] **Step 3: Deep-validate with the plugin-validator agent**

Dispatch the `plugin-dev:plugin-validator` agent against the repo, focused on the new `skills/start/SKILL.md`. Expected: no schema or frontmatter errors. Fix any it reports, then re-run.

- [ ] **Step 4: Commit**

```bash
git add skills/start/SKILL.md && git commit -m "start skill - /scribe:start discoverability command (Cluster D1)" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 5: Manual smoke (Julian)**

This step is Julian's, since it needs a plugin reload. Reload the plugin, run `/scribe:start` with no accounts authenticated (confirm it routes to auth-init) and with at least one account (confirm it lists accounts and the catalog). Note the result; no code change unless it misbehaves.

---

## Task 6 - Auth callback clarity and Windows ${HOME} handling (Cluster D2, part 1)

**Files:**
- Modify: `skills/auth-init/SKILL.md` (one line in section 6)
- Modify: `.claude-plugin/plugin.json` (only if the verification in Step 2 requires it)

- [ ] **Step 1: Add the callback-clarity line to auth-init**

In `skills/auth-init/SKILL.md`, section "## 6. Authenticate via Claude Code", find:

```markdown
The token is then written automatically to `~/.workspace-mcp/credentials/<email>.json`. The server uses it from this point forward without further prompts (the token auto-refreshes).
```

Replace with:

```markdown
The token is then written automatically to `~/.workspace-mcp/credentials/<email>.json`. The browser redirects back to the locally-running MCP server (started by the plugin manifest), which exchanges the code for the token; that is why the server must stay running until the success page appears. The server uses the token from this point forward without further prompts (the token auto-refreshes).
```

- [ ] **Step 2: Resolve the Windows `${HOME}` question before touching plugin.json**

`plugin.json` uses `${HOME}` in three env vars (`GOOGLE_CLIENT_SECRET_PATH`, `WORKSPACE_MCP_CREDENTIALS_DIR`, `ALLOWED_FILE_DIRS`). This works on macOS. The open question is whether Claude Code's plugin MCP launcher expands `${HOME}` on Windows. Do not guess.

Verify with the `claude-code-guide` agent (or current Claude Code plugin docs), asking specifically: "In a plugin `plugin.json` `mcpServers.<name>.env` value, what variable expansion does the launcher perform, and does `${HOME}` expand on Windows? What is the recommended cross-platform way to reference the user home directory?"

- [ ] **Step 3: Apply the manifest decision**

Pick the branch that matches the Step 2 finding. Both are fully specified; choose one.

Branch A - the launcher expands `${HOME}` cross-platform (including Windows). No manifest change. The existing Windows troubleshooting note in auth-init already covers the rare failure. Record the finding in a comment in this plan and move on.

Branch B - the launcher does NOT expand `${HOME}` on Windows. Do not break the working macOS config by swapping in something unverified. Instead, keep `${HOME}` and make the Windows override explicit and proactive. In `skills/auth-init/SKILL.md`, promote the existing Windows `${HOME}` note from "troubleshooting" to a first-class step in the install flow, with this content:

```markdown
**Windows users - set explicit paths.** Claude Code may not expand `${HOME}` on Windows. Before first run, add this to your project `.claude/settings.json` under `mcpServers.scribe.env`, replacing `C:\Users\YourName` with your home directory:

    "GOOGLE_CLIENT_SECRET_PATH": "C:\\Users\\YourName\\.workspace-mcp\\oauth_client.json",
    "WORKSPACE_MCP_CREDENTIALS_DIR": "C:\\Users\\YourName\\.workspace-mcp\\credentials",
    "ALLOWED_FILE_DIRS": "C:\\Users\\YourName\\.workspace-mcp\\attachments"
```

- [ ] **Step 4: Mark Windows as unverified-from-here**

Whichever branch was taken, the Windows behaviour was not tested on a Windows machine in this session. Add a one-line note in the commit body and tell Julian it needs his confirmation on Windows. Do not claim Windows is "fixed."

- [ ] **Step 5: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && python3 -c "import json;json.load(open('.claude-plugin/plugin.json'))" && echo "plugin.json OK" && grep -n $'[–—]' skills/auth-init/SKILL.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: `make validate` success, `plugin.json OK`, `PASS style`.

- [ ] **Step 6: Commit**

```bash
git add skills/auth-init/SKILL.md .claude-plugin/plugin.json && git commit -m "auth-init - callback clarity and Windows path handling (Cluster D2); Windows unverified, needs Julian to confirm" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7 - Archive the stale auth issues doc (Cluster D2, part 2)

**Files:**
- Move: `docs/issues/scribe-auth-init-issues.md` -> `docs/issues/legacy/scribe-auth-init-issues.md`
- Create: `docs/issues/legacy/README.md`

Note - `docs/issues/` is gitignored, so this is a local filesystem tidy, not a tracked change. It still follows Julian's archive-over-delete rule.

- [ ] **Step 1: Move the file**

```bash
cd /Users/juliandickie/code/scribe-plugin && mkdir -p docs/issues/legacy && git mv --force docs/issues/scribe-auth-init-issues.md docs/issues/legacy/scribe-auth-init-issues.md 2>/dev/null || mv docs/issues/scribe-auth-init-issues.md docs/issues/legacy/scribe-auth-init-issues.md
```
(The `git mv` will no-op to a plain `mv` because the path is gitignored; either way the file ends up in `legacy/`.)

- [ ] **Step 2: Create the legacy README**

Create `docs/issues/legacy/README.md`:

```markdown
# Legacy issues - archived

Resolved or superseded issue reports, kept for history (archive over delete).

- `scribe-auth-init-issues.md` - archived 2026-06-13. First-run auth-init failures reported against scribe 0.3.0 on Windows. The v1.0 auth-init rewrite resolved issues 1 through 9; issue 10 (callback server) is moot in the plugin-managed stdio flow; issue 11 (Windows `${HOME}`) is addressed in the 2026-06-13 accuracy-and-onboarding work (auth-init Windows note, pending Windows confirmation). No open items remain from this report.
```

- [ ] **Step 3: Verify**

```bash
cd /Users/juliandickie/code/scribe-plugin && ls docs/issues/legacy/ && test -f docs/issues/scribe-auth-init-issues.md && echo "STILL PRESENT - move failed" || echo "moved OK"
```
Expected: `legacy/` lists both files; prints `moved OK`.

- [ ] **Step 4: No commit needed**

`docs/issues/` is gitignored, so there is nothing to commit. Skip.

---

## Task 8 - Reflect current state in README and CLAUDE.md (no version bump)

**Files:**
- Modify: `README.md` (skill count and command list, wherever workflows/skills are enumerated)
- Modify: `CLAUDE.md` (skill count, repo structure skill list, writing-style rule 3)

- [ ] **Step 1: Update the CLAUDE.md skill count (three exact spots)**

Adding `start` makes the infra group 6 (auth-init, auth-add, auth-status, push, client-resolve, start) and the total 31. This also fixes a pre-existing inconsistency where the "Current state" line said "6 existing infra" while the total said 30.

Spot 1, the "What this project is" overview - change `30 skills` to `31 skills` and `5 existing infra skills` to `6 existing infra skills` in:

```
- 30 skills (`skills/<name>/SKILL.md`) organised in a three-layer architecture (orchestration router + 10 auto-activated service skills + 14 user-invokable workflow skills + 5 existing infra skills) that teach Claude when and how to use the MCP tools.
```

Spot 2, the "Current state" line - change `30` to `31`:

```
- **Skill count** - 30 (6 existing infra + 1 orchestration + 10 service + 14 workflow)
```

Spot 3, the architecture section header - change `(5)` to `(6)` and append `start`:

```
**Existing infra skills (5).** `auth-init`, `auth-add`, `auth-status`, `push`, `client-resolve` - unchanged from earlier versions.
```
becomes
```
**Existing infra skills (6).** `auth-init`, `auth-add`, `auth-status`, `push`, `client-resolve`, `start` - `start` is the discoverability command added in 1.1.0; the rest are unchanged.
```

Also add `start` to the repo-structure tree under the infra skills. The current tree ends the infra group with `client-resolve` on a `└──` line; change that to `├──` and add a final `└── start/SKILL.md  # Discoverability - /scribe:start`.

- [ ] **Step 2: Correct writing-style rule 3 in CLAUDE.md**

Find the rule 3 block under "Writing style rules":

```markdown
3. **Blank lines between list items**. When listing things in markdown, place a full blank line between each bullet so line breaks survive when content is pasted into external apps like Google Docs.
```

Replace with:

```markdown
3. **Blank lines for Google-Doc paragraph fidelity**. Markdown's single newline is a soft break, so lines collapse into one paragraph when converted into a Google Doc. When content is destined for a Google Doc, separate items with a blank line so each lands on its own paragraph, or use a real list marker (`- `) with a blank line before and after the list. This is not a blanket rule and not always about lists - it does not apply to SKILL.md files or local docs read as markdown, and the goal is not to force everything into structured lists. Use tight markdown in skill and local files.
```

- [ ] **Step 3: Update README**

README.md was not read during planning, so read it first to find the exact spots:

```bash
cd /Users/juliandickie/code/scribe-plugin && grep -nE '30|scribe:|workflow|skill' README.md
```

Then add `/scribe:start` wherever the commands or workflows are listed (as the orientation entry point), and update any stated skill count to 31. Keep the existing README structure and tone; this is a content sync per the "README reflects current state" rule, not a rewrite.

- [ ] **Step 4: Validate**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate && grep -rn $'[–—]' README.md CLAUDE.md && echo "FAIL dashes" || echo "PASS style"
```
Expected: success and `PASS style`.

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md && git commit -m "docs - reflect /scribe:start, corrected skill count (31), and writing-style rule 3" -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final verification (after all tasks)

- [ ] **Run the full validator**

```bash
cd /Users/juliandickie/code/scribe-plugin && make validate
```
Expected: all manifests parse, all skills present and well-formed.

- [ ] **Dispatch the plugin-validator agent** against the whole plugin. Expected: no errors. Fix and re-run if any.

- [ ] **Style sweep across all changed files**

```bash
cd /Users/juliandickie/code/scribe-plugin && grep -rn $'[–—]' skills/ README.md CLAUDE.md && echo "FAIL dashes" || echo "PASS no dashes" ; grep -rnE '^#+ .*:' skills/start/SKILL.md && echo "check heading colons" || echo "PASS no new heading colons"
```

- [ ] **Hand back to Julian** for the manual smokes that need a reload and auth - `/scribe:start` in both auth states (Task 5 Step 5), and the Windows `${HOME}` confirmation (Task 6 Step 4). These cannot be completed from a macOS session without a Windows machine and a reloaded plugin.

## Deferred to a separate, explicitly-approved step

- Version bump to 1.1.0 in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, and `make publish`. Not part of this plan (spec non-goal). Do it only when Julian approves a release.

- Wave 2 (cluster E) - error-recovery map, tool-index references file, service-skill description audit, and param trim across the other nine service skills. Its own plan, written after this wave lands.

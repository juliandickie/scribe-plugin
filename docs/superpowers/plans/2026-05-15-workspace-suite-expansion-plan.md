# Scribe v1.0 Full Workspace Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand Scribe from a Drive/Docs-focused plugin into a complete Google Workspace orchestration layer with 10 service skills, 14 workflow skills, a refactored orchestration router, and ship as v1.0.0 to the Claude Code plugin marketplace.

**Architecture:** Three-layer skill model. Layer 1 is `workspace/SKILL.md` as a broad-description orchestration router. Layer 2 is ten auto-activated service skills (one per Google service). Layer 3 is fourteen user-invokable workflow skills (`disable-model-invocation: true`). All powered by a single upstream `workspace-mcp@1.20.4` MCP server with the full `--tools` list enabled.

**Tech Stack:** Markdown skill prose with YAML frontmatter, JSON manifests (plugin.json, marketplace.json), Bash hooks, Makefile, GitHub releases via gh CLI. No application code - this is a configuration + prose plugin.

**Reference docs:**

- Spec - `/Users/juliandickie/code/scribe-plugin/docs/superpowers/specs/2026-05-15-workspace-suite-expansion-design.md`

- Current CLAUDE.md - `/Users/juliandickie/code/scribe-plugin/CLAUDE.md`

- Upstream tool docs - https://github.com/taylorwilsdon/google_workspace_mcp

---

## Phase 1 - Foundation

### Task 1: Branch and verify upstream pin

**Files:**

- Inspect: `.claude-plugin/plugin.json`

- Verify: PyPI for latest workspace-mcp version

- [ ] **Step 1: Create feature branch**

```bash
cd /Users/juliandickie/code/scribe-plugin
git checkout -b feature/v1-workspace-suite
git status
```

Expected: clean working tree, on `feature/v1-workspace-suite`.

- [ ] **Step 2: Check current upstream pin**

```bash
jq -r '.mcpServers.scribe.args[0]' .claude-plugin/plugin.json
```

Expected output: `workspace-mcp@1.20.4`

- [ ] **Step 3: Check latest PyPI version**

```bash
curl -s https://pypi.org/pypi/workspace-mcp/json | jq -r '.info.version'
```

If output equals `1.20.4`, no pin bump needed. If higher, note the new version - it will be used in Task 5 instead of 1.20.4 (update every reference from `1.20.4` to the new version throughout this plan).

- [ ] **Step 4: Commit the branch state (empty commit to mark start)**

```bash
git commit --allow-empty -m "Start v1.0 workspace suite expansion"
```

---

### Task 2: Update Makefile - add check-upstream target

**Files:**

- Modify: `Makefile`

- [ ] **Step 1: Add check-upstream target and update validate target**

Open `Makefile` and replace the existing `validate` target and add a new `check-upstream` target. The full updated targets:

```makefile
validate: ## Validate manifests parse and skill structure is intact
	@python3 -m json.tool .claude-plugin/plugin.json > /dev/null && echo "  plugin.json - valid JSON"
	@python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "  marketplace.json - valid JSON"
	@for skill in workspace auth-init auth-add auth-status push client-resolve \
	              gmail calendar sheets slides docs drive contacts tasks forms chat \
	              daily-briefing inbox-triage support-scan meeting-prep thread-to-doc \
	              client-digest weekly-wrap follow-up-tracker contact-onboard doc-chase \
	              attach-vault event-recap smart-reply educator-setup; do \
		test -f skills/$$skill/SKILL.md && echo "  skills/$$skill/SKILL.md - present" || (echo "  MISSING - skills/$$skill/SKILL.md"; exit 1); \
	done
	@grep -q "name" .claude-plugin/plugin.json && echo "  plugin name field - present"
	@grep -q "mcpServers" .claude-plugin/plugin.json && echo "  mcpServers - declared"

check-upstream: ## Compare pinned workspace-mcp version against latest PyPI release
	@current=$$(jq -r '.mcpServers.scribe.args[0]' .claude-plugin/plugin.json | sed 's/workspace-mcp@//'); \
	latest=$$(curl -s https://pypi.org/pypi/workspace-mcp/json | jq -r '.info.version'); \
	if [ "$$current" = "$$latest" ]; then \
		echo "PASS - current pin $$current matches latest PyPI release"; \
	else \
		echo "OUTDATED - current pin $$current, latest is $$latest"; \
		echo "Review changelog at https://github.com/taylorwilsdon/google_workspace_mcp/releases"; \
	fi
```

Also update the `.PHONY` line near the top of Makefile to include the new target:

```makefile
.PHONY: help validate publish icons clean release-notes orient check-upstream
```

- [ ] **Step 2: Verify Makefile syntax**

```bash
make help
```

Expected: list of targets including `check-upstream`. The `validate` target will FAIL at this point because the new skill directories don't exist yet - that is correct and expected.

- [ ] **Step 3: Verify check-upstream works**

```bash
make check-upstream
```

Expected: either "PASS - current pin 1.20.4 matches latest PyPI release" OR "OUTDATED - current pin 1.20.4, latest is X.Y.Z".

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "Add make check-upstream target; expand validate for v1 skill set"
```

---

### Task 3: Update plugin.json manifest

**Files:**

- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Rewrite plugin.json with full tool list, new description, new keywords, v1.0.0 version**

Replace the file's full contents:

```json
{
  "name": "scribe",
  "version": "1.0.0",
  "description": "Scribe - Google Workspace orchestration for Claude Code. Multi-account access to Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, and Chat. Ships 14 cross-service workflow commands plus 10 service skills. Wraps taylorwilsdon/google_workspace_mcp.",
  "author": {
    "name": "Julian Dickie",
    "url": "https://github.com/juliandickie"
  },
  "homepage": "https://github.com/juliandickie/scribe-plugin",
  "repository": "https://github.com/juliandickie/scribe-plugin",
  "license": "MIT",
  "keywords": [
    "google",
    "workspace",
    "drive",
    "docs",
    "gmail",
    "calendar",
    "sheets",
    "slides",
    "contacts",
    "tasks",
    "forms",
    "chat",
    "workflows",
    "automation",
    "mcp",
    "oauth",
    "scribe"
  ],
  "icon": "docs/images/icon.png",
  "mcpServers": {
    "scribe": {
      "command": "uvx",
      "args": [
        "workspace-mcp@1.20.4",
        "--tools",
        "appscript",
        "calendar",
        "chat",
        "contacts",
        "docs",
        "drive",
        "forms",
        "gmail",
        "search",
        "sheets",
        "slides",
        "tasks"
      ],
      "env": {
        "GOOGLE_CLIENT_SECRET_PATH": "${HOME}/.workspace-mcp/oauth_client.json",
        "WORKSPACE_MCP_CREDENTIALS_DIR": "${HOME}/.workspace-mcp/credentials",
        "ALLOWED_FILE_DIRS": "${HOME}/.workspace-mcp/attachments"
      }
    }
  }
}
```

- [ ] **Step 2: Validate JSON parses**

```bash
python3 -m json.tool .claude-plugin/plugin.json > /dev/null && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Verify tools array length is 12**

```bash
jq '.mcpServers.scribe.args | map(select(. != "workspace-mcp@1.20.4" and . != "--tools")) | length' .claude-plugin/plugin.json
```

Expected: `12`

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "plugin.json - enable all 12 workspace-mcp tool groups, bump to v1.0.0"
```

---

### Task 4: Update marketplace.json

**Files:**

- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update version and description fields**

Replace the file's full contents:

```json
{
  "name": "scribe-marketplace",
  "description": "Scribe - Google Workspace orchestration for Claude Code. Multi-account access to the full Workspace suite with 14 named cross-service workflows.",
  "owner": {
    "name": "Julian Dickie",
    "url": "https://github.com/juliandickie"
  },
  "plugins": [
    {
      "name": "scribe",
      "description": "Google Workspace orchestration for Claude Code. Multi-account access to Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, and Chat. Ships 14 cross-service workflow commands plus 10 service skills. Wraps taylorwilsdon/google_workspace_mcp.",
      "version": "1.0.0",
      "source": "./",
      "author": {
        "name": "Julian Dickie",
        "url": "https://github.com/juliandickie"
      },
      "homepage": "https://github.com/juliandickie/scribe-plugin",
      "license": "MIT",
      "keywords": [
        "google",
        "workspace",
        "drive",
        "docs",
        "gmail",
        "calendar",
        "sheets",
        "slides",
        "contacts",
        "tasks",
        "forms",
        "chat",
        "workflows",
        "automation",
        "mcp",
        "oauth",
        "scribe"
      ],
      "icon": "docs/images/icon.png"
    }
  ]
}
```

- [ ] **Step 2: Validate JSON parses**

```bash
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "marketplace.json - v1.0.0, updated description and keywords"
```

---

### Task 5: Update hooks/post-install.sh pin reference

**Files:**

- Modify: `hooks/post-install.sh`

- [ ] **Step 1: Read current file**

```bash
cat hooks/post-install.sh
```

- [ ] **Step 2: Update the WORKSPACE_MCP_VERSION assignment**

Find the line that reads `WORKSPACE_MCP_VERSION="1.20.4"` (or similar) and confirm it matches the pin in `plugin.json`. If the PyPI check in Task 1 Step 3 revealed a newer version, update both `plugin.json` and this file to the new version. Otherwise, the line is already correct - skip to Step 3.

- [ ] **Step 3: Commit if changed**

```bash
git status hooks/post-install.sh
# If modified:
git add hooks/post-install.sh
git commit -m "hooks/post-install.sh - sync pin reference"
# Otherwise:
echo "No change needed"
```

---

### Task 6: Update auth-init/SKILL.md

**Files:**

- Modify: `skills/auth-init/SKILL.md`

- [ ] **Step 1: Replace Section 2 (Enable required APIs) with expanded list**

Locate the section that begins `## 2. Enable required APIs` and replace it with:

```markdown
## 2. Enable required APIs

Under **APIs & Services > Library**, enable the APIs the user needs. For the full Scribe suite, enable all of these. For a minimal install, enable only the first two and add the others later as the workflows you want require them.

**Required (mandatory for the plugin to start):**

- **Google Drive API**

- **Google Docs API**

**Strongly recommended (most workflow skills depend on these):**

- **Gmail API**

- **Google Calendar API**

- **Google Sheets API**

- **Google Slides API**

**Optional (enable to unlock specific workflows):**

- **People API** (Contacts)

- **Google Tasks API**

- **Google Forms API**

- **Google Chat API**

- **Apps Script API** (advanced - rarely needed)

The plugin's MCP server requests scopes for all enabled APIs on first OAuth. If a user later sees a "Scope not authorized" error for a specific service, they need to enable that API in Cloud Console and re-run `start_google_auth` for that service.
```

- [ ] **Step 2: Replace Section 6's service_name guidance**

Find the bullet near the end of Section 6 that reads `service_name - use "drive"...` and update to:

```markdown
- `service_name` - use `"drive"` for the initial setup. This authorises the default scope set the server requests, which covers Drive, Docs, Gmail, Calendar, Sheets, Slides, and most other services in one consent flow. If you later see a "Scope not authorized" error for a specific service, re-run `start_google_auth` with that service name (e.g. `"contacts"`, `"tasks"`, `"forms"`, `"chat"`).
```

Also update the Troubleshooting bullet for "Missing required argument: service_name" to read:

```markdown
- "Missing required argument: service_name" - the `start_google_auth` tool requires both `user_google_email` and `service_name`. Valid values include `drive`, `docs`, `gmail`, `calendar`, `sheets`, `slides`, `contacts`, `tasks`, `forms`, `chat`. Use `drive` for the initial setup; it covers the broad scope set.
```

- [ ] **Step 3: Append a new "Restricting scopes (advanced)" section after the existing Troubleshooting section**

Add this section at the end of the file:

```markdown
## Restricting scopes (advanced)

By default the plugin enables all 12 tool groups and the OAuth consent screen requests scopes for each. Users who want narrower OAuth scopes can override `--tools` with `--permissions` in their per-project `.claude/settings.json` MCP env config:

```json
{
  "mcpServers": {
    "scribe": {
      "args": [
        "workspace-mcp@1.20.4",
        "--permissions", "gmail:readonly", "drive:full", "docs:full"
      ]
    }
  }
}
```

Gmail permission levels are cumulative - `readonly` < `organize` < `drafts` < `send` < `full`. Other services accept `readonly` or `full`.

If you switch from `--tools` to `--permissions`, re-run `start_google_auth` so the consent screen reflects the narrower scope set.
```

- [ ] **Step 4: Verify the file still under 500 lines and frontmatter parses**

```bash
wc -l skills/auth-init/SKILL.md
head -5 skills/auth-init/SKILL.md | grep -E "^description|^disable-model"
```

Expected: line count under 500, frontmatter fields visible.

- [ ] **Step 5: Commit**

```bash
git add skills/auth-init/SKILL.md
git commit -m "auth-init - document full API enablement and --permissions override"
```

---

### Task 7: Update auth-add/SKILL.md service_name guidance

**Files:**

- Modify: `skills/auth-add/SKILL.md`

- [ ] **Step 1: Update the service_name bullet**

Find the bullet that reads `service_name - use "drive"...` and replace with the same text used in Task 6 Step 2.

- [ ] **Step 2: Commit**

```bash
git add skills/auth-add/SKILL.md
git commit -m "auth-add - update service_name guidance to reflect full suite"
```

---

### Task 8: Update CLAUDE.md

**Files:**

- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the "Current state" section**

Find the `## Current state - as of YYYY-MM-DD` block and replace its bullets with:

```markdown
- **Plugin version** - 1.0.0 (in plugin.json + marketplace.json)
- **Pinned upstream version** - `workspace-mcp@1.20.4` from PyPI
- **Distribution** - GitHub at `juliandickie/scribe-plugin`, public, MIT licensed, with v1.0.0 release tagged
- **Marketplace install** - `/plugin marketplace add juliandickie/scribe-plugin` then `/plugin install scribe`
- **Direct download** - `https://github.com/juliandickie/scribe-plugin/archive/refs/tags/v1.0.0.zip`
- **Skill count** - 30 (6 existing infra + 1 orchestration + 10 service + 14 workflow)
- **Tools enabled** - all 12 workspace-mcp tool groups
```

And update the section heading to `## Current state - as of 2026-05-15` (use the date of the implementation, not the original spec date).

- [ ] **Step 2: Replace the "Skills - the modern shape" section**

Find the heading `## Skills - the modern shape` and replace the entire section with:

```markdown
## Skills - the three-layer architecture

Scribe v1.0 uses a three-layer skill model.

**Layer 1 - Orchestration (auto-activated, broad description).**

- `workspace/SKILL.md` - the routing brain. Multi-account selection rules, cross-service chaining patterns, cross-plugin composition hints, setup precondition checks. Loads on every Workspace-context turn. Does NOT contain per-service tool details.

**Layer 2 - Service skills (10 auto-activated, narrow descriptions).**

- `docs/SKILL.md` - Google Docs (tabs, batch updates, find/replace, structure inspection)

- `drive/SKILL.md` - Drive (folders, files, sharing, permissions, public access)

- `gmail/SKILL.md` - Gmail (search, threads, drafts, send, labels, batch ops)

- `calendar/SKILL.md` - Calendar (events, free/busy, OOO, focus time, calendars)

- `sheets/SKILL.md` - Sheets (ranges, formulas, table creation, append rows)

- `slides/SKILL.md` - Slides (read, create, update slide content, layouts)

- `contacts/SKILL.md` - Contacts (read, create, search via People API)

- `tasks/SKILL.md` - Tasks (read, create, complete, task lists)

- `forms/SKILL.md` - Forms (read responses, create forms, analytics)

- `chat/SKILL.md` - Google Chat (send messages, read spaces)

Each service skill loads only when its specific service is in scope (description-as-trigger rule). Each contains MCP tool API details for that service.

**Layer 3 - Workflow skills (14 user-invokable, disable-model-invocation).**

User-invokable slash commands for named cross-service patterns:

- `/scribe:daily-briefing`, `/scribe:inbox-triage`, `/scribe:support-scan`

- `/scribe:meeting-prep`, `/scribe:thread-to-doc`, `/scribe:client-digest`

- `/scribe:weekly-wrap`, `/scribe:follow-up-tracker`, `/scribe:contact-onboard`

- `/scribe:doc-chase`, `/scribe:attach-vault`, `/scribe:event-recap`

- `/scribe:smart-reply`, `/scribe:educator-setup`

Each workflow skill is a complete recipe for a multi-service tool chain. See `docs/workflows.md` for detailed reference.

**Existing infra skills (5).** `auth-init`, `auth-add`, `auth-status`, `push`, `client-resolve` - unchanged from earlier versions.
```

- [ ] **Step 3: Add a new "Cross-plugin composition" subsection under "Important conventions and gotchas"**

Find the heading `## Important conventions and gotchas` and add this new subsection at the end of that section (before the next `## ` heading):

```markdown
### Cross-plugin composition

Scribe never directly calls other plugins' MCP tools or APIs. Cross-plugin orchestration happens through prose hints in workflow skills - e.g. "if the ClickUp plugin is installed, also create a ClickUp task with the email URL." Claude reads the hint, sees the ClickUp plugin's tools are available, and chains the call.

This pattern keeps Scribe decoupled from other plugins' versions. Never add direct tool references like `mcp__clickup__create_task` into Scribe skill prose; reference plugins by their user-facing names ("ClickUp plugin", "Slack plugin") so the prose is robust to plugin renames.

For dedicated multi-plugin workflows, the right place is a separate meta-orchestration plugin - see `/Users/juliandickie/code/plugin-dev/docs/2026-05-15-meta-orchestrator-concept.md`.
```

- [ ] **Step 4: Add a "Future work" section to CLAUDE.md**

Add a new top-level section at the end of the file:

```markdown
## Future work

Items flagged during the v1.0 design conversation that are not in v1.0 scope. Full context in the spec at `docs/superpowers/specs/2026-05-15-workspace-suite-expansion-design.md`.

- **Meta-orchestration plugin** - separate plugin composing Scribe + ClickUp + Spiffy + AC Builder + Slack into cross-system workflows. Concept doc at `/Users/juliandickie/code/plugin-dev/docs/2026-05-15-meta-orchestrator-concept.md`.

- **Per-skill telemetry** - count workflow invocations to inform v1.1 priorities. Requires opt-in instrumentation.

- **Workflow templates as upstream feature** - propose to taylorwilsdon as a workspace-mcp capability if the workflow pattern proves broadly useful.

- **`--permissions` granular control as setup option** - in v1.0 documented as advanced override only. v1.1 could add a `/scribe:permissions` command for interactive setup.

- **AppScript and Search service skills** - tools enabled at manifest level but no dedicated service skill yet. Add in v1.1 if usage warrants.

- **Optional GitHub Actions weekly upstream-check** - `make check-upstream` covers manual cadence; automation deferred.
```

- [ ] **Step 5: Update the "Don't do this" section**

Find the `## Don't do this` heading and add a new bullet at the end of the existing list:

```markdown
- Don't bundle other plugins' MCP tools into Scribe. Cross-plugin chaining happens via prose hints and Claude's natural skill composition, not by importing or invoking other plugins' tool namespaces directly. If a workflow needs ClickUp/Slack/etc., reference those plugins by name in the prose, never call their tools directly.
```

- [ ] **Step 6: Verify and commit**

```bash
wc -l CLAUDE.md
git add CLAUDE.md
git commit -m "CLAUDE.md - v1.0 three-layer architecture, future work, cross-plugin pattern"
```

---

### Task 9: Refactor workspace/SKILL.md as orchestration router

**Files:**

- Modify (rewrite): `skills/workspace/SKILL.md`

- [ ] **Step 1: Replace the file's full contents**

```markdown
---
description: Use when a user request mentions Google Workspace - any Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, or Chat operation. Also triggers on multi-service or multi-account requests, document URLs, folder IDs, and natural phrases like "across my accounts," "in my Drive," "from my inbox." Routes work to service-specific skills and workflow skills.
last-validated: 2026-05-15
---

# Scribe - Workspace orchestration router

This skill is the routing brain for Scribe. It loads on every Workspace-context turn and teaches Claude how to think about routing, multi-account selection, cross-service chaining, and cross-plugin composition. It does NOT contain per-service MCP tool details - those live in the ten service skills which auto-activate alongside this one.

## Multi-account routing rules

Scribe supports multiple authenticated Google accounts. Pass `user_google_email` on every MCP tool call to select the account. The selection logic:

1. **Explicit user mention wins.** "Use julian@idd to..." or "for my Pro Marketing account" - use that one.

2. **Explicit multi-account intent triggers auto-loop.** "Check both my inboxes," "across all my accounts," "for julian@idd and julian@pro" - call `list_authenticated_accounts`, then iterate, accumulating results. Do NOT prompt for confirmation when intent is this explicit.

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

1. Calendar - `get_events` for the window, `manage_event` if listing free/busy.

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

## Setup precondition check

Before any MCP tool call, if you have any doubt the user has set up OAuth, call `list_authenticated_accounts`. If it returns empty, do NOT attempt other tool calls - they will fail with confusing token errors. Instead direct the user to `/scribe:auth-init`.

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
```

- [ ] **Step 2: Verify line count and frontmatter**

```bash
wc -l skills/workspace/SKILL.md
head -5 skills/workspace/SKILL.md
```

Expected: under 250 lines, frontmatter has `description` and `last-validated`.

- [ ] **Step 3: Commit**

```bash
git add skills/workspace/SKILL.md
git commit -m "workspace/SKILL.md - refactor as orchestration router for v1.0"
```

---

### Task 10: Create service skill template

**Files:**

- Create: `docs/skill-templates/service-skill-template.md`

This template is a reference for Tasks 12-21. It is not loaded as a skill (it lives under `docs/`, not `skills/`).

- [ ] **Step 1: Create the templates directory and file**

```bash
mkdir -p docs/skill-templates
```

Then create `docs/skill-templates/service-skill-template.md` with this content:

```markdown
---
description: {Trigger phrase a user would type, naming this service's specific nouns. Must be distinct from other service skills. Max 1024 chars. Use service-specific verbs like "search Gmail," "list events," "read spreadsheet rows."}
last-validated: 2026-05-15
---

# Scribe - {Service name}

{One sentence describing what this skill enables.}

## When to use

Use this skill when the user's request involves -

- {Specific user-facing scenario 1}

- {Specific user-facing scenario 2}

- {Specific user-facing scenario 3}

## MCP tool reference

The following tools are exposed by workspace-mcp for {service}. Pass `user_google_email` on every call (see workspace/SKILL.md for account selection rules).

### {tool_name_1}

{One-line purpose.}

Parameters:

- `param1` - {description}

- `param2` - {description, mark optional if so}

Returns: {return shape summary}

### {tool_name_2}

{...repeat for each tool the service exposes...}

## Common patterns

### {Pattern name 1}

1. {First tool call with parameters}

2. {Second tool call with parameters}

3. {Outcome}

### {Pattern name 2}

{...}

## Gotchas

- {Service-specific quirk 1, e.g. timezone handling, ID vs name distinction, pagination behaviour}

- {Service-specific quirk 2}

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing." Quick reference:

- Explicit user mention - use it

- Multi-account intent ("both inboxes," "all accounts") - auto-loop

- Client context - check profile.md or Contacts

- Single authenticated account - use it

- Ambiguous + multiple accounts - prompt once

## Cross-service handoff

When a request spans services, this skill's role ends after the {service} operation. The orchestration layer in workspace/SKILL.md handles chaining to other services.

## Source

This skill wraps `workspace-mcp` tools for {service}. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.
```

- [ ] **Step 2: Commit**

```bash
git add docs/skill-templates/service-skill-template.md
git commit -m "docs - add service skill template for v1 expansion"
```

---

### Task 11: Create workflow skill template

**Files:**

- Create: `docs/skill-templates/workflow-skill-template.md`

- [ ] **Step 1: Create the file**

```markdown
---
description: {Trigger phrase a user would actually type for this workflow. Must be specific. Max 1024 chars. Example - "Scan support inbox for new inquiries, log to a tracking sheet, draft responses."}
disable-model-invocation: true
argument-hint: {Argument signature. Single positional - "<contact-or-email>". Multi-arg - "[--account email] [--client CLIENT-ID] [--since 7d]". Empty if no args.}
last-validated: 2026-05-15
---

# Scribe - {Workflow name}

{One-paragraph description of what this workflow does and why a user would invoke it.}

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `{param1}` (optional) - {description, default if omitted}

- `{param2}` (optional) - {description, default if omitted}

If a parameter is missing and required for the workflow to proceed, ask the user once.

## Tool call sequence

1. **{Step name}** - {service} - call {tool_name} with `param1=X, param2=Y`. Why: {rationale}.

2. **{Step name}** - {service} - call {tool_name} with `param1=X`. Use the result from step 1's `field_name`.

3. **{Step name}** - {service} - call {tool_name}. {Note about parameter sourcing.}

4. **Summary** - return the resulting URL/ID and a one-line summary to the user.

## Multi-account behaviour

{One of:}

- This workflow operates on a single account. Resolve via the rules in workspace/SKILL.md.

- This workflow loops across all authenticated accounts when intent is explicit ("check both inboxes"). Otherwise uses the resolved single account.

## Cross-plugin composition

After the Scribe tool chain completes, check whether these plugins are installed and chain accordingly:

- **ClickUp plugin** - {what to do, e.g. "create a follow-up task with the doc URL in the list named X"}

- **Slack plugin** - {what to do, e.g. "post a one-line summary to channel Y"}

- **Spiffy plugin** - {what to do, omit if not relevant}

- **AC Builder plugin** - {what to do, omit if not relevant}

If a referenced plugin is not available, skip its step silently and note it in the final summary ("Posted to Drive; ClickUp plugin not installed, no task created").

## Example invocations

Natural language:

- "{Natural phrase 1}"

- "{Natural phrase 2}"

Explicit args:

- `/scribe:{workflow-slug} {example-arg-string}`

## Failure modes

- **No matching {data, e.g. emails}** - {what to do}

- **No accounts authenticated** - direct to `/scribe:auth-init`

- **Sandbox rejection on file copy** - link the user to push/SKILL.md sandbox section

- **Permission scope error** - tell the user which API they need to enable in Cloud Console

## Output

Always return:

- A short one-line summary of what happened

- URLs/IDs of any artifacts created (Doc URL, Sheet URL, draft IDs)

- A note for any cross-plugin steps that were skipped
```

- [ ] **Step 2: Commit**

```bash
git add docs/skill-templates/workflow-skill-template.md
git commit -m "docs - add workflow skill template for v1 expansion"
```

---

## Phase 2 - Service skills (Tasks 12-21)

Each service skill task creates a new directory under `skills/` with a `SKILL.md` derived from the service-skill-template (Task 10). The general process:

1. Copy template to `skills/{service}/SKILL.md`

2. Fill in the placeholders with the service-specific values listed in the task

3. Validate frontmatter + line count

4. Commit

For each task below, the per-service values are given. The executor copies the template and substitutes them.

---

### Task 12: gmail/SKILL.md

**Files:**

- Create: `skills/gmail/SKILL.md`

- [ ] **Step 1: Create the directory and file**

```bash
mkdir -p skills/gmail
cp docs/skill-templates/service-skill-template.md skills/gmail/SKILL.md
```

- [ ] **Step 2: Edit skills/gmail/SKILL.md with these substitutions**

Replace the placeholders with the following service-specific content:

- **description** - `Use when the user's request involves Gmail - reading emails, searching threads, sending or drafting messages, managing labels, batch label modifications, or any inbox operation. Triggers on words like email, inbox, message, thread, label, draft, send, reply, forward, archive.`

- **{Service name}** - `Gmail`

- **What this skill does (one sentence)** - `Enables Claude to read, search, draft, send, and organise Gmail messages and threads through the workspace-mcp server.`

- **When to use bullets**:

  - Reading or searching emails by sender, subject, date, label, or content

  - Drafting, sending, or scheduling email replies and new messages

  - Managing labels, applying or removing labels in bulk

  - Filtering or organising the inbox

  - Reading attachments from a message

- **Tool reference** - include each of these with parameters and return shape:

  - `search_gmail_messages` - search Gmail with Gmail query syntax (`from:`, `subject:`, `is:unread`, etc.). Params - `query`, `user_google_email`, optional `max_results`. Returns - list of message metadata.

  - `get_gmail_message_content` - fetch full content of one message by ID. Params - `message_id`, `user_google_email`.

  - `get_gmail_messages_content_batch` - batch fetch multiple messages. Params - `message_ids[]`, `user_google_email`.

  - `get_gmail_thread_content` - fetch all messages in a thread. Params - `thread_id`, `user_google_email`.

  - `get_gmail_threads_content_batch` - batch fetch multiple threads.

  - `search_gmail_threads` - thread-level search. Params - `query`, `user_google_email`.

  - `get_gmail_attachment_content` - download attachment content. Params - `message_id`, `attachment_id`, `user_google_email`.

  - `send_gmail_message` - send a new message. Params - `to`, `subject`, `body`, optional `cc`, `bcc`, `user_google_email`.

  - `draft_gmail_message` - create a draft. Same params as send.

  - `modify_gmail_message_labels` - apply/remove labels. Params - `message_id`, `add_labels[]`, `remove_labels[]`, `user_google_email`.

  - `batch_modify_gmail_message_labels` - bulk label changes.

  - `list_gmail_labels` - list available labels.

  - `manage_gmail_label` - create, update, or delete labels.

  - `list_gmail_filters` - list current Gmail filters.

  - `manage_gmail_filter` - create or delete filters.

- **Common patterns** - include these 3:

  - **Find recent unread from sender** - `search_gmail_messages` with `query="from:sender@x.com is:unread newer_than:7d"`, then `get_gmail_thread_content` for each result.

  - **Draft a reply** - `get_gmail_message_content` to read the original, then `draft_gmail_message` with `to`/`subject`/`body` from context. Always draft, never send unprompted.

  - **Bulk archive read promotions** - `search_gmail_messages` with `query="label:promotions is:read"`, collect IDs, then `batch_modify_gmail_message_labels` with `remove_labels=["INBOX"]`.

- **Gotchas**:

  - Gmail query syntax is its own DSL. Use `is:unread`, `from:`, `to:`, `subject:`, `newer_than:7d`, `has:attachment`. Don't try SQL.

  - Label IDs and label names are different. `INBOX` is a system label; user labels have format `Label_XXXX`. `list_gmail_labels` shows both.

  - Sending requires `gmail:send` scope. If you see permission errors on send/draft, the user authenticated with a narrower scope set.

  - Batch operations return per-item success/failure. Always check the response for partial failures.

  - Email body can be plain text or HTML. Detect by content; the tool accepts either via `body` param.

- [ ] **Step 3: Verify line count under 500 and frontmatter parses**

```bash
wc -l skills/gmail/SKILL.md
head -5 skills/gmail/SKILL.md
```

- [ ] **Step 4: Commit**

```bash
git add skills/gmail/SKILL.md
git commit -m "Add gmail service skill"
```

---

### Task 13: calendar/SKILL.md

**Files:**

- Create: `skills/calendar/SKILL.md`

- [ ] **Step 1: Create directory and file from template, then substitute**

```bash
mkdir -p skills/calendar
cp docs/skill-templates/service-skill-template.md skills/calendar/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Calendar - reading events, creating meetings, checking availability, managing focus time or out-of-office, listing calendars, or any scheduling operation. Triggers on calendar, event, meeting, schedule, availability, free/busy, OOO, focus time.`

- **Service name** - `Calendar`

- **What this skill does** - `Enables Claude to read, create, update, and reason about Google Calendar events across one or more authenticated accounts.`

- **When to use bullets**:

  - Reading today's, upcoming, or past calendar events

  - Creating new events or meetings

  - Checking free/busy across attendees

  - Managing focus time blocks or out-of-office responder

  - Listing or describing calendars the user has access to

- **Tool reference**:

  - `get_events` - list events from a calendar. Params - `calendar_id` (use `"primary"` for default), `time_min`, `time_max` (RFC 3339), optional `max_results`, `user_google_email`.

  - `manage_event` - create, update, or delete an event. Params - `action` (`create`/`update`/`delete`), `event_id` (for update/delete), event fields (`summary`, `start`, `end`, `attendees`, `description`, etc), `calendar_id`, `user_google_email`.

  - `query_freebusy` - check availability across calendars. Params - `time_min`, `time_max`, `calendar_ids[]`, `user_google_email`.

  - `list_calendars` - enumerate calendars the user can read. Params - `user_google_email`.

  - `create_calendar` - create a new calendar. Params - `summary`, `description`, `user_google_email`.

  - `manage_focus_time` - read or manage focus time blocks. Params - `action`, `start`, `end`, `user_google_email`.

  - `manage_out_of_office` - read or set OOO auto-reply.

- **Common patterns**:

  - **Today's agenda** - `get_events` with `calendar_id="primary"`, `time_min=<today 00:00>`, `time_max=<today 23:59>` in the user's timezone.

  - **Schedule a meeting respecting availability** - `query_freebusy` with attendees' calendars first, then `manage_event` `action="create"` for a slot all attendees are free.

  - **Multi-account day view** - call `list_authenticated_accounts`, then `get_events` per account, merge results sorted by start time.

- **Gotchas**:

  - All event times use RFC 3339 with timezone (e.g. `2026-05-15T09:00:00+10:00` for Brisbane). The server does NOT auto-handle naive datetimes - always pass timezone.

  - `calendar_id="primary"` is the user's main calendar. Other calendars need their full ID, get them via `list_calendars`.

  - Recurring events return one entry per occurrence within the time range, not one master entry.

  - `query_freebusy` returns busy intervals, not free intervals. Compute free = window minus busy.

  - Attendees added in `manage_event` get an automatic invite email. To suppress, the upstream tool may have a flag; check current docs.

- [ ] **Step 2: Validate**

```bash
wc -l skills/calendar/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/calendar/SKILL.md
git commit -m "Add calendar service skill"
```

---

### Task 14: docs/SKILL.md

**Files:**

- Create: `skills/docs/SKILL.md`

- [ ] **Step 1: Create from template with substitutions**

```bash
mkdir -p skills/docs
cp docs/skill-templates/service-skill-template.md skills/docs/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Docs - reading or updating document content, working with specific tabs, batch updates, find-and-replace, headers/footers, or document structure. Triggers on Google Doc, document, doc tab, tab structure, find and replace, doc URL.`

- **Service name** - `Docs`

- **What this skill does** - `Enables Claude to read, write, and structure Google Docs - including the tabbed document model and high-fidelity markdown-to-Docs writing.`

- **When to use bullets**:

  - Reading the content of a specific Google Doc (full or single tab)

  - Pushing markdown content into a Doc or a specific tab

  - Performing find-and-replace operations across a Doc

  - Inspecting tab structure or managing tabs (create, rename, delete, populate)

  - Updating headers, footers, or paragraph styles

- **Tool reference**:

  - `get_doc_content` - read full doc text. Params - `document_id`, `user_google_email`.

  - `get_doc_as_markdown` - read doc as markdown. Params - `document_id`, `user_google_email`.

  - `inspect_doc_structure` - enumerate tabs, headings, structure. Params - `document_id`, `user_google_email`.

  - `manage_doc_tab` - create, rename, delete, populate_from_markdown a tab. Params - `action`, `document_id`, `tab_id` (for actions other than create), `title`, `markdown_text`, `index`, `replace_existing`, `user_google_email`.

  - `create_doc` - create a new doc. Params - `title`, optional `parent_folder_id`, `user_google_email`.

  - `import_to_google_doc` - convert and import a local file. Params - `file_path` (sandbox-bound), `source_format` (`md`, `txt`, `html`, `docx`, etc.), `parent_folder_id`, `user_google_email`.

  - `batch_update_doc` - apply multiple operations in one call. Params - `document_id`, `requests[]`, `user_google_email`.

  - `find_and_replace_doc` - replace text occurrences. Params - `document_id`, `find_text`, `replace_text`, optional `tab_id`, `user_google_email`.

  - `modify_doc_text` - direct text modifications.

  - `insert_doc_elements` - insert structural elements.

  - `insert_doc_image` - insert an image.

  - `create_table_with_data` - create a table populated from a 2D array.

  - `update_paragraph_style` - apply paragraph styling.

  - `update_doc_headers_footers` - manage headers and footers.

  - `manage_document_comment` - read/manage comments on a doc.

  - `list_document_comments` - list comments on a doc.

  - `export_doc_to_pdf` - export to PDF.

  - `debug_docs_runtime_info` / `debug_table_structure` - diagnostics.

- **Common patterns**:

  - **Update a specific tab from markdown** - `inspect_doc_structure` to find tab_id by title, then `manage_doc_tab` with `action="populate_from_markdown"`, `replace_existing=true`.

  - **Create a new tab and populate it** - `manage_doc_tab action="create"` returns new tab_id, then call again with `action="populate_from_markdown"`.

  - **Bulk find/replace** - `find_and_replace_doc` once per term, or batch via `batch_update_doc` for atomic application.

- **Gotchas**:

  - Docs use a tab structure now. A doc without explicit tabs has a single default tab; tab_id is still needed for manage_doc_tab calls.

  - `inspect_doc_structure` is the source of truth for tab IDs - don't guess.

  - `import_to_google_doc` uses the sandbox at `~/.workspace-mcp/attachments`. Files outside fail. See push/SKILL.md for auto-copy pattern.

  - `populate_from_markdown` with `replace_existing=true` wipes the tab before writing. With false it appends.

  - `batch_update_doc` is atomic - if any operation fails, none are applied. Use for invariant-critical updates.

- [ ] **Step 2: Validate**

```bash
wc -l skills/docs/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/docs/SKILL.md
git commit -m "Add docs service skill"
```

---

### Task 15: drive/SKILL.md

**Files:**

- Create: `skills/drive/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/drive
cp docs/skill-templates/service-skill-template.md skills/drive/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Drive - folders, files, file uploads, file sharing, permissions, public access checks, or any Drive content operation. Triggers on Drive, folder, file, upload, share, permissions, Drive URL, file ID.`

- **Service name** - `Drive`

- **What this skill does** - `Enables Claude to read, organise, share, and upload files in Google Drive - including folder structure management and permission controls.`

- **When to use bullets**:

  - Creating, copying, moving, or listing files and folders

  - Uploading files from the local sandbox

  - Sharing files with specific people or making them public

  - Checking file permissions or public-access status

  - Searching Drive by name, type, owner, or content

- **Tool reference**:

  - `search_drive_files` - search by query. Params - `query` (Drive query syntax like `name contains 'X' and mimeType = 'application/vnd.google-apps.folder'`), `user_google_email`.

  - `list_drive_items` - list contents of a folder. Params - `folder_id`, `user_google_email`, optional pagination.

  - `list_docs_in_folder` - convenience - list Docs in a folder.

  - `get_drive_file_content` - read file content for supported types.

  - `get_drive_file_download_url` - get a download URL.

  - `read_file_content` / `download_file_content` - lower-level reads.

  - `create_drive_folder` - create a folder. Params - `name`, `parent_folder_id`, `user_google_email`.

  - `create_drive_file` - create a Drive file from content.

  - `copy_drive_file` - copy a file. Params - `file_id`, `destination_folder_id`, optional `new_name`.

  - `update_drive_file` - update file metadata.

  - `manage_drive_access` - share with users or groups. Params - `file_id`, `email`, `role` (`reader`/`writer`/`commenter`/`owner`), optional `send_notification`.

  - `set_drive_file_permissions` - set or modify permissions.

  - `get_drive_file_permissions` / `check_drive_file_public_access` - read permissions.

  - `get_drive_shareable_link` - get a shareable URL.

  - `get_file_metadata` / `get_file_permissions` - inspect metadata.

  - `search_files` / `list_recent_files` - search variants.

- **Common patterns**:

  - **Bootstrap a client folder** - `create_drive_folder` for the parent, then 3-4 calls for subfolders (curriculum, planning, etc).

  - **Find a folder by name** - `search_drive_files` with `query="name = 'X' and mimeType = 'application/vnd.google-apps.folder'"`, take first result.

  - **Share a doc for review** - `manage_drive_access` with `email`, `role="commenter"`, `send_notification=true`.

  - **Audit a folder's external sharing** - `list_drive_items`, then per-file `get_drive_file_permissions`, surface anything shared externally.

- **Gotchas**:

  - Drive uses MIME types for file kinds. `application/vnd.google-apps.folder` is a folder; `application/vnd.google-apps.document` is a Google Doc; `application/vnd.google-apps.spreadsheet` is a Sheet; etc.

  - Folder IDs and file IDs look identical from the URL. Both are random strings.

  - Permission changes can take seconds to propagate; if a follow-up call fails, retry once.

  - `search_drive_files` requires Drive query syntax (different from Gmail query). See https://developers.google.com/drive/api/guides/search-files.

  - The Shared Drive distinction matters - files in Shared Drives have a `driveId` and different sharing semantics from My Drive files.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/drive/SKILL.md
git add skills/drive/SKILL.md
git commit -m "Add drive service skill"
```

---

### Task 16: sheets/SKILL.md

**Files:**

- Create: `skills/sheets/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/sheets
cp docs/skill-templates/service-skill-template.md skills/sheets/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Sheets - reading cell values, writing data, appending rows, working with ranges in A1 notation, formulas, or creating new spreadsheets. Triggers on spreadsheet, sheet, rows, columns, cells, range, formula, csv data.`

- **Service name** - `Sheets`

- **What this skill does** - `Enables Claude to read and write Google Sheets - ranges, individual cells, full sheets, formulas, and structured data tables.`

- **When to use bullets**:

  - Reading data from a specific Sheet or range

  - Appending rows to a tracking sheet

  - Updating cells with computed values or formulas

  - Creating new sheets or duplicating templates

  - Exporting structured data into a Sheet

- **Tool reference**:

  - The exact Sheets tool names depend on workspace-mcp's current Sheets module. Reference the live tool list via `uvx workspace-mcp@1.20.4 --tools sheets` or inspect the MCP tools panel.

  - Typical operations exposed (subject to confirmation at implementation time):

    - read range (returns cell values for an A1-notated range)

    - write range (overwrite cell values)

    - append row (add a new row at the bottom)

    - create spreadsheet (new file in Drive)

    - create sheet (add a new tab to an existing spreadsheet)

    - clear range (empty cells without deleting structure)

  - **At implementation time, list the actual exposed tools by inspecting the MCP server and update this section before commit.**

- **Common patterns**:

  - **Log a support inquiry** - read header row to confirm column layout, then append row with `[timestamp, sender, subject, link_to_thread]`.

  - **Read a config sheet** - read named range like `Config!A1:B20`, parse rows into key-value pairs.

  - **Bulk update** - prefer batched range writes over per-cell calls for performance.

- **Gotchas**:

  - Sheets use A1 notation (`Sheet1!A1:B10`) - not R1C1. Always include the sheet name when working with a multi-sheet spreadsheet.

  - Empty cells return as missing values, not empty strings. Be defensive when parsing rows.

  - Sheet IDs (gid in URLs) are different from spreadsheet IDs. The spreadsheet ID is the long random string in the URL; the sheet ID is the small numeric `gid` parameter.

  - Append-row finds the first empty row in a sheet, not necessarily after the last data row. If a sheet has gaps, append may slot into a gap.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/sheets/SKILL.md
git add skills/sheets/SKILL.md
git commit -m "Add sheets service skill"
```

---

### Task 17: slides/SKILL.md

**Files:**

- Create: `skills/slides/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/slides
cp docs/skill-templates/service-skill-template.md skills/slides/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Slides - reading or updating slide content, creating presentations, modifying slide elements, or working with decks. Triggers on presentation, deck, slide, slides, slideshow.`

- **Service name** - `Slides`

- **What this skill does** - `Enables Claude to read, create, and update Google Slides presentations - slide content, layout, and text.`

- **When to use bullets**:

  - Reading the content of an existing deck

  - Creating new presentations from a structure or outline

  - Adding or updating slides within a deck

  - Modifying text on specific slides

- **Tool reference** - confirm exact tool names by inspecting the MCP tools panel at implementation time. Typical operations:

  - read presentation (returns all slide contents)

  - create presentation

  - add slide

  - update slide content

- **Common patterns**:

  - **Generate a deck from an outline** - create presentation, then per outline section add a slide and set its text content.

  - **Read existing deck and summarise** - read presentation, surface slide titles and key text.

- **Gotchas**:

  - Slides has rich layout primitives (text boxes, shapes, images). Don't assume a slide is just a title and bullets.

  - Layouts are template-driven. Changing a slide's layout often requires understanding the master slide structure.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/slides/SKILL.md
git add skills/slides/SKILL.md
git commit -m "Add slides service skill"
```

---

### Task 18: contacts/SKILL.md

**Files:**

- Create: `skills/contacts/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/contacts
cp docs/skill-templates/service-skill-template.md skills/contacts/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Contacts - looking up a person by name or email, creating contacts, searching the address book, or enriching email addresses with contact metadata. Triggers on contact, person, address book, who is X.`

- **Service name** - `Contacts`

- **What this skill does** - `Enables Claude to read and create Google Contacts via the People API - useful for resolving names to emails, enriching contact info, and creating new contact entries.`

- **When to use bullets**:

  - Looking up a contact by name to find their email

  - Looking up by email to find their name and other metadata

  - Creating a new contact

  - Listing contacts in a specific group

- **Tool reference** - confirm exact tool names from MCP tools panel. Typical operations:

  - read contact (by ID or email)

  - search contacts (by name or query)

  - list contacts

  - create contact

- **Common patterns**:

  - **Resolve a name to an email** - search contacts by name, return the matching email(s).

  - **Enrich an email** - given an email, look up the contact and surface name, organisation, phone if present.

- **Gotchas**:

  - The People API distinguishes between contacts (people you've explicitly added) and "other contacts" (people you've emailed but not added). Both may be searchable.

  - Workspace org contacts (directory) are separate from personal contacts. The API exposes both differently.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/contacts/SKILL.md
git add skills/contacts/SKILL.md
git commit -m "Add contacts service skill"
```

---

### Task 19: tasks/SKILL.md

**Files:**

- Create: `skills/tasks/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/tasks
cp docs/skill-templates/service-skill-template.md skills/tasks/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Tasks - reading or creating to-do items, managing checklists, marking tasks complete, working with task lists. Triggers on task, to-do, checklist, action item, google tasks. Does NOT trigger on ClickUp or other PM-system tasks - those go to their respective plugins.`

- **Service name** - `Tasks`

- **What this skill does** - `Enables Claude to read, create, and complete items in Google Tasks - the lightweight to-do system separate from external PM tools.`

- **When to use bullets**:

  - Reading what's on the user's Google Tasks lists

  - Creating new tasks from email or doc content

  - Marking tasks complete

  - Managing or listing task lists

- **Tool reference** - confirm from MCP tools panel. Typical operations:

  - list task lists

  - read tasks in a list

  - create task

  - update task (mark complete, change due date)

  - delete task

- **Common patterns**:

  - **Convert action items from a doc to tasks** - read the doc, parse action items, create one Google Task per item.

  - **Daily task surfacing** - read default task list, surface incomplete items due today or overdue.

- **Gotchas**:

  - Google Tasks is the simple to-do system inside Gmail/Calendar UI. Not to be confused with Google Workspace Tasks API used in admin contexts.

  - If the user uses ClickUp (or another PM) as primary, defer task creation to that plugin per the cross-plugin composition pattern.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/tasks/SKILL.md
git add skills/tasks/SKILL.md
git commit -m "Add tasks service skill"
```

---

### Task 20: forms/SKILL.md

**Files:**

- Create: `skills/forms/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/forms
cp docs/skill-templates/service-skill-template.md skills/forms/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Forms - reading form responses, creating new forms, analysing survey results. Triggers on form, survey, response, questionnaire, form responses.`

- **Service name** - `Forms`

- **What this skill does** - `Enables Claude to read responses from existing Google Forms and create new forms programmatically.`

- **When to use bullets**:

  - Reading responses to a specific form

  - Creating a new form with questions

  - Aggregating or summarising survey results

- **Tool reference** - confirm exact tools from MCP tools panel.

- **Common patterns**:

  - **Summarise survey responses** - read responses, group by question, return distribution and free-text excerpts.

  - **Create a form from a spec** - given a list of questions, create the form and return the share URL.

- **Gotchas**:

  - Form response data structure varies by question type. Multi-select returns arrays; grid questions return nested structures.

  - New forms default to private. Sharing requires Drive API calls (use the drive skill alongside).

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/forms/SKILL.md
git add skills/forms/SKILL.md
git commit -m "Add forms service skill"
```

---

### Task 21: chat/SKILL.md

**Files:**

- Create: `skills/chat/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/chat
cp docs/skill-templates/service-skill-template.md skills/chat/SKILL.md
```

Substitute:

- **description** - `Use when the user's request involves Google Chat - sending messages to spaces, reading channel history, managing Google Chat threads. Triggers on Google Chat, Chat message, Chat space, gchat. Does NOT trigger on Slack - that goes to the Slack plugin if present.`

- **Service name** - `Chat`

- **What this skill does** - `Enables Claude to send and read messages in Google Chat spaces.`

- **When to use bullets**:

  - Sending a message to a Google Chat space

  - Reading recent messages in a space

  - Posting a workflow summary to a Chat channel

- **Tool reference** - confirm exact tools from MCP tools panel.

- **Common patterns**:

  - **Post a workflow summary** - send a one-line summary message to a designated Chat space after a workflow completes.

  - **Read recent activity** - get messages from a space for a given time window.

- **Gotchas**:

  - Google Chat is the Workspace messaging product. Distinct from Slack and Microsoft Teams. If the user's team uses Slack primarily, use the Slack plugin instead.

  - Chat space IDs are different from regular email addresses. They look like `spaces/ABCDEF`.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/chat/SKILL.md
git add skills/chat/SKILL.md
git commit -m "Add chat service skill"
```

---

## Phase 3 - Workflow skills (Tasks 22-35)

Each workflow skill task creates a new directory under `skills/` with a `SKILL.md` derived from the workflow-skill-template (Task 11). Per-workflow values are given below.

---

### Task 22: daily-briefing/SKILL.md

**Files:**

- Create: `skills/daily-briefing/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/daily-briefing
cp docs/skill-templates/workflow-skill-template.md skills/daily-briefing/SKILL.md
```

Substitute:

- **description** - `Scan all authenticated Gmail inboxes for unread or flagged messages today, pull today's calendar events from all accounts, and surface urgent items with context. Invoke via /scribe:daily-briefing.`

- **argument-hint** - `[--account email] [--date YYYY-MM-DD]`

- **Workflow name** - `Daily briefing`

- **Description paragraph** - `Compiles a daily morning briefing across all the user's authenticated Google accounts. Scans inboxes for unread/flagged messages received in the last 24 hours, pulls today's calendar events from every account's primary calendar, and surfaces anything tagged urgent or from named-VIP senders. Output is a short, scannable summary the user can read in 60 seconds.`

- **Parameters bullet**:

  - `--account email` (optional) - restrict to a single account. Default - loop across all authenticated accounts.

  - `--date YYYY-MM-DD` (optional) - the day to brief on. Default - today in user's local timezone.

- **Tool call sequence**:

  1. `list_authenticated_accounts` - get the set of accounts to scan (unless --account specified).

  2. Per account - `search_gmail_messages` with `query="(is:unread OR is:starred) newer_than:1d"`, capture top 10 by recency.

  3. Per account - `get_events` with `calendar_id="primary"`, `time_min=<date 00:00>`, `time_max=<date 23:59>`, capture all events.

  4. Compose the briefing - structured output with sections: Today's Calendar (per account), Unread/Flagged Email (per account), Anything Urgent (VIPs or marked urgent).

  5. Return the briefing as a markdown response. Do NOT save to Drive unless user asks.

- **Multi-account behaviour** - Loops across all authenticated accounts by default. Single account via --account.

- **Cross-plugin composition**:

  - ClickUp plugin - if installed, also surface any tasks due today across configured ClickUp lists.

  - Slack plugin - if installed, surface DMs or mentions from the last 24 hours.

  - AC Builder plugin - if installed, enrich unread emails from new contacts with AC tag info.

- **Example invocations**:

  - "What's on my plate today?"

  - "Give me a daily briefing"

  - "Daily briefing for julian@idd only"

  - Explicit - `/scribe:daily-briefing --account julian@idd`

- **Failure modes**:

  - No accounts authenticated - direct to /scribe:auth-init.

  - Some accounts fail (e.g. token expired for one) - skip those, note in summary, continue with the rest.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/daily-briefing/SKILL.md
git add skills/daily-briefing/SKILL.md
git commit -m "Add /scribe:daily-briefing workflow skill"
```

---

### Task 23: inbox-triage/SKILL.md

**Files:**

- Create: `skills/inbox-triage/SKILL.md`

- [ ] **Step 1: Create from template with substitutions**

```bash
mkdir -p skills/inbox-triage
cp docs/skill-templates/workflow-skill-template.md skills/inbox-triage/SKILL.md
```

Substitute:

- **description** - `Scan all authenticated Gmail inboxes, categorise unread by urgency and sender type, apply labels, and draft replies to flagged threads. Invoke via /scribe:inbox-triage.`

- **argument-hint** - `[--account email] [--since 1d|7d|...] [--no-drafts]`

- **Workflow name** - `Inbox triage`

- **Description paragraph** - `Triages the user's Gmail inbox(es). Categorises unread messages into Action (needs a reply), FYI (just read), and Noise (archive candidate). Applies appropriate labels. For Action items, drafts a reply in the user's voice (saved as draft, never sent automatically).`

- **Parameters**:

  - `--account email` (optional) - single account. Default - all authenticated accounts.

  - `--since 7d` (optional) - time window. Default - 24 hours.

  - `--no-drafts` (optional flag) - skip the draft-reply step.

- **Tool call sequence**:

  1. Resolve accounts (--account or all).

  2. Per account - `search_gmail_messages query="is:unread newer_than:<since>"`.

  3. Per message - `get_gmail_message_content` to read the body.

  4. Classify each message - Action / FYI / Noise using sender, subject patterns, and content cues.

  5. `list_gmail_labels` to find or create labels `Triage/Action`, `Triage/FYI`, `Triage/Noise` if not present (use `manage_gmail_label` to create).

  6. `batch_modify_gmail_message_labels` to apply categorisation.

  7. For each Action message, `draft_gmail_message` with a contextual reply.

  8. Return summary - counts per category, list of drafted replies with links.

- **Multi-account behaviour** - Loops across all authenticated accounts by default.

- **Cross-plugin composition**:

  - ClickUp plugin - for Action items that look like task creation requests, create a ClickUp task and link the email URL.

  - Slack plugin - post a one-line triage summary to a designated channel.

- **Example invocations**:

  - "Triage my inbox"

  - "Sort my unread from the last week"

  - Explicit - `/scribe:inbox-triage --since 3d --no-drafts`

- **Failure modes**:

  - Label creation forbidden - some Workspace orgs restrict label creation. Fall back to categorisation in the output without applying labels.

  - Draft creation fails - the user's scope may be readonly. Surface what would have been drafted.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/inbox-triage/SKILL.md
git add skills/inbox-triage/SKILL.md
git commit -m "Add /scribe:inbox-triage workflow skill"
```

---

### Task 24: support-scan/SKILL.md

**Files:**

- Create: `skills/support-scan/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/support-scan
cp docs/skill-templates/workflow-skill-template.md skills/support-scan/SKILL.md
```

Substitute:

- **description** - `Scan a designated support inbox for new inquiries, log each to a tracking sheet, draft initial response. Invoke via /scribe:support-scan.`

- **argument-hint** - `[--account email] [--sheet-id ID] [--since 1d]`

- **Workflow name** - `Support inquiry scan`

- **Description paragraph** - `Designed for support inbox triage. Scans a specified account's inbox for new inquiries in the time window, classifies each (general inquiry, complaint, refund, course-question, other), logs each row to a designated tracking sheet, and drafts an initial response in the support team's voice.`

- **Parameters**:

  - `--account email` (required if user has multiple accounts) - the support inbox to scan.

  - `--sheet-id ID` (required first time) - the tracking sheet ID. Cached in conversation for repeat invocations.

  - `--since 1d` (optional) - time window. Default - 1 day.

- **Tool call sequence**:

  1. Validate parameters; if `--sheet-id` missing, ask user once.

  2. `search_gmail_messages` with `query="is:unread newer_than:<since>"` on the support account.

  3. Per message - `get_gmail_thread_content` for full context.

  4. Classify intent (rule-based or LLM judgment in prose).

  5. Per inquiry - append a row to the tracking sheet with `[timestamp, sender, subject, classification, thread_url, status="new"]`.

  6. Per inquiry - `draft_gmail_message` with a context-aware reply.

  7. Return summary - counts per category, sheet URL, list of drafted responses.

- **Multi-account behaviour** - Single account (the designated support inbox). Requires `--account` if user has multiple authenticated.

- **Cross-plugin composition**:

  - ClickUp plugin - for inquiries classified as bugs/complaints, create a ClickUp task in the support list with the email URL.

  - Slack plugin - post new urgent inquiries to a `#support` channel.

  - Spiffy plugin - for refund or credit inquiries, look up purchase history before drafting the response.

  - AC Builder plugin - enrich sender info with AC tags before classification.

- **Example invocations**:

  - "Scan our support inbox"

  - "Run support triage on julian@idd, log to the support tracker"

  - Explicit - `/scribe:support-scan --account support@idd --sheet-id 1AB...XYZ --since 12h`

- **Failure modes**:

  - Sheet not found - prompt user for correct sheet ID or offer to create one.

  - No new inquiries - report "No new inquiries in window" and exit clean.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/support-scan/SKILL.md
git add skills/support-scan/SKILL.md
git commit -m "Add /scribe:support-scan workflow skill"
```

---

### Task 25: meeting-prep/SKILL.md

**Files:**

- Create: `skills/meeting-prep/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/meeting-prep
cp docs/skill-templates/workflow-skill-template.md skills/meeting-prep/SKILL.md
```

Substitute:

- **description** - `Pull a specific or next calendar event, find related emails from attendees, build a structured prep doc in Drive. Invoke via /scribe:meeting-prep.`

- **argument-hint** - `[--event "title"] [--event-id ID] [--account email] [--folder ID]`

- **Workflow name** - `Meeting prep`

- **Description paragraph** - `Builds a structured prep doc for a meeting. Pulls the calendar event (next upcoming OR specified by title or ID), looks up related emails from each attendee across the user's accounts, and assembles a doc with Attendees, Context, Discussion topics, and Open questions sections.`

- **Parameters**:

  - `--event "title"` OR `--event-id ID` - specifies the event. If neither, use next upcoming event on the primary calendar.

  - `--account email` (optional) - account to use. Default - resolved per the standard rules.

  - `--folder ID` (optional) - Drive folder for the prep doc. Default - a folder named "Meeting briefings" under the user's My Drive, created if absent.

- **Tool call sequence**:

  1. Resolve the event - `get_events` to find next upcoming, OR `manage_event action="read"` if ID provided, OR `get_events` with `q=<title>` if title provided.

  2. Extract attendee emails from the event.

  3. Per attendee - `search_gmail_messages` with `query="from:<attendee> OR to:<attendee>"`, capture top 5 by recency.

  4. Resolve target folder - `search_drive_files` for "Meeting briefings", create if absent.

  5. `create_doc` titled `Meeting prep - <event title> - <date>`.

  6. Populate the doc via `manage_doc_tab populate_from_markdown` with sections: Attendees (names + emails + brief context), Meeting context (event description, location, time), Recent communication (links to top emails per attendee), Agenda (placeholder), Open questions (placeholder).

  7. Return the doc URL.

- **Multi-account behaviour** - Uses the account that owns the event by default. Cross-account email search per attendee uses all authenticated accounts.

- **Cross-plugin composition**:

  - ClickUp plugin - if the event title or description mentions a ClickUp task, link it in the prep doc.

  - AC Builder plugin - enrich attendee context with AC tags and recent automation history.

  - Slack plugin - find prior Slack discussions about the meeting topic or attendees.

- **Example invocations**:

  - "Prep for my next meeting"

  - "Meeting prep for the Q3 planning event"

  - "Build a briefing doc for tomorrow's call with Sarah"

  - Explicit - `/scribe:meeting-prep --event-id ABC123 --folder DEF456`

- **Failure modes**:

  - No upcoming events - tell user and offer to search by title.

  - Multiple events match a title query - prompt user to pick.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/meeting-prep/SKILL.md
git add skills/meeting-prep/SKILL.md
git commit -m "Add /scribe:meeting-prep workflow skill"
```

---

### Task 26: thread-to-doc/SKILL.md

**Files:**

- Create: `skills/thread-to-doc/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/thread-to-doc
cp docs/skill-templates/workflow-skill-template.md skills/thread-to-doc/SKILL.md
```

Substitute:

- **description** - `Convert an email thread into a structured Google Doc; save any attachments into a client or contact subfolder in Drive. Invoke via /scribe:thread-to-doc.`

- **argument-hint** - `[--thread-id ID] [--client CLIENT-ID] [--folder ID]`

- **Workflow name** - `Thread to doc`

- **Description paragraph** - `Converts an email thread to a Google Doc and organises its attachments into a client folder. The doc contains the thread structured chronologically with sender, timestamp, and body per message. Attachments are saved into a per-thread subfolder under the chosen client or contact root.`

- **Parameters**:

  - `--thread-id ID` (optional, prompts if missing) - the thread to convert.

  - `--client CLIENT-ID` (optional) - AHPRA-style client. Resolves the destination folder via client-resolve.

  - `--folder ID` (optional) - explicit destination folder if not using a client.

- **Tool call sequence**:

  1. Resolve thread - prompt user if no `--thread-id`; offer search by sender or subject.

  2. `get_gmail_thread_content` - fetch full thread.

  3. Resolve destination folder - use --folder, or resolve via client-resolve skill, or default to a "Conversations" folder under My Drive.

  4. `create_drive_folder` for `<thread-subject>-<date>` as a subfolder of destination.

  5. Per message in thread - if attachments present, `get_gmail_attachment_content` then `create_drive_file` into the thread subfolder.

  6. `create_doc` titled `Email thread - <subject>` in the thread subfolder.

  7. Populate via `manage_doc_tab populate_from_markdown` with structured thread content (each message as a section with sender/timestamp/body).

  8. Return the doc URL plus subfolder URL.

- **Multi-account behaviour** - Single account. Account selected by where the thread lives.

- **Cross-plugin composition**:

  - ClickUp plugin - if the thread suggests a follow-up task, create one with doc URL attached.

  - AC Builder plugin - log the conversation against the contact's AC record.

- **Example invocations**:

  - "Save this email thread to a doc"

  - "Convert the thread about Q3 planning to a doc, save attachments to the iDD-internal client folder"

  - Explicit - `/scribe:thread-to-doc --thread-id 18b... --client IDD-ED-001`

- **Failure modes**:

  - Thread has many large attachments - inform user of attachment sizes, ask for confirmation before downloading.

  - Sandbox rejection on attachment save - attachment must be saved to a Drive folder, not local; this isn't a sandbox issue, but if `create_drive_file` requires a local path, route through the sandbox auto-copy pattern (see push/SKILL.md).

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/thread-to-doc/SKILL.md
git add skills/thread-to-doc/SKILL.md
git commit -m "Add /scribe:thread-to-doc workflow skill"
```

---

### Task 27: client-digest/SKILL.md

**Files:**

- Create: `skills/client-digest/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/client-digest
cp docs/skill-templates/workflow-skill-template.md skills/client-digest/SKILL.md
```

Substitute:

- **description** - `Aggregate emails, calendar events, and Drive activity (comments, suggested edits, recent changes) for a named client or contact. Invoke via /scribe:client-digest.`

- **argument-hint** - `<client-or-contact> [--since 7d] [--account email]`

- **Workflow name** - `Client digest`

- **Description paragraph** - `Builds a comprehensive activity digest for a specific client, contact, or company. Surfaces all email threads, calendar events, and Drive document activity (comments, suggested edits, recent modifications) related to that entity within the time window.`

- **Parameters**:

  - `<client-or-contact>` (positional, required) - name, email, or AHPRA CLIENT-ID.

  - `--since 7d` (optional) - time window. Default - 7 days.

  - `--account email` (optional) - account to scope to. Default - all accounts.

- **Tool call sequence**:

  1. Resolve the contact - if AHPRA CLIENT-ID, use client-resolve. If name, search Contacts. If email, use directly.

  2. Resolve accounts (all unless --account).

  3. Per account - `search_gmail_messages` with `query="from:<email> OR to:<email> newer_than:<since>"`.

  4. Per account - `get_events` with `q=<contact-name>` or filter events with the contact as attendee.

  5. `search_drive_files` for docs that mention the contact or are shared with them.

  6. Per matching doc - `list_document_comments` to surface comment activity.

  7. Assemble digest with sections: Emails, Calendar events, Drive activity (modified, shared, commented).

  8. Return as markdown summary OR save to a doc if user prefers.

- **Multi-account behaviour** - Loops all accounts by default.

- **Cross-plugin composition**:

  - AC Builder plugin - include the contact's AC tags, list memberships, and recent automation history.

  - Slack plugin - search Slack channels for mentions of the contact.

  - Spiffy plugin - if the contact is a customer, include purchase history, course progress, and credit balance.

  - ClickUp plugin - surface any open ClickUp tasks tied to the contact.

- **Example invocations**:

  - "Tell me everything about Sarah Smith"

  - "Client digest for IDD-ED-007 over the last 30 days"

  - Explicit - `/scribe:client-digest "sarah@example.com" --since 30d`

- **Failure modes**:

  - No matches - report "No activity found in window for <contact>".

  - Multiple contacts match a name - prompt user to pick.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/client-digest/SKILL.md
git add skills/client-digest/SKILL.md
git commit -m "Add /scribe:client-digest workflow skill"
```

---

### Task 28: weekly-wrap/SKILL.md

**Files:**

- Create: `skills/weekly-wrap/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/weekly-wrap
cp docs/skill-templates/workflow-skill-template.md skills/weekly-wrap/SKILL.md
```

Substitute:

- **description** - `Compile the past week's emails, calendar events, and Drive document activity into a summary report doc. Invoke via /scribe:weekly-wrap.`

- **argument-hint** - `[--week current|last|N] [--output-folder ID] [--account email]`

- **Workflow name** - `Weekly wrap`

- **Description paragraph** - `Generates a weekly summary report compiling all the user's activity across Gmail, Calendar, and Drive into a structured doc. Sections include emails sent and received, meetings attended, docs created or significantly edited.`

- **Parameters**:

  - `--week current|last|N` (optional) - default `last`. `current` = this week so far, `last` = last full week, `N` = N weeks ago.

  - `--output-folder ID` (optional) - destination. Default - "Weekly wraps" folder under My Drive, created if absent.

  - `--account email` (optional) - single account. Default - all accounts.

- **Tool call sequence**:

  1. Compute the week's date range based on --week.

  2. Resolve accounts.

  3. Per account - `search_gmail_messages query="newer_than:<7d> older_than:<0d>"` for received; same with `in:sent` for sent.

  4. Per account - `get_events` for the week's range.

  5. `search_drive_files` for files modified in the week's range owned by the user.

  6. Resolve or create the output folder.

  7. `create_doc` titled `Weekly wrap - <week-of-date>` in output folder.

  8. Populate with sections - Activity overview (counts), Notable emails sent/received, Meetings attended, Documents created/edited.

  9. Return doc URL.

- **Multi-account behaviour** - Loops all accounts by default. The output doc surfaces per-account breakdowns.

- **Cross-plugin composition**:

  - ClickUp plugin - include tasks completed and tasks created in the week from configured lists.

  - Spiffy plugin - include the week's enrollment/refund/credit activity.

- **Example invocations**:

  - "Give me a weekly wrap"

  - "Compile last week's activity into a report"

  - Explicit - `/scribe:weekly-wrap --week last --output-folder ABC...`

- **Failure modes**:

  - No activity - produce a doc anyway with "Quiet week" sections.

  - Output folder creation fails - save to My Drive root with a fallback name.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/weekly-wrap/SKILL.md
git add skills/weekly-wrap/SKILL.md
git commit -m "Add /scribe:weekly-wrap workflow skill"
```

---

### Task 29: follow-up-tracker/SKILL.md

**Files:**

- Create: `skills/follow-up-tracker/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/follow-up-tracker
cp docs/skill-templates/workflow-skill-template.md skills/follow-up-tracker/SKILL.md
```

Substitute:

- **description** - `Find sent emails with no reply after N days; surface them with optional draft follow-ups. Invoke via /scribe:follow-up-tracker.`

- **argument-hint** - `[--days 7] [--account email] [--draft-replies]`

- **Workflow name** - `Follow-up tracker`

- **Description paragraph** - `Identifies sent emails that haven't received a reply after a configurable threshold (default 7 days). Optionally drafts polite follow-up replies for each.`

- **Parameters**:

  - `--days N` (optional, default 7) - how many days without reply before flagging.

  - `--account email` (optional) - single account. Default - all accounts.

  - `--draft-replies` (optional flag) - also draft a follow-up reply for each.

- **Tool call sequence**:

  1. Resolve accounts.

  2. Per account - `search_gmail_messages query="in:sent older_than:<days>d newer_than:<days+30>d"`.

  3. Per message - `get_gmail_thread_content` to check whether a reply came after the original.

  4. Filter to those with no reply.

  5. If --draft-replies, `draft_gmail_message` per item with a polite follow-up referencing the original.

  6. Return list with subject, recipient, days-since-sent, and (if drafted) draft URLs.

- **Multi-account behaviour** - Loops all accounts by default.

- **Cross-plugin composition**:

  - ClickUp plugin - for follow-ups that look task-related, create a "follow up" task with email URL.

- **Example invocations**:

  - "What emails am I waiting on replies to?"

  - "Find emails I sent two weeks ago that haven't been answered, draft follow-ups"

  - Explicit - `/scribe:follow-up-tracker --days 14 --draft-replies`

- **Failure modes**:

  - No unanswered emails - report clean inbox.

  - Thread structure ambiguous (user replied to self after sending) - filter heuristic should ignore self-replies.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/follow-up-tracker/SKILL.md
git add skills/follow-up-tracker/SKILL.md
git commit -m "Add /scribe:follow-up-tracker workflow skill"
```

---

### Task 30: contact-onboard/SKILL.md

**Files:**

- Create: `skills/contact-onboard/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/contact-onboard
cp docs/skill-templates/workflow-skill-template.md skills/contact-onboard/SKILL.md
```

Substitute:

- **description** - `Bootstrap a new contact - create Drive folder, add Contacts entry, log row in a tracking sheet, draft welcome email. Invoke via /scribe:contact-onboard.`

- **argument-hint** - `<name-and-email> [--folder-parent ID] [--tracker-sheet ID] [--account email]`

- **Workflow name** - `Contact onboarding`

- **Description paragraph** - `For onboarding a new contact, client, or business relationship. Creates a structured Drive folder for them, adds them to Google Contacts, logs a row in the tracking sheet of the user's choice, and drafts a welcome email.`

- **Parameters**:

  - `<name-and-email>` (required) - in format `Sarah Smith <sarah@example.com>`.

  - `--folder-parent ID` (optional) - parent folder for the new contact folder. Default - "Contacts" folder under My Drive.

  - `--tracker-sheet ID` (optional, prompts if missing first run) - the contact tracker sheet.

  - `--account email` (optional) - account to use.

- **Tool call sequence**:

  1. Parse name and email from input.

  2. Check if contact already exists - search Contacts by email. If exists, prompt user to confirm before duplicating.

  3. Create Contacts entry.

  4. Resolve folder parent (use --folder-parent or default).

  5. `create_drive_folder` for the contact's name as a subfolder.

  6. `manage_drive_access` - share the contact folder with the contact's email if user confirms.

  7. Append a row to the tracker sheet with `[date, name, email, folder_url, status="onboarding"]`.

  8. `draft_gmail_message` with a welcome email template - introducing the user, linking the shared folder, mentioning next steps.

  9. Return folder URL, draft URL, sheet row reference.

- **Multi-account behaviour** - Single account. Specified via --account or resolved.

- **Cross-plugin composition**:

  - AC Builder plugin - add contact to ActiveCampaign, apply default new-contact tag.

  - ClickUp plugin - create an onboarding task series in the configured onboarding list.

  - Slack plugin - if Slack channel invites are supported, optionally invite the contact to a shared channel.

- **Example invocations**:

  - "Onboard Sarah Smith <sarah@example.com>"

  - "Set up a new contact - John Brown john@example.com"

  - Explicit - `/scribe:contact-onboard "Sarah Smith <sarah@example.com>" --tracker-sheet ABC...`

- **Failure modes**:

  - Contact already exists - prompt before duplicating.

  - Folder already exists at the path - prompt before overwriting; default to appending date suffix.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/contact-onboard/SKILL.md
git add skills/contact-onboard/SKILL.md
git commit -m "Add /scribe:contact-onboard workflow skill"
```

---

### Task 31: doc-chase/SKILL.md

**Files:**

- Create: `skills/doc-chase/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/doc-chase
cp docs/skill-templates/workflow-skill-template.md skills/doc-chase/SKILL.md
```

Substitute:

- **description** - `Find Google Docs shared with reviewers that have no recent comment or edit activity; draft reminder emails to the reviewers. Invoke via /scribe:doc-chase.`

- **argument-hint** - `[--folder ID] [--days 7] [--account email] [--draft-reminders]`

- **Workflow name** - `Doc review chaser`

- **Description paragraph** - `Finds Google Docs that have been shared for review but haven't been touched (no comments, suggested edits, or content changes) within the time window. Drafts polite reminder emails to the inactive reviewers.`

- **Parameters**:

  - `--folder ID` (optional) - scope to docs in this folder. Default - all docs owned by the user.

  - `--days N` (optional, default 7) - inactivity threshold.

  - `--account email` (optional) - single account.

  - `--draft-reminders` (optional flag) - also draft reminder emails.

- **Tool call sequence**:

  1. Resolve accounts.

  2. `search_drive_files` (or `list_docs_in_folder` if folder specified) for Docs owned by the user, modified more than `--days` ago.

  3. Per doc - `get_drive_file_permissions` to find reviewers (commenter/writer roles, not owner).

  4. Per doc - `list_document_comments` to check recent comment activity.

  5. Filter to docs with reviewers AND no comment/edit activity in window.

  6. If --draft-reminders, per doc, `draft_gmail_message` to each inactive reviewer with a polite nudge.

  7. Return list of stale docs with reviewer emails and draft URLs.

- **Multi-account behaviour** - Single account by default. --account to scope.

- **Cross-plugin composition**:

  - Slack plugin - for reviewers in shared Slack workspaces, optionally DM them instead of email.

- **Example invocations**:

  - "What docs am I waiting on review for?"

  - "Chase up outstanding doc reviews from last week"

  - Explicit - `/scribe:doc-chase --folder ABC --days 10 --draft-reminders`

- **Failure modes**:

  - No stale docs - report clean state.

  - Multiple reviewers per doc - draft separate reminders per reviewer.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/doc-chase/SKILL.md
git add skills/doc-chase/SKILL.md
git commit -m "Add /scribe:doc-chase workflow skill"
```

---

### Task 32: attach-vault/SKILL.md

**Files:**

- Create: `skills/attach-vault/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/attach-vault
cp docs/skill-templates/workflow-skill-template.md skills/attach-vault/SKILL.md
```

Substitute:

- **description** - `Scan Gmail inbox for emails with attachments, organise the attachments into Drive folders by sender or project. Invoke via /scribe:attach-vault.`

- **argument-hint** - `[--since 30d] [--by sender|project] [--vault-root ID] [--account email]`

- **Workflow name** - `Attachment vault`

- **Description paragraph** - `Periodic attachment archival. Scans Gmail for emails with attachments in the time window, downloads each attachment, and organises them into Drive folders by sender (default) or by project (heuristic on subject line).`

- **Parameters**:

  - `--since 30d` (optional) - time window. Default - 30 days.

  - `--by sender|project` (optional) - organisation strategy. Default - `sender`.

  - `--vault-root ID` (optional) - parent Drive folder. Default - "Attachment vault" under My Drive.

  - `--account email` (optional) - single account or default to all.

- **Tool call sequence**:

  1. Resolve accounts.

  2. Per account - `search_gmail_messages query="has:attachment newer_than:<since>"`.

  3. Per message - extract sender, subject, and attachment metadata.

  4. Resolve or create vault root.

  5. Per attachment - determine destination subfolder (`Vault/<sender-domain>/<sender>` for sender mode; `Vault/<project-tag>` for project mode where project-tag is heuristic on subject).

  6. `create_drive_folder` for missing subfolders.

  7. `get_gmail_attachment_content` then `create_drive_file` into the appropriate subfolder.

  8. Return summary - counts per subfolder, total attachments archived.

- **Multi-account behaviour** - Loops all accounts by default.

- **Cross-plugin composition** - None specific. Pure Workspace workflow.

- **Example invocations**:

  - "Archive all my email attachments from the last month"

  - "Save attachments to a vault by sender"

  - Explicit - `/scribe:attach-vault --since 60d --by project`

- **Failure modes**:

  - Very large attachments - confirm before downloading anything over a threshold (e.g. 50MB).

  - Duplicate filenames - append timestamp to disambiguate.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/attach-vault/SKILL.md
git add skills/attach-vault/SKILL.md
git commit -m "Add /scribe:attach-vault workflow skill"
```

---

### Task 33: event-recap/SKILL.md

**Files:**

- Create: `skills/event-recap/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/event-recap
cp docs/skill-templates/workflow-skill-template.md skills/event-recap/SKILL.md
```

Substitute:

- **description** - `Post-meeting recap - pull emails from attendees since the event, create a notes/action-items doc, draft a follow-up email. Invoke via /scribe:event-recap.`

- **argument-hint** - `[--event-id ID] [--account email] [--folder ID]`

- **Workflow name** - `Event recap`

- **Description paragraph** - `Post-meeting workflow. Pulls the most recent past calendar event (or specified by ID), gathers any emails from attendees since the event happened, creates a notes and action-items doc, and drafts a follow-up email to attendees.`

- **Parameters**:

  - `--event-id ID` (optional) - default - most recent past event.

  - `--account email` (optional) - account that owns the event.

  - `--folder ID` (optional) - destination for the recap doc. Default - "Meeting recaps" folder.

- **Tool call sequence**:

  1. Resolve event - most recent past, or by ID.

  2. Extract attendees, original event description, location.

  3. Per attendee - `search_gmail_messages query="from:<attendee> newer_than:<event-time>"` for follow-up communication.

  4. Resolve recap folder.

  5. `create_doc` titled `Recap - <event title> - <date>`.

  6. Populate with sections - Event summary, Attendees, Notes (placeholder), Action items (placeholder), Post-meeting emails (links).

  7. `draft_gmail_message` to all attendees with the doc link and a brief summary.

  8. Return doc URL and draft URL.

- **Multi-account behaviour** - Single account (the event owner's).

- **Cross-plugin composition**:

  - ClickUp plugin - for action items detected in the notes section, offer to create ClickUp tasks.

  - Slack plugin - post the recap doc link to a designated channel.

- **Example invocations**:

  - "Recap my last meeting"

  - "Build a recap doc from this morning's call"

  - Explicit - `/scribe:event-recap --event-id ABC123`

- **Failure modes**:

  - No recent past event - prompt user to specify.

  - Multi-day or recurring event - clarify which occurrence to recap.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/event-recap/SKILL.md
git add skills/event-recap/SKILL.md
git commit -m "Add /scribe:event-recap workflow skill"
```

---

### Task 34: smart-reply/SKILL.md

**Files:**

- Create: `skills/smart-reply/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/smart-reply
cp docs/skill-templates/workflow-skill-template.md skills/smart-reply/SKILL.md
```

Substitute:

- **description** - `Given a contact name or email and a topic, pull prior email history with that contact for context and draft a contextual reply. Invoke via /scribe:smart-reply.`

- **argument-hint** - `<contact> <topic-or-message> [--account email]`

- **Workflow name** - `Smart reply`

- **Description paragraph** - `For composing a contextual email without needing to read through full thread history first. Given a contact (name or email) and a topic or message intent, pulls the user's recent email history with that contact, then drafts a reply that fits the relationship tone and references relevant prior context.`

- **Parameters**:

  - `<contact>` (required) - name or email of the recipient.

  - `<topic-or-message>` (required) - what the email is about.

  - `--account email` (optional) - sender account. Default - resolved.

- **Tool call sequence**:

  1. Resolve contact email if name given - search Contacts.

  2. `search_gmail_messages query="from:<contact-email> OR to:<contact-email>"`, limit to 5-10 most recent.

  3. `get_gmail_messages_content_batch` for context.

  4. Compose a reply in the user's voice, referencing prior context where relevant.

  5. `draft_gmail_message` with the reply.

  6. Return draft URL and a preview of the draft text.

- **Multi-account behaviour** - Single account (the sender).

- **Cross-plugin composition**:

  - AC Builder plugin - enrich contact context with AC tags and recent automation history.

- **Example invocations**:

  - "Draft an email to Sarah about the proposal deadline"

  - "Smart reply to john@example.com - we need to push the meeting"

  - Explicit - `/scribe:smart-reply "Sarah" "Q3 proposal deadline pushback" --account julian@idd`

- **Failure modes**:

  - Contact not found - prompt for email.

  - No prior history - draft anyway but note the lack of context.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/smart-reply/SKILL.md
git add skills/smart-reply/SKILL.md
git commit -m "Add /scribe:smart-reply workflow skill"
```

---

### Task 35: educator-setup/SKILL.md

**Files:**

- Create: `skills/educator-setup/SKILL.md`

- [ ] **Step 1: Create from template**

```bash
mkdir -p skills/educator-setup
cp docs/skill-templates/workflow-skill-template.md skills/educator-setup/SKILL.md
```

Substitute:

- **description** - `Bootstrap a new educator - create their Drive folder structure with curriculum, planning, and course tracker, share access, and draft a welcome email. Invoke via /scribe:educator-setup.`

- **argument-hint** - `<name-and-email> [--parent-folder ID] [--tracker-sheet ID] [--course-name "..."]`

- **Workflow name** - `Educator setup`

- **Description paragraph** - `iDD-specific workflow for onboarding a new educator for a course. Creates a structured Drive folder set (curriculum, planning, course tracker), adds the educator as collaborator, logs them to the master educator tracker sheet, and drafts a welcome email with expectations and kickoff meeting suggestion.`

- **Parameters**:

  - `<name-and-email>` (required) - educator info.

  - `--parent-folder ID` (optional) - parent under which to create the educator folder. Default - "Educators" folder.

  - `--tracker-sheet ID` (optional) - master educator tracker sheet.

  - `--course-name "..."` (optional) - which course they'll teach.

- **Tool call sequence**:

  1. Parse name and email.

  2. Resolve parent folder.

  3. `create_drive_folder` for `<educator-name>` under parent.

  4. Inside, `create_drive_folder` for `Curriculum`, `Planning`, `Recordings`.

  5. `create_doc` titled `<educator-name> - Course planning` in Planning folder.

  6. `manage_drive_access` to share the educator folder with the educator's email at `writer` level.

  7. Append row to tracker sheet with `[date, name, email, folder_url, course_name, status="onboarding"]`.

  8. `draft_gmail_message` welcome email with folder link, expectations summary, suggested kickoff date.

  9. Return folder URLs and draft URL.

- **Multi-account behaviour** - Uses the iDD account by default (resolved via user context).

- **Cross-plugin composition**:

  - AC Builder plugin - add the educator to the AC educators list.

  - ClickUp plugin - create educator onboarding task series in the designated list.

  - Slack plugin - invite to relevant Slack channels (or draft a request to invite them).

- **Example invocations**:

  - "Set up Dr Sarah Smith as a new educator for the Implant course"

  - "Onboard educator John Brown john@example.com"

  - Explicit - `/scribe:educator-setup "Dr Sarah Smith <sarah@example.com>" --course-name "Implant placement masterclass"`

- **Failure modes**:

  - Educator already exists - prompt before overwriting.

  - Sharing fails (external user, org policy) - surface the issue and continue with rest of setup.

- [ ] **Step 2: Validate and commit**

```bash
wc -l skills/educator-setup/SKILL.md
git add skills/educator-setup/SKILL.md
git commit -m "Add /scribe:educator-setup workflow skill"
```

---

## Phase 4 - User-facing documentation

### Task 36: Rewrite README.md

**Files:**

- Rewrite: `README.md`

- [ ] **Step 1: Replace README.md contents**

Write the README with these exact contents:

```markdown
# Scribe - Google Workspace orchestration for Claude Code

Scribe is a Claude Code plugin that turns Google Workspace into a programmable surface. Multi-account access to Gmail, Calendar, Drive, Docs, Sheets, Slides, Contacts, Tasks, Forms, and Chat. 14 named cross-service workflow commands. Wraps [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp).

**Version 1.0.0** | MIT licensed | Install via `/plugin marketplace add juliandickie/scribe-plugin`

## What you can do

- Run named workflows across services - daily briefing, inbox triage, meeting prep, weekly wrap, and 10 more

- Compose Workspace operations dynamically from natural-language prompts - "check both my inboxes for anything urgent and create a summary doc"

- Manage multiple Google accounts in one Claude session - personal Gmail and business Workspace, agency client and own org

## Install

```bash
/plugin marketplace add juliandickie/scribe-plugin
/plugin install scribe
/scribe:auth-init
```

The `auth-init` command walks through one-time Google Cloud Project setup and OAuth consent (5-10 minutes).

## Workflows

14 named commands that compose multi-service operations. Each accepts natural-language invocation OR explicit flags.

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

## Multi-org and multi-account

Scribe handles multiple OAuth clients (one per Workspace org if you need cross-org access). The token cache stores credentials per email; multi-account loops are first-class in the orchestration router. See [docs/multi-org-setup.md](docs/multi-org-setup.md) for the symlink-swap pattern.

## Architecture

Three-layer skill model:

1. **Orchestration router** (`workspace/SKILL.md`) - auto-loads on every Workspace request. Routes between accounts, services, and workflows.

2. **Service skills** (10 files) - auto-load when their specific service is in scope. Teach the MCP tool API for that service.

3. **Workflow skills** (14 files) - user-invoked via slash command. Each is a complete recipe for one cross-service operation.

This keeps each skill focused (under 500 lines), avoids token bloat, and lets the marketplace user pick what to invoke.

## Customisation

- `ALLOWED_FILE_DIRS` env var in your `.claude/settings.json` MCP config can extend the upload sandbox beyond `~/.workspace-mcp/attachments`.

- `--permissions SERVICE:LEVEL` override (in place of `--tools`) lets you restrict OAuth scopes per service. See `skills/auth-init/SKILL.md` "Restricting scopes (advanced)" section.

- Workflow skills are independent files - fork the repo and edit any to suit your workflow needs.

## License

MIT.

## Credits

Wraps [`workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) by [@taylorwilsdon](https://github.com/taylorwilsdon). The breadth of Scribe v1.0 is possible because of his work on the underlying MCP server.
```

- [ ] **Step 2: Verify the readme renders well**

```bash
wc -l README.md
head -50 README.md
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "README - rewrite for v1.0 - workflows, services, three-layer architecture"
```

---

### Task 37: Create docs/workflows.md

**Files:**

- Create: `docs/workflows.md`

- [ ] **Step 1: Create the workflows reference doc by aggregating the 14 SKILL.md files**

The doc structure mirrors the 14 skill files but presented as a single browsable reference. Each section copies the body of the corresponding `skills/<workflow>/SKILL.md` (everything below the frontmatter).

```bash
cat > docs/workflows.md <<'EOF'
# Scribe Workflows Reference

Detailed reference for the 14 named workflow slash commands in Scribe v1.0. Each entry covers what the workflow does, parameters, full tool sequence, multi-account behaviour, cross-plugin composition options, examples, and failure modes.

For shorter prose loaded into Claude at runtime, see the individual `skills/<workflow>/SKILL.md` files. This document is a maintainer and user reference rather than a runtime-loaded skill.

EOF

# Append each workflow skill's body (skip frontmatter)
for skill in daily-briefing inbox-triage support-scan meeting-prep thread-to-doc \
             client-digest weekly-wrap follow-up-tracker contact-onboard doc-chase \
             attach-vault event-recap smart-reply educator-setup; do
  echo "" >> docs/workflows.md
  echo "---" >> docs/workflows.md
  echo "" >> docs/workflows.md
  # Strip frontmatter (everything between first --- and second ---)
  awk '/^---$/{c++} c>=2 && !/^---$/' "skills/$skill/SKILL.md" >> docs/workflows.md
done

# Add closing sections
cat >> docs/workflows.md <<'EOF'

---

## Cross-workflow patterns

These patterns recur across multiple workflows -

- **Multi-account loop** - workflows that scan or compile across accounts call `list_authenticated_accounts` first, then iterate. The orchestration router (workspace/SKILL.md) defines when this fires automatically vs. prompts.

- **Attachment handling** - workflows that download attachments use `get_gmail_attachment_content` then `create_drive_file`. The sandbox at `~/.workspace-mcp/attachments` does not constrain Drive uploads, only local file uploads.

- **Cross-plugin defer** - any workflow can chain into ClickUp, Slack, Spiffy, AC Builder, or other plugins by referencing them in prose. Claude reads the hint and chains naturally.

## Authoring new workflows

Add a new workflow skill in v1.1+ by copying `docs/skill-templates/workflow-skill-template.md` to `skills/<workflow-slug>/SKILL.md`, filling in the placeholders, and adding the slug to the validation loop in `Makefile`.
EOF
```

- [ ] **Step 2: Verify the file looks right**

```bash
wc -l docs/workflows.md
head -20 docs/workflows.md
```

- [ ] **Step 2: Commit**

```bash
git add docs/workflows.md
git commit -m "docs - add workflows reference"
```

---

### Task 38: Create docs/services.md

**Files:**

- Create: `docs/services.md`

- [ ] **Step 1: Create services reference doc by aggregating the 10 service skill files**

```bash
cat > docs/services.md <<'EOF'
# Scribe Services Reference

Detailed reference for the 10 service skills in Scribe v1.0. Each section enumerates the MCP tools available for that service, their parameter shapes, common patterns, and gotchas.

For shorter prose loaded into Claude at runtime, see the individual `skills/<service>/SKILL.md` files.

EOF

# Append each service skill's body (skip frontmatter)
for skill in gmail calendar docs drive sheets slides contacts tasks forms chat; do
  echo "" >> docs/services.md
  echo "---" >> docs/services.md
  echo "" >> docs/services.md
  awk '/^---$/{c++} c>=2 && !/^---$/' "skills/$skill/SKILL.md" >> docs/services.md
done

# Add cross-service section
cat >> docs/services.md <<'EOF'

---

## Cross-service patterns

These patterns chain multiple services. They mirror the orchestration logic in `skills/workspace/SKILL.md`.

### Email to Doc

Gmail (`get_gmail_thread_content`) → optional Gmail (`get_gmail_attachment_content`) → optional Drive (`create_drive_file`) → Docs (`create_doc` + `manage_doc_tab populate_from_markdown`).

### Calendar to prep Doc

Calendar (`get_events`) → Gmail (`search_gmail_messages` per attendee) → Docs (`create_doc`).

### Sheet logging

Sheets (read header row to confirm structure) → Sheets (append row).

### Drive activity scan

Drive (`list_drive_items` + `get_drive_file_permissions`) → Docs (`list_document_comments`).

For full multi-service workflows, see `docs/workflows.md`.

## Authoring new service skills

Add a new service skill in v1.1+ by copying `docs/skill-templates/service-skill-template.md` to `skills/<service>/SKILL.md`, filling in the placeholders with the service-specific MCP tools, and adding the slug to the validation loop in `Makefile`.
EOF
```

- [ ] **Step 2: Verify the file looks right**

```bash
wc -l docs/services.md
head -20 docs/services.md
```

- [ ] **Step 2: Commit**

```bash
git add docs/services.md
git commit -m "docs - add services reference"
```

---

## Phase 5 - Validation and release

### Task 39: Run validation

**Files:**

- Inspect: all skill files, manifests

- [ ] **Step 1: Run make validate**

```bash
make validate
```

Expected: all 30 skill directories report `present`. plugin.json and marketplace.json report valid JSON. If any skill missing, the make target exits 1 - identify which, return to that task.

- [ ] **Step 2: Run make check-upstream**

```bash
make check-upstream
```

Expected: `PASS - current pin 1.20.4 matches latest PyPI release`. If `OUTDATED`, evaluate whether to bump before release.

- [ ] **Step 3: Verify all skill frontmatter parses**

```bash
for skill_md in skills/*/SKILL.md; do \
  echo "=== $skill_md ==="; \
  head -10 "$skill_md" | grep -E "^description:|^last-validated:|^argument-hint:|^disable-model-invocation:"; \
done
```

Expected: each file shows its frontmatter fields. Note any missing `last-validated` and add them.

- [ ] **Step 4: Verify all skills under 500 lines**

```bash
wc -l skills/*/SKILL.md | sort -rn | head -10
```

Expected: largest skill under 500 lines. If any exceeds, refactor that skill (split into supporting files or trim).

- [ ] **Step 5: Run plugin-validator agent**

Invoke the `plugin-dev:plugin-validator` agent with the current repo state. Address any structural issues it reports.

- [ ] **Step 6: Commit any validation-driven fixes (if needed)**

```bash
git add -p
git commit -m "Validation pass - frontmatter and line-count fixes"
```

---

### Task 40: Test smoke checklist (manual)

**Files:** N/A (manual testing)

- [ ] **Step 1: Restart Claude Code session to pick up new plugin version**

In a separate Claude Code session, install the local plugin path or reload.

- [ ] **Step 2: Run /scribe:auth-status**

Expected: lists currently authenticated accounts.

- [ ] **Step 3: Invoke at least 3 workflow skills with synthetic data**

Suggested:

- `/scribe:daily-briefing` - should produce a summary across accounts.

- `/scribe:meeting-prep` - should produce a prep doc.

- `/scribe:smart-reply "test contact" "test topic"` - should produce a draft.

Record any tool-call failures or prose issues. Fix in their respective skill files. Re-commit.

- [ ] **Step 4: Test natural-language orchestration (no slash command)**

Type "check my inbox and calendar for today" - confirm workspace skill loads and routes correctly to gmail + calendar skills.

- [ ] **Step 5: Commit smoke-test fixes if any**

```bash
git status
# If fixes needed:
git add -p
git commit -m "Smoke-test fixes"
```

---

### Task 41: Merge feature branch to main and release

**Files:** N/A (git operations)

- [ ] **Step 1: Switch to main and merge**

```bash
git checkout main
git pull
git merge feature/v1-workspace-suite --no-ff -m "Merge v1.0 workspace suite expansion"
```

- [ ] **Step 2: Verify clean tree and run final validate**

```bash
git status
make validate
make check-upstream
```

Expected: clean tree, validate passes, upstream pin OK.

- [ ] **Step 3: Run make publish**

```bash
make publish VERSION=1.0.0
```

This triggers the Makefile publish flow - validates, bumps version (already 1.0.0, no-op), commits version bump (or skips if already at target), tags v1.0.0, pushes main and tag, creates GitHub release with auto-generated notes.

Expected output ending in `DONE - https://github.com/juliandickie/scribe-plugin/releases/tag/v1.0.0`.

- [ ] **Step 4: Override release notes with custom content**

Auto-generated notes are usually thin for a major release. Override:

```bash
gh release edit v1.0.0 --notes "$(cat <<'EOF'
# Scribe v1.0.0 - Full Workspace Suite

The biggest release since the initial plugin. Scribe is now a complete Google Workspace orchestration layer with 10 service skills, 14 named workflow commands, and a refactored orchestration router.

## What's new

**14 named workflow commands** for cross-service operations:

- `/scribe:daily-briefing` - inbox + calendar morning sweep
- `/scribe:inbox-triage` - categorise, label, draft replies
- `/scribe:support-scan` - support inbox to tracking sheet + drafts
- `/scribe:meeting-prep` - prep doc with related emails
- `/scribe:thread-to-doc` - email thread to Doc + attachments to folder
- `/scribe:client-digest` - full activity digest for a client
- `/scribe:weekly-wrap` - weekly summary across services
- `/scribe:follow-up-tracker` - find unanswered sent emails
- `/scribe:contact-onboard` - bootstrap folder + Contact + Sheet + welcome
- `/scribe:doc-chase` - nudge inactive doc reviewers
- `/scribe:attach-vault` - organise email attachments into Drive
- `/scribe:event-recap` - post-meeting notes doc + follow-up
- `/scribe:smart-reply` - contextual draft from prior history
- `/scribe:educator-setup` - bootstrap educator's Drive structure

**10 service skills** - one per Google service - now auto-activate to give Claude per-service MCP tool API depth.

**Three-layer skill architecture** - orchestration router + service skills + workflow skills - keeps each skill focused under 500 lines and ensures Claude loads the right context per request.

**Cross-plugin composition** - workflow skills include "if ClickUp/Slack/Spiffy/AC Builder plugin is installed..." prose hints so Claude chains across plugins naturally.

**Multi-account orchestration** - explicit multi-account intent triggers auto-loop across all authenticated accounts. Ambiguous intent prompts once.

## Upgrading from 0.x

The install command is the same. After upgrading, run `/scribe:auth-status` to confirm existing tokens still work. Existing tokens cover the broader scope set the v1.0 tool list requests, but if you see "Scope not authorized" errors on a specific service, re-run `/scribe:auth-add EMAIL` for that account.

## Documentation

- Workflows reference - [docs/workflows.md](docs/workflows.md)
- Services reference - [docs/services.md](docs/services.md)
- Multi-org setup - [docs/multi-org-setup.md](docs/multi-org-setup.md)

## Credits

Wraps [`workspace-mcp@1.20.4`](https://pypi.org/project/workspace-mcp/) by [@taylorwilsdon](https://github.com/taylorwilsdon). The breadth of this release is possible because of his work on the underlying MCP server.
EOF
)"
```

- [ ] **Step 5: Verify release page renders correctly**

```bash
open https://github.com/juliandickie/scribe-plugin/releases/tag/v1.0.0
```

Expected: release page shows custom notes, asset includes source zip.

- [ ] **Step 6: Delete the feature branch (optional)**

```bash
git branch -d feature/v1-workspace-suite
git push origin --delete feature/v1-workspace-suite
```

---

## Self-review checklist (for plan author, not executor)

After all tasks complete, the executor verifies:

1. **Spec coverage** - each spec section maps to at least one task.

   - Architecture three-layer - Task 9 (workspace) + Tasks 12-21 (services) + Tasks 22-35 (workflows). Covered.

   - Plugin manifest changes - Task 3. Covered.

   - auth-init updates - Task 6. Covered.

   - auth-add updates - Task 7. Covered.

   - Documentation - Tasks 36, 37, 38. Covered.

   - Upstream maintenance cadence - Task 2 (Makefile check-upstream target). Documented in CLAUDE.md and as monthly ritual via Task 8.

   - Resolved decisions (arg syntax, account selection, last-validated, scope posture) - encoded in workspace/SKILL.md (Task 9) and each skill template (Tasks 10, 11). Covered.

   - Web research findings - 500-line limit enforced in Task 39 Step 4, description-as-trigger discipline encoded in templates. Covered.

   - Risks - skill collision risk addressed in workspace description tuning (Task 9) and Task 39 validation. Upstream pin lag addressed in Task 1 Step 3. Covered.

2. **Placeholder scan** - search the plan for "TBD", "TODO", "implement later", "fill in", "[...]". None should remain except the documented template placeholders in Tasks 10 and 11 (template files explicitly contain `{...}` placeholders that get filled in subsequent tasks).

3. **Type consistency** - skill directory names match across plan and Makefile validate target. Workflow command names match between spec, README, workflows.md, plan task list, and Makefile.

4. **Frequent commits** - 41 tasks produce roughly 35-40 commits. Each task ends in a commit. No batched changes.

If the executor finds any gap during execution, surface it before proceeding past the affected task.

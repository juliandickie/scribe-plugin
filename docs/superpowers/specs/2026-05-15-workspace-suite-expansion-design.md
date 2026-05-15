# Scribe v1.0 - Full Workspace Suite Expansion

Spec date - 2026-05-15. Status - design phase, awaiting plan.

## Summary

Expand Scribe from a Drive/Docs-focused plugin into a complete Google Workspace orchestration layer. Enable all twelve tool groups exposed by `workspace-mcp`, restructure the skill architecture into a three-layer model (orchestration router, service skills, workflow skills), and ship fourteen named workflow slash commands that compose multi-account, cross-service operations. Position Scribe v1.0 as the canonical Workspace plugin for Claude Code.

## Goals

- Enable the full workspace-mcp tool surface (currently only four of twelve tool groups are enabled).

- Provide deep per-service tool guidance via service-specific auto-activated skills, so Claude can correctly route any Workspace request without hand-holding.

- Ship a curated catalog of named workflow skills for the highest-frequency cross-service patterns (daily briefing, inbox triage, support scan, etc.), each user-invokable via `/scribe:<workflow-name>`.

- Preserve multi-account capability and make multi-account looping a first-class pattern in the orchestration layer.

- Keep Scribe focused on Google Workspace. Cross-plugin orchestration with ClickUp, Spiffy, ActiveCampaign Builder, Slack, etc. happens via prose hints and Claude's natural skill composition, not by bundling other plugins' tools into Scribe.

## Non-goals

- Building a meta-orchestration plugin that composes Scribe with other plugins. Flagged as a follow-up project.

- Modifying upstream `workspace-mcp` Python code. Any tool-level bugs surfaced during this work go to the upstream repo as separate issues or PRs, not into the Scribe expansion.

- Adding automated tests. Skills are prose; the existing `make validate` plus the `plugin-dev:plugin-validator` agent cover structural checks.

- Per-skill telemetry. Worth doing in v1.1 once usage patterns emerge, but not v1.0.

## Architecture - three-layer skill model

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1 - Orchestration (auto-activated, broad description)      │
│   workspace/SKILL.md - routing, multi-account, chaining patterns │
└─────────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
┌───────────────────┐ ┌──────────────┐ ┌─────────────────────┐
│ LAYER 2 - Service │ │ ...10 total  │ │ LAYER 3 - Workflow  │
│ (auto-activated,  │ │              │ │ (user-invoked,      │
│  narrow desc)     │ │              │ │  disable-model-     │
│                   │ │              │ │  invocation: true)  │
│ gmail/SKILL.md    │ │              │ │ ...14 total         │
│ calendar/SKILL.md │ │              │ │                     │
│ sheets/SKILL.md   │ │              │ │ daily-briefing      │
│ slides/SKILL.md   │ │              │ │ inbox-triage        │
│ docs/SKILL.md     │ │              │ │ support-scan        │
│ drive/SKILL.md    │ │              │ │ meeting-prep        │
│ contacts/SKILL.md │ │              │ │ thread-to-doc       │
│ tasks/SKILL.md    │ │              │ │ ...                 │
│ forms/SKILL.md    │ │              │ │                     │
│ chat/SKILL.md     │ │              │ │                     │
└───────────────────┘ └──────────────┘ └─────────────────────┘
```

Layer 1 (orchestration) loads on every Workspace-context turn. It teaches Claude how to think about routing - which account, which service, which order. It does not contain per-tool API details.

Layer 2 (service skills) load when the user's prompt mentions a specific service (or the orchestration skill defers to one). Each service skill teaches the MCP tool API for that service - parameter shapes, common patterns, gotchas.

Layer 3 (workflow skills) only load when the user explicitly invokes the slash command. Each workflow skill is a complete, reproducible recipe for one named cross-service operation.

## Layer 1 - Orchestration (workspace/SKILL.md)

The current `workspace/SKILL.md` is refactored from a tool reference into a routing and orchestration guide. Body sections:

**Multi-account routing** - rules for picking which account to use. Priority order: explicit user mention, then client/contact context (AHPRA-style profile.md `google_account_email` frontmatter, Contacts lookup), then default account. When a workflow spans accounts, document the loop pattern - call `list_authenticated_accounts` first, iterate, accumulate.

**Cross-service chaining patterns** - canonical sequences for the most common multi-step shapes:

- Email to Doc - search Gmail, get_thread, create Doc with thread content, save attachments to Drive folder via `import_to_google_doc` or `create_drive_file`.

- Calendar to Doc - list_events for window, get_event details, create prep Doc with structured sections.

- Sheet logging - append_row pattern with timestamp + source link.

- Drive activity scan - list comments, find suggested edits, surface to user.

**Service skill delegation** - explicit pointers ("for Gmail-specific tool details, see the gmail skill auto-activated alongside this one"). Avoids duplicating per-service knowledge.

**Cross-plugin composition** - guidance for when other plugins are present. Examples - if user mentions ClickUp tasks, defer task creation to the ClickUp plugin; if Slack plugin is available, use it for posting summaries; if Spiffy plugin is available, defer course-credit and coupon operations to it. Scribe never tries to talk to non-Google APIs directly.

**Sandbox and attachment rules** - inherited from current skill. `~/.workspace-mcp/attachments` sandbox, auto-copy pattern for outside-sandbox files, `realpath` resolution makes symlinks unsafe.

**Setup precondition checks** - if no accounts authenticated (via `list_authenticated_accounts` call returning empty), route the user to `/scribe:auth-init` rather than failing on first MCP call.

Target length - under 250 lines. Loads cheaply on every Workspace-context turn.

## Layer 2 - Service skills (10 files)

Each service skill is a new directory under `skills/` with auto-activation enabled (no `disable-model-invocation` flag). The frontmatter `description` is narrow enough that the skill only activates when its specific service is in scope.

| Skill directory | Triggers on | Teaches |
|---|---|---|
| gmail/ | email, inbox, message, thread, label, draft, send, reply | search_messages, get_thread, draft, send, label management, batch operations, thread patterns |
| calendar/ | calendar, event, meeting, schedule, availability, free/busy | list_events, get_event, manage_event create/update, query_freebusy, list_calendars, focus time, OOO management |
| sheets/ | spreadsheet, sheet, rows, columns, data, csv | read range, write cells, create sheet, append row, formula patterns, table_with_data |
| slides/ | presentation, deck, slide, slideshow | read presentation, create slide, update slide content, layout patterns |
| docs/ | google doc, document, tab, doc structure | extracted from current workspace/SKILL.md and expanded - manage_doc_tab actions, find_and_replace, batch_update, headers/footers, comments |
| drive/ | drive, folder, file, upload, share, permissions | extracted from current workspace/SKILL.md and expanded - search_drive_files, list_drive_items, create_drive_folder, manage_drive_access, permissions, public access checks |
| contacts/ | contact, person, address book | read contacts, create contact, search contacts, contact metadata |
| tasks/ | task, to-do, checklist, action item | read tasks, create tasks, complete tasks, task list management |
| forms/ | form, survey, response, questionnaire | read form responses, create forms, response analytics |
| chat/ | google chat, chat message, chat space | read/send Chat messages, space management |

Each service skill follows a consistent template:

1. Frontmatter - description (narrow), no disable-model-invocation flag.

2. What this skill does - one sentence.

3. When to use - bullet list of trigger contexts.

4. Tool reference - each MCP tool with parameter shapes and one-line purpose.

5. Common patterns - 2-5 named patterns with the exact tool call sequence.

6. Gotchas - service-specific quirks (e.g. Gmail label IDs vs names, Calendar timezone handling, Sheets A1 vs R1C1 notation).

7. Account selection - reminder to pass `user_google_email` and how to determine the right one.

The docs/ and drive/ skills extract content from the current workspace/SKILL.md (which currently embeds both). After extraction, workspace/SKILL.md no longer contains per-tool details for any service - it pure orchestration.

## Layer 3 - Workflow skills (14 files)

Each workflow skill is a new directory under `skills/` with `disable-model-invocation: true` so it only runs when the user explicitly invokes the slash command. Each is a complete recipe.

### Catalog

| Slash command | Services | What it does |
|---|---|---|
| /scribe:daily-briefing | Gmail + Calendar | Scan all authenticated inboxes for unread/flagged, pull today's calendar events, surface urgent items with context |
| /scribe:inbox-triage | Gmail | Scan all accounts, categorise by urgency/sender, apply labels, draft replies to flagged threads |
| /scribe:support-scan | Gmail + Sheets | Scan designated support inbox(es) for new inquiries, log to a tracking sheet, draft initial responses |
| /scribe:meeting-prep | Calendar + Gmail + Docs | Pull next or named meeting, find related emails, create a structured prep doc in Drive |
| /scribe:thread-to-doc | Gmail + Drive + Docs | Convert an email thread into a structured Google Doc, save attachments into a client/contact subfolder |
| /scribe:client-digest | Gmail + Calendar + Drive | Aggregate emails, calendar events, and Drive activity (comments, suggestions, edits) for a named client or contact |
| /scribe:weekly-wrap | Gmail + Calendar + Drive + Sheets | Compile week's emails, events, created/edited docs into a summary report doc |
| /scribe:follow-up-tracker | Gmail | Find sent emails with no reply after X days, surface them with draft follow-ups |
| /scribe:contact-onboard | Gmail + Drive + Sheets + Contacts | Given a name and email, create Drive folder, add Contacts entry, log to a sheet, draft welcome email |
| /scribe:doc-chase | Drive + Docs + Gmail | Find shared Docs with no recent comment/edit activity, draft reminder emails to reviewers |
| /scribe:attach-vault | Gmail + Drive | Scan inboxes for emails with attachments, organise attachments into Drive folders by sender or project |
| /scribe:event-recap | Calendar + Gmail + Docs | Post-meeting - pull attendee emails, create notes/action-items doc, draft follow-up email |
| /scribe:smart-reply | Gmail + Contacts | Given a contact name and topic, pull prior email history for context, draft a contextual reply |
| /scribe:educator-setup | Drive + Docs + Sheets + Gmail | Bootstrap a Drive folder structure for a new educator - curriculum folder, planning doc, course tracker sheet, welcome email draft |

### Workflow skill template

Each workflow skill file follows a consistent template:

1. Frontmatter - description (specific to the workflow), `disable-model-invocation: true`, `argument-hint` string for any parameters.

2. What this workflow does - one paragraph.

3. Parameters - what the user can pass on invocation (account email, date range, client name, folder ID, etc.) and what defaults apply when omitted.

4. Tool call sequence - the exact MCP tool calls in order, with parameter notes.

5. Multi-account behavior - whether the workflow loops over all accounts or uses a single specified one.

6. Cross-plugin composition - "if the ClickUp plugin is installed, also create a ClickUp task" / "if the Slack plugin is installed, also post a summary to channel X". This is the prose-hint pattern that lets Claude compose Scribe with other plugins without code coupling.

7. Example invocations - 2-3 natural language examples showing how to call the skill and what happens.

8. Failure modes - what to do if no matching emails found, no inbox connected, sandbox rejection, etc.

## Plugin manifest changes (.claude-plugin/plugin.json)

Update the `mcpServers.scribe.args` array from:

```json
["workspace-mcp@1.20.4", "--tools", "drive", "docs", "gmail", "calendar"]
```

to:

```json
["workspace-mcp@<latest>", "--tools", "appscript", "calendar", "chat", "contacts", "docs", "drive", "forms", "gmail", "search", "sheets", "slides", "tasks"]
```

Bump `version` to `1.0.0` in plugin.json. Bump matching version in `.claude-plugin/marketplace.json` `plugins[0].version`.

Update `description` in plugin.json to reflect full Workspace scope - "Google Workspace orchestration for Claude Code - Gmail, Calendar, Docs, Drive, Sheets, Slides, Contacts, Tasks, Forms, Chat. Multi-account OAuth. Wraps taylorwilsdon/google_workspace_mcp."

Update `keywords` to include - sheets, slides, contacts, tasks, forms, chat, workflows, automation.

The `--permissions` flag is NOT used in v1.0. The reasoning - using `--tools` enables the full surface with sensible default scopes per service. Switching to `--permissions` requires per-service level decisions that vary by user. Document `--permissions` as an advanced override in `auth-init/SKILL.md` for users who want to restrict scopes. Revisit in v1.1 if marketplace users push back on scope breadth.

## auth-init/SKILL.md changes

Section 2 (Enable required APIs) becomes a longer list - all twelve services. Mark Drive, Docs, Gmail, Calendar as recommended; mark Sheets, Slides, Contacts, Tasks, Forms, Chat, AppScript, Search as optional but enable-them-if-you-want-the-workflow-to-work.

Section 6 (Authenticate via Claude Code) - update the `service_name` parameter docs. Add a paragraph explaining that calling `start_google_auth` once with `service_name=drive` covers the broad scope set the server requests by default, but if the user later sees scope errors on a specific service they can re-auth with that service_name.

New section after Troubleshooting - "Restricting scopes" - documents the `--permissions SERVICE:LEVEL` flag and how to add it to `~/.claude/settings.json` MCP env config to override the default `--tools` behavior. Examples for read-only mode, gmail-readonly mode, etc.

## Documentation changes

**README.md** - rewrite headline section. Currently "push markdown to Drive" framing. New framing - "Google Workspace orchestration for Claude Code." Add new sections:

- Workflows - bulleted list of all 14 named slash commands with one-line descriptions and example invocations.

- Services - bulleted list of all 10 service skills with what each enables.

- Skills section reorganized to reflect the three-layer model.

- Multi-org section stays as-is.

**CLAUDE.md** - update for v1.0:

- Current state block - bump version, update pin, update skill count.

- Skills - the modern shape - rewrite to describe three-layer architecture.

- Don't do this - add "Don't bundle other plugins' MCP tools into Scribe. Cross-plugin chaining happens via prose hints and Claude's natural skill composition, not code coupling."

- Important conventions - new subsection "Cross-plugin composition" describing the prose-hint pattern.

- Quick orientation - add `make validate` should now pass with 30 skill directories.

**docs/workflows.md** - new file. Detailed reference for each of the 14 workflow skills. Longer than each SKILL.md prose - includes worked examples with sample data, step-by-step output for each tool call, common failure modes and recovery patterns.

**docs/services.md** - new file. Per-service tool reference with all parameters, all tools, all return shapes. Mirrors the per-service skill files but as a flat reference for users browsing rather than Claude routing.

## Versioning and release

Version - **v1.0.0**. Major bump from 0.x signals stable, complete suite to marketplace users.

Release commit message - "Release v1.0.0 - full Google Workspace suite (10 services, 14 workflows)."

`make publish VERSION=1.0.0` workflow:

1. Substantive changes commit (skills, manifest tools array, README, CLAUDE.md updates) goes first under its own commit.

2. Then `make publish VERSION=1.0.0` does the version-bump commit, tag, push, GitHub release.

GitHub release notes - draft custom (not auto-generated) given the scope of the change. Highlight the three-layer architecture, list the 14 workflow commands, link to docs/workflows.md, note the upstream pin, link to issue #771 for users who want scope restriction.

## Validation

`make validate` updated to verify all 30 skill directories exist and each contains a SKILL.md with valid frontmatter (description present, frontmatter parses).

Manual smoke test checklist documented in CLAUDE.md - invoke each of the 14 workflow skills once with synthetic data, verify the expected MCP tool calls fire, verify outputs land in expected Drive locations.

`plugin-dev:plugin-validator` agent run after the manifest changes to catch schema-level issues.

## Out of scope - flagged as follow-up projects

- **Meta-orchestration plugin** - composes Scribe with ClickUp, Spiffy, ActiveCampaign Builder, Slack into named cross-system workflows. Own repo, own design cycle. Working name TBD.

- **Per-skill telemetry** - count workflow invocations to inform v1.1 priorities. Requires opt-in instrumentation.

- **Workflow templates as upstream feature** - propose to taylorwilsdon as a workspace-mcp capability if the workflow pattern proves broadly useful.

- **`--permissions` granular control as a setup option** - in v1.0 it's documented as an advanced override only. v1.1 could add a `/scribe:permissions` command that helps users construct a permissions string interactively.

- **AppScript and Search service skills** - included in --tools at the manifest level so the MCP tools are available, but no dedicated service skill in v1.0. Add in v1.1 if usage warrants.

## File-level change inventory

```
.claude-plugin/plugin.json                   modify - version, args, description, keywords
.claude-plugin/marketplace.json              modify - version
hooks/post-install.sh                        modify - WORKSPACE_MCP_VERSION pin
README.md                                    rewrite headline, add Workflows + Services sections
CLAUDE.md                                    modify - architecture, skills shape, don'ts
docs/multi-org-setup.md                      no change
docs/workflows.md                            new file
docs/services.md                             new file
docs/superpowers/specs/2026-05-15-...md      this file (new)
skills/workspace/SKILL.md                    rewrite as orchestration router
skills/auth-init/SKILL.md                    modify - APIs list, scopes appendix
skills/auth-add/SKILL.md                     modify - update pin reference
skills/auth-status/SKILL.md                  no change
skills/push/SKILL.md                         no change
skills/client-resolve/SKILL.md               no change
skills/gmail/SKILL.md                        new
skills/calendar/SKILL.md                     new
skills/sheets/SKILL.md                       new
skills/slides/SKILL.md                       new
skills/docs/SKILL.md                         new
skills/drive/SKILL.md                        new
skills/contacts/SKILL.md                     new
skills/tasks/SKILL.md                        new
skills/forms/SKILL.md                        new
skills/chat/SKILL.md                         new
skills/daily-briefing/SKILL.md               new
skills/inbox-triage/SKILL.md                 new
skills/support-scan/SKILL.md                 new
skills/meeting-prep/SKILL.md                 new
skills/thread-to-doc/SKILL.md                new
skills/client-digest/SKILL.md                new
skills/weekly-wrap/SKILL.md                  new
skills/follow-up-tracker/SKILL.md            new
skills/contact-onboard/SKILL.md              new
skills/doc-chase/SKILL.md                    new
skills/attach-vault/SKILL.md                 new
skills/event-recap/SKILL.md                  new
skills/smart-reply/SKILL.md                  new
skills/educator-setup/SKILL.md               new
Makefile                                     modify - validate target counts new skill dirs
```

Total - 9 modify, 27 new, 4 unchanged. Across 30 skill directories after the expansion (6 existing + 10 service + 14 workflow).

## Risks and open questions

**Risk - skill collision in auto-activation.** With 11 auto-activated skills (workspace + 10 service skills), Claude may load multiple simultaneously when context is ambiguous. Mitigation - keep service skill descriptions narrow (specific service nouns), keep workspace skill description broad-but-distinct (orchestration/multi-service/routing language). Test by invoking ambiguous prompts and checking which skills load.

**Risk - OAuth scope breadth.** Enabling all 12 tool groups requests broad scopes. New users may balk at the consent screen. Mitigation - document `--permissions` override clearly in auth-init for users who want to restrict, link to upstream issue #771 for scope discussion.

**Risk - upstream pin lag.** New workspace-mcp release between spec and ship. Mitigation - check for latest release at the start of implementation, pin to whatever is current then, document the pin date in CLAUDE.md current-state block.

**Open question - workflow skill argument syntax.** Should multi-arg workflows use named flags (`/scribe:meeting-prep --event "Q3 planning"`) or positional args (`/scribe:meeting-prep "Q3 planning"`)? Lean toward named flags for consistency with current `/scribe:push` flag pattern, but worth confirming when writing the implementation plan.

**Open question - account selection UX.** When a workflow loops over all accounts, should it auto-loop or prompt the user? Lean toward auto-loop with summary output ("scanned 3 accounts, found 12 unread"), but worth confirming.

**Open question - workflow skill versioning when plugin bumps.** When v1.1 ships and adds 3 new workflow skills, do existing workflow skills carry version metadata? Probably not in v1.0 - revisit if backward compatibility becomes an issue.

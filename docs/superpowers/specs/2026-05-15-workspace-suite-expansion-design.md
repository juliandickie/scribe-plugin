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

1. Frontmatter - description (narrow, specific service nouns - the "trigger not documentation" rule), `last-validated` date, no `disable-model-invocation` flag.

2. What this skill does - one sentence.

3. When to use - bullet list of trigger contexts using language a user would actually type.

4. Tool reference - each MCP tool with parameter shapes and one-line purpose.

5. Common patterns - 2-5 named patterns with the exact tool call sequence.

6. Gotchas - service-specific quirks (e.g. Gmail label IDs vs names, Calendar timezone handling, Sheets A1 vs R1C1 notation).

7. Account selection - reminder to pass `user_google_email` and how to determine the right one (links back to `workspace/SKILL.md` Multi-account routing rules).

Target body length 200-400 lines per service skill. Anything longer splits into supporting files in the skill directory (progressive disclosure pattern).

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

1. Frontmatter - description (specific trigger phrase a user would type), `disable-model-invocation: true`, `argument-hint` string for parameters (named flags pattern for multi-arg workflows, positional for single-arg), `last-validated` date.

2. What this workflow does - one paragraph.

3. Parameters - what the user can pass on invocation (account email, date range, client name, folder ID, etc.) and what defaults apply when omitted. Both natural-language and explicit-args invocation styles documented.

4. Tool call sequence - the exact MCP tool calls in order, with parameter notes.

5. Multi-account behavior - whether the workflow loops over all accounts or uses a single specified one. Defers to the rule in `workspace/SKILL.md` for selection logic.

6. Cross-plugin composition - "if the ClickUp plugin is installed, also create a ClickUp task" / "if the Slack plugin is installed, also post a summary to channel X". This is the prose-hint pattern that lets Claude compose Scribe with other plugins without code coupling.

7. Example invocations - 2-3 natural language examples plus 1 explicit-args example showing how to call the skill and what happens.

8. Failure modes - what to do if no matching emails found, no inbox connected, sandbox rejection, etc.

Target body length 100-300 lines per workflow skill.

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
Makefile                                     modify - validate target, new check-upstream target
.github/workflows/upstream-check.yml         optional new - weekly automation, deferred decision
```

Total - 9 modify, 27 new (28 if upstream-check workflow ships in v1.0), 4 unchanged. Across 30 skill directories after the expansion (6 existing + 10 service + 14 workflow).

## Resolved decisions (revised 2026-05-15 after feedback)

These were open questions in the initial draft; resolved after second-pass review.

### Decision - argument syntax for workflow skills

Use the `argument-hint` frontmatter field (per current Claude Code skill spec) with **named flags for any workflow that has more than one parameter, positional for single-arg workflows**.

Rationale - based on current best practice docs, `argument-hint` populates the slash command autocomplete menu, and `$ARGUMENTS` captures the full string (named flags survive). Most invocations will be natural language (Claude populating the arguments from intent), so the syntax matters most as readable documentation. Named flags are self-documenting in the slash autocomplete; positional is concise for one-arg cases.

Examples:

- `/scribe:meeting-prep [--event "Q3 planning"] [--account email]` - named flags
- `/scribe:contact-brief NAME-OR-EMAIL` - positional, single arg
- `/scribe:thread-to-doc [--thread-id ID] [--client CLIENT-ID]` - named flags
- `/scribe:weekly-wrap [--week current|last|N] [--output-folder ID]` - named flags

Each workflow skill's body documents both natural-language and explicit-args invocation styles.

### Decision - account selection behavior

- Explicit multi-account intent in user prompt ("check both my inboxes", "across all my accounts", "for julian@idd and julian@pro") - auto-loop across all matching accounts, do not prompt.

- Single account authenticated - use it, do not prompt.

- Client or contact context implies an account (AHPRA profile.md, Contacts lookup) - use it, do not prompt.

- Ambiguous intent with multiple accounts authenticated ("check my inbox") - prompt the user once to clarify, then remember within the conversation.

Document this rule in `workspace/SKILL.md` under "Multi-account routing." Each workflow skill links back to this rule rather than re-stating it.

### Decision - per-skill versioning

No per-skill semver versions. Skills are prose, not API surfaces, so semantic versioning per skill creates maintenance overhead without payoff.

Instead - each SKILL.md frontmatter includes an optional `last-validated` field (ISO date) recording when the skill was last smoke-tested against the current upstream pin. This serves the actual maintenance need: "which skills haven't been touched since upstream changed?" The plugin's git history covers per-skill change tracking.

`make validate` checks that `last-validated` dates exist and warns if any skill is older than the current upstream pin date.

### Decision - OAuth scope breadth posture

Not treated as a risk. Initial users are internal; they expect the full scope grant as part of the value proposition. README messaging stays positive (does not apologise for scope breadth). The `--permissions` override is documented in `auth-init/SKILL.md` as an advanced option for users who want to restrict, not foregrounded.

## Upstream maintenance cadence (new section)

Regular upstream-version check is now a first-class maintenance ritual, not an ad-hoc activity.

### Implementation

Add a `make check-upstream` target that queries the PyPI JSON API for the latest `workspace-mcp` release, compares against the pinned version in `plugin.json`, and prints status. The PyPI JSON endpoint is `https://pypi.org/pypi/workspace-mcp/json`.

```makefile
check-upstream:
	@current=$$(jq -r '.mcpServers.scribe.args[0]' .claude-plugin/plugin.json | sed 's/workspace-mcp@//'); \
	latest=$$(curl -s https://pypi.org/pypi/workspace-mcp/json | jq -r '.info.version'); \
	if [ "$$current" = "$$latest" ]; then \
		echo "PASS - current pin $$current matches latest PyPI release"; \
	else \
		echo "OUTDATED - current pin $$current, latest is $$latest"; \
		echo "Review changelog at https://github.com/taylorwilsdon/google_workspace_mcp/releases"; \
	fi
```

### Cadence

- **Monthly minimum** - `make check-upstream` is documented in CLAUDE.md as a monthly maintenance ritual.

- **Pre-release** - run before every `make publish` cycle to catch unannounced upstream changes.

- **Optional automation** - a GitHub Actions workflow (`.github/workflows/upstream-check.yml`) can run weekly and open an issue if drift is detected. Decision deferred to implementation phase; not blocking v1.0.

### Update workflow when outdated

When `make check-upstream` reports drift:

1. Read the upstream release notes at https://github.com/taylorwilsdon/google_workspace_mcp/releases for the diff range.

2. Identify breaking changes (tool renames, parameter changes, scope additions).

3. If breaking, bump Scribe's MINOR or MAJOR version per the impact.

4. Update the pin in all five files (per CLAUDE.md "Pinning to a new upstream version" section).

5. Run `make validate` and smoke-test affected workflow skills.

6. Update `last-validated` date in skill frontmatter for any skill whose behavior could be affected.

7. `make publish VERSION=<new-version>`.

## Current best-practice findings (from web research 2026-05-15)

The web search surfaced several current best practices worth pinning down for this spec:

**Skill description as trigger, not documentation.** Each service and workflow skill's `description` frontmatter must be specific enough that Claude reliably picks the right skill. Vague descriptions cause skills to silently never fire OR to fire on the wrong context. For our 11 auto-activated skills (workspace + 10 service), each description must use distinct service-specific nouns to avoid collision.

**Frontmatter limits.** `name` max 64 characters, lowercase letters/numbers/hyphens only, no XML tags, no reserved words. `description` max 1024 characters, non-empty. All proposed skill names in this spec fit.

**Body length target.** Keep each SKILL.md under 500 lines for optimal performance. Service skills should aim for 200-400 lines. Workflow skills should aim for 100-300 lines. Long content goes into supporting files in the skill directory and loads only on demand (progressive disclosure).

**disable-model-invocation behavior.** Setting `disable-model-invocation: true` blocks Claude from auto-triggering. User can still invoke via slash command. (There is an open GitHub issue #26251 reporting that some configurations may also block user invocation; the current Scribe plugin's five disable-model-invocation skills all work correctly, so this appears to be a configuration-specific bug not affecting our pattern.)

**Argument capture.** `$ARGUMENTS` captures everything after the slash command as a single string. `$0`, `$1`, `$2` capture space-separated tokens. Named flags work because the full argument string is available to the skill prose; the skill can parse out `--event "Q3 planning"` from the arguments string.

**Schema validation.** Unofficial JSON schemas exist at schemastore.org for `claude-code-plugin-manifest.json` and `claude-code-marketplace.json`. The `plugin-dev:plugin-validator` agent uses these for schema-level checks. Add to the validation step in the plan.

## Risks (revised - shorter)

**Risk - skill collision in auto-activation.** With 11 auto-activated skills, Claude may load multiple simultaneously when context is ambiguous. Mitigation - tight, distinct descriptions per current best practice (the description-as-trigger rule). Manual test - invoke ambiguous prompts during development and verify the right single skill loads.

**Risk - upstream pin lag.** New workspace-mcp release between spec and ship. Mitigation - `make check-upstream` immediately before implementation start; pin to whatever is current then.

(OAuth scope breadth de-risked per the resolved decision above.)

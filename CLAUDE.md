# Scribe Plugin

Context document for AI agents and contributors picking up this project in a new session. The README.md is for end users; this file is for whoever is editing the repo. Last refreshed 2026-05-15.

## What this project is

A Claude Code plugin that wraps [taylorwilsdon's `workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) (Python, on PyPI). The plugin contributes -

- 30 skills (`skills/<name>/SKILL.md`) organised in a three-layer architecture (orchestration router + 10 auto-activated service skills + 14 user-invokable workflow skills + 5 existing infra skills) that teach Claude when and how to use the MCP tools.

- An MCP server declaration (`mcpServers` block in plugin.json) that uvx-pulls a pinned version of `workspace-mcp` from PyPI and pre-configures three env vars so the credential flow works out of the box.

- Documentation, install hooks, and a multi-org switching helper script.

The plugin's distinctive value is the integration polish, not the underlying MCP server's capability. The capability is upstream's. We made the install one command, the OAuth setup five minutes, and the cross-Workspace-org workflow tractable.

## Current state - as of 2026-05-15

- **Plugin version** - 1.0.0 (in plugin.json + marketplace.json)
- **Pinned upstream version** - `workspace-mcp@1.20.4` from PyPI
- **Distribution** - GitHub at `juliandickie/scribe-plugin`, public, MIT licensed, with v1.0.0 release tagged
- **Marketplace install** - `/plugin marketplace add juliandickie/scribe-plugin` then `/plugin install scribe`
- **Direct download** - `https://github.com/juliandickie/scribe-plugin/archive/refs/tags/v1.0.0.zip`
- **Skill count** - 30 (6 existing infra + 1 orchestration + 10 service + 14 workflow)
- **Tools enabled** - all 12 workspace-mcp tool groups

## Architecture - where this fits in the broader ecosystem

Two repositories. This plugin and the upstream MCP server it wraps.

```
┌──────────────────────────────────────────────────────────────────────┐
│ taylorwilsdon/google_workspace_mcp (UPSTREAM, PyPI as workspace-mcp)  │
│ Python MCP server. Owns Google API tool implementations.              │
│ Our PR #727 added the markdown-to-Docs writer; merged 2026-04-26.    │
│ Our umbrella issue #731 produced PR #742; merged 2026-05-01.         │
│ Pending - upstream issue #771 (configurable scopes, design phase).   │
└─────────────────────────────────────▲────────────────────────────────┘
                                      │ uvx pulls workspace-mcp@1.20.4
                                      │ from PyPI
                                      │
┌─────────────────────────────────────┴────────────────────────────────┐
│ juliandickie/scribe-plugin (THIS REPO)                                │
│ Claude Code plugin - 30 skills + manifest + hooks + docs.             │
│ Distributed via the official Claude Code plugin marketplace flow.     │
└──────────────────────────────────────────────────────────────────────┘
```

**Historical note.** A third repository, `juliandickie/google_workspace_mcp`, was a fork of taylorwilsdon's repo that staged PR #727 before merge. It is fully retired - no consumer pulls from it, the install path is PyPI, and it can be archived on GitHub at any time. Future contributions to upstream should be made by forking taylorwilsdon's repo directly for a single focused PR (the v1.0 path is the model), not by reactivating the old fork.

A separate downstream consumer - `juliandickie/Documents/GitHub/ahpra-writing-research-cc` - uses workspace functionality via its own scripts. That repo has its own upstream pin and is unaffected by Scribe plugin changes; treat it as out-of-scope here.

## Repo structure

```
scribe-plugin/
├── .claude-plugin/
│   ├── plugin.json              # MCP server declaration + manifest
│   └── marketplace.json         # registry entry for /plugin marketplace add
├── skills/                      # 30 skills total (three layers)
│   # Layer 1 - Orchestration (auto-activated)
│   ├── workspace/SKILL.md       # Routing brain; multi-account, chaining patterns
│   # Layer 2 - Service skills (auto-activated, narrow descriptions)
│   ├── gmail/SKILL.md           # Gmail API operations
│   ├── calendar/SKILL.md        # Calendar API operations
│   ├── docs/SKILL.md            # Google Docs operations
│   ├── drive/SKILL.md           # Drive operations
│   ├── sheets/SKILL.md          # Sheets operations
│   ├── slides/SKILL.md          # Slides operations
│   ├── contacts/SKILL.md        # People API
│   ├── tasks/SKILL.md           # Google Tasks
│   ├── forms/SKILL.md           # Google Forms
│   ├── chat/SKILL.md            # Google Chat
│   # Layer 3 - Workflow skills (user-invoked via slash command)
│   ├── daily-briefing/SKILL.md
│   ├── inbox-triage/SKILL.md
│   ├── support-scan/SKILL.md
│   ├── meeting-prep/SKILL.md
│   ├── thread-to-doc/SKILL.md
│   ├── client-digest/SKILL.md
│   ├── weekly-wrap/SKILL.md
│   ├── follow-up-tracker/SKILL.md
│   ├── contact-onboard/SKILL.md
│   ├── doc-chase/SKILL.md
│   ├── attach-vault/SKILL.md
│   ├── event-recap/SKILL.md
│   ├── smart-reply/SKILL.md
│   ├── educator-setup/SKILL.md
│   # Infra skills (user-invoked)
│   ├── auth-init/SKILL.md       # First-run OAuth setup
│   ├── auth-add/SKILL.md        # Add another account
│   ├── auth-status/SKILL.md     # List authenticated accounts
│   ├── push/SKILL.md            # BOTH user-invoked AND auto-activated
│   └── client-resolve/SKILL.md  # AHPRA-specific repo convention
├── hooks/
│   └── post-install.sh          # Optional manual pre-install of workspace-mcp
├── scripts/
│   └── switch.sh                # Multi-org OAuth client symlink switcher
├── docs/
│   ├── multi-org-setup.md       # Cross-Workspace OAuth client setup
│   ├── workflows.md             # Full reference for the 14 workflow skills
│   ├── services.md              # Full reference for the 10 service skills
│   ├── skill-templates/         # Templates for authoring new service/workflow skills
│   ├── superpowers/             # Specs and plans for major changes
│   └── images/                  # Hero/architecture/before-after/icon assets
├── Makefile                     # help/validate/check-upstream/publish/icons targets
├── README.md                    # User-facing overview
├── CLAUDE.md                    # This file - dev context
├── LICENSE                      # MIT
└── .gitignore                   # .DS_Store
```

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

**Historical note** - the skill named `scribe` was renamed to `workspace` in v0.2.0 to avoid the awkward `/scribe:scribe` invocation name. The auto-activated skill is at `skills/workspace/SKILL.md` even though the plugin name and command prefix are still `scribe`.

## Development workflow

### Make targets (run from repo root)

```bash
make help               # Self-documenting target list
make validate           # JSON parse check + skill structure check
make publish VERSION=x.y.z   # Bump version in both manifests, commit, tag, push, gh release
make icons              # Regenerate icon variants from docs/images/icon-1024.png
make release-notes      # Show commits since last tag (helps draft notes)
```

### Releasing a new version

The `make publish` target enforces a clean working tree, then runs the full publish dance -

1. Updates `version` in `.claude-plugin/plugin.json` via jq
2. Updates `plugins[0].version` in `.claude-plugin/marketplace.json` via jq
3. Validates both files still parse
4. Commits "Release vX.Y.Z"
5. Tags vX.Y.Z
6. Pushes main and tag to origin
7. Creates a GitHub release with auto-generated notes

If the working tree is dirty when you invoke it, the target stops. Commit the substantive changes first under their own commit, THEN run `make publish` so the version-bump commit is its own focused entry.

For releases with substantive changes, draft custom release notes via `gh release create` with `--notes` rather than `--generate-notes` (which the Makefile uses by default for patch releases). See the v0.2.1 and v0.3.0 releases for examples.

### Pinning to a new upstream version

When taylorwilsdon ships a new release of `workspace-mcp` -

1. Bump the pin in `.claude-plugin/plugin.json` `mcpServers.scribe.args[0]` from `workspace-mcp@1.20.4` to the new version
2. Bump the same in `hooks/post-install.sh` `WORKSPACE_MCP_VERSION="1.20.4"`
3. Bump the same in `skills/auth-init/SKILL.md`, `skills/auth-add/SKILL.md`, `docs/multi-org-setup.md` wherever the pin appears (currently 5 files total)
4. Test the update locally - install the plugin, run `/scribe:auth-status`, push a sample markdown file
5. Run `make publish VERSION=...`

Consider whether the upstream release contains breaking changes (API surface changes, scope changes, env var renames). If so, bump Scribe's MAJOR or MINOR version accordingly. Patch upstream releases (1.20.4 -> 1.20.5) typically map to patch Scribe releases (0.3.0 -> 0.3.1).

### Validation

`make validate` is a quick smoke test - JSON parse + skill file presence. For deeper validation use the `plugin-dev:plugin-validator` agent. The validator catches schema-level issues that the Makefile's grep-based check misses (e.g. unsupported manifest fields, frontmatter shape problems, missing required keys).

## Writing style rules - apply to all docs and skill files

These rules are inherited from the AHPRA project the plugin originally served. They make content survive Google Drive paste cycles cleanly and produce more readable plain-text output.

1. **No em dashes** (U+2014). Use ` - ` (space-hyphen-space) for separators, a comma for continuing thoughts, parentheses for asides, or split into two sentences.

2. **No colons in markdown headings**. Use ` - ` instead. `## Part 1 - Setup` not `## Part 1: Setup`. Colons cause filename compatibility issues when content syncs to local file systems.

3. **Blank lines between list items**. When listing things in markdown, place a full blank line between each bullet so line breaks survive when content is pasted into external apps like Google Docs.

4. **Minimum word counts only**. All length guidance is a floor, never a ceiling. Don't truncate to fit.

These rules apply to README.md, CLAUDE.md, all SKILL.md files, all docs/, all script comments, all commit messages. Run grep before committing to verify -

```bash
grep -rn $'—' README.md docs/ skills/ scripts/ hooks/ Makefile && echo "FAIL - em dashes found" || echo "PASS - no em dashes"
```

## Upstream relationship

### What's been contributed

- **PR #727** at taylorwilsdon/google_workspace_mcp - merged 2026-04-26. Added `update_tab_from_markdown` MCP tool plus markdown-writer module plus two bug fixes. Taylor refactored during merge to consolidate three tab tools into the single action-based `manage_doc_tab` (which is now the canonical surface).

- **Issue #731** - umbrella feedback report from real production use. Closed by PR #742.

- **PR #742** by taylor (closing #731) - merged 2026-05-01. Added auto-retry on transient HTTP 500s, reworded `import_to_google_doc` parameter docs, surfaced `driveId` in `list_drive_items` detailed output.

- **Issue #771** - configurable OAuth scope subset per install. Open as of 2026-05-08, awaiting taylor's design steer between Options A/B/C. Will become a PR from us once direction is chosen.

### What's in the PyPI package right now

`workspace-mcp` v1.20.4 (released 2026-05-07) includes everything from PRs #727 and #742. The plugin pins to this exact version. The next upstream release will likely be 1.20.5 or 1.21.0 depending on what taylor includes.

### How to contribute more

If a future user surfaces friction worth fixing -

1. Plugin-level fixes (skill prose, manifest, docs, install flow) - patch this repo, cut a Scribe patch release. Examples - v0.2.1 added precondition checks and sandbox docs without touching upstream.

2. MCP-server-level fixes (tool behaviour, scope handling, retry policy, new tools) - file an issue at taylorwilsdon/google_workspace_mcp first if it requires design discussion, or open a PR directly if the right answer is mechanically clear. The contribution pattern - fork taylorwilsdon's repo fresh, branch off its main, single focused PR, link any related issue. See the issue #731 and PR #742 thread for an example that worked. Do not reuse the old `juliandickie/google_workspace_mcp` fork - that was retired with v0.3.0; start from upstream.

3. AHPRA-specific workflow concerns - those go in the AHPRA repo's `scripts/gdocs/` rather than here. Don't pull AHPRA conventions into this plugin's general-purpose surface.

## Important conventions and gotchas

### Tool sandbox

The MCP server's `import_to_google_doc` enforces `ALLOWED_FILE_DIRS` (defaults to `~/.workspace-mcp/attachments` per our manifest). Files outside that path are rejected. **Symlinks do NOT bypass the sandbox** because the server resolves with `realpath()` before checking. The `skills/push/SKILL.md` walks Claude through auto-copying outside-sandbox files into `~/.workspace-mcp/attachments/scribe-session/` instead of trying symlinks.

### Multi-org OAuth

Internal-type OAuth consent screens only accept identities from the owning Workspace org. So a user with two Workspaces needs TWO OAuth clients - one per org. The `scripts/switch.sh` helper plus the symlink-swap pattern documented in `docs/multi-org-setup.md` is how Scribe handles this. Token caches at `~/.workspace-mcp/credentials/<email>.json` are self-contained and unaffected by which OAuth client is currently active, so authentication only happens once per email.

### Skills frontmatter

The `disable-model-invocation: true` flag in skill frontmatter prevents Claude from auto-triggering a skill based on context matching. Use it for skills that should ONLY run when the user explicitly types the slash command.

Where it applies in v1.0:

- **All 14 workflow skills** have `disable-model-invocation: true` (user-only invocation via slash command).

- **Infra skills** `auth-init`, `auth-add`, `auth-status`, `client-resolve` have it (one-time setup operations, not for auto-trigger).

- **The `workspace` orchestration router** does NOT have it (auto-activates on every Workspace-context turn).

- **All 10 service skills** (gmail, calendar, docs, drive, sheets, slides, contacts, tasks, forms, chat) do NOT have it (auto-activate when their service is in scope).

- **The `push` skill** does NOT have it (we want both - explicit `/scribe:push` invocation AND auto-activation when the user says "push this markdown to Drive").

The `argument-hint` field in skill frontmatter is the modern equivalent of `arguments` arrays from the legacy commands/ format. Use a string like `<file> [--folder <id>] [--account <email>]` rather than a structured list.

The `last-validated` field (ISO date) records when each skill was last smoke-tested against the current upstream pin. This serves the maintenance need of knowing which skills haven't been touched since upstream changed. `make validate` does not currently enforce this; it is informational.

### Icon regeneration

`docs/images/icon-1024.png` is the source of truth for all icon variants. To regenerate the smaller sizes -

```bash
make icons
```

Don't hand-edit the smaller variants. They get overwritten. If the brand mark needs a redesign, regenerate icon-1024.png via the `creators-studio:create-image` skill, then run `make icons`.

### "What about commands/?"

Don't add a `commands/` directory. The legacy commands/ format is deprecated in favour of skills/. The plugin install warning that appeared in v0.1 ("uses the legacy commands/ format - consider migrating") was the trigger for our v0.2.0 migration. The current state is correct; don't undo it.

### Cross-plugin composition

Scribe never directly calls other plugins' MCP tools or APIs. Cross-plugin orchestration happens through prose hints in workflow skills - e.g. "if the ClickUp plugin is installed, also create a ClickUp task with the email URL." Claude reads the hint, sees the ClickUp plugin's tools are available, and chains the call.

This pattern keeps Scribe decoupled from other plugins' versions. Never add direct tool references like `mcp__clickup__create_task` into Scribe skill prose; reference plugins by their user-facing names ("ClickUp plugin", "Slack plugin") so the prose is robust to plugin renames.

For dedicated multi-plugin workflows, the right place is a separate meta-orchestration plugin - see `/Users/juliandickie/code/plugin-dev/docs/2026-05-15-meta-orchestrator-concept.md`.

## Don't do this

- Don't pin upstream `workspace-mcp` to a major version range like `>=1.20`. Always pin to an exact version. Upstream patch releases occasionally introduce schema changes that need testing.

- Don't add a `commands/` directory. Skills cover both auto-activation and user invocation per the current Claude Code spec.

- Don't reference any `juliandickie/google_workspace_mcp` URL or branch (including the historical `fork-extension`) anywhere in user-facing files. That fork is retired. All install paths must reference `workspace-mcp@<version>` from PyPI, which builds from taylorwilsdon's main branch.

- Don't include AHPRA-specific conventions in skill prose. The `client-resolve` skill is intentionally scoped as "AHPRA-style repo convention" and explicitly says it's a no-op in non-AHPRA repos. Don't extend other skills with AHPRA tab-label expectations or condition-id assumptions.

- Don't generate emojis in skills, README, or commit messages unless explicitly requested. The user's CLAUDE.md preference is to avoid emoji.

- Don't autonomously create new GitHub repos, push to public visibility, or send messages to upstream maintainers without explicit user confirmation. PR creation, issue filing, and repo public-private settings all require an explicit instruction from the user.

- Don't bundle other plugins' MCP tools into Scribe. Cross-plugin chaining happens via prose hints and Claude's natural skill composition, not by importing or invoking other plugins' tool namespaces directly. If a workflow needs ClickUp/Slack/etc., reference those plugins by name in the prose, never call their tools directly.

## Future work

Items flagged during the v1.0 design conversation that are not in v1.0 scope. Full context in the spec at `docs/superpowers/specs/2026-05-15-workspace-suite-expansion-design.md`.

- **Meta-orchestration plugin** - separate plugin composing Scribe + ClickUp + Spiffy + AC Builder + Slack into cross-system workflows. Concept doc at `/Users/juliandickie/code/plugin-dev/docs/2026-05-15-meta-orchestrator-concept.md`.

- **Per-skill telemetry** - count workflow invocations to inform v1.1 priorities. Requires opt-in instrumentation.

- **Workflow templates as upstream feature** - propose to taylorwilsdon as a workspace-mcp capability if the workflow pattern proves broadly useful.

- **`--permissions` granular control as setup option** - in v1.0 documented as advanced override only. v1.1 could add a `/scribe:permissions` command for interactive setup.

- **AppScript and Search service skills** - tools enabled at manifest level but no dedicated service skill yet. Add in v1.1 if usage warrants.

- **Optional GitHub Actions weekly upstream-check** - `make check-upstream` covers manual cadence; automation deferred.

## Where to find more

- **README.md** - end-user view of what the plugin does and how to install
- **docs/multi-org-setup.md** - detailed cross-Workspace setup with switch.sh
- **skills/*/SKILL.md** - the actual Claude-facing skill prose (these are read by Claude at runtime, so they're the source of truth for tool routing logic)
- **AHPRA repo's CLAUDE.md** at `/Users/juliandickie/Documents/GitHub/ahpra-writing-research-cc/CLAUDE.md` - context for the consumer that drove this plugin's original requirements
- **Upstream README** at https://github.com/taylorwilsdon/google_workspace_mcp - the underlying MCP server's docs
- **GitHub releases** at https://github.com/juliandickie/scribe-plugin/releases - per-version changelogs

## Quick orientation for a new session

If you're an AI agent picking this up cold -

1. Read this file first (you're here).
2. Skim `README.md` to understand the user-facing pitch.
3. Read `skills/workspace/SKILL.md` (the orchestration router) to understand routing logic.
4. Browse `docs/workflows.md` and `docs/services.md` for the full skill catalog without opening 30 files.
5. Open individual skill files only when you need to modify a specific one.
6. Run `make orient` for a one-shot snapshot - validates manifests, shows recent local commits, lists published GitHub releases, confirms local plugin.json version matches the latest tag, lists open issues on this repo, and shows the state of the open upstream design discussion (taylorwilsdon issue #771).

If the user asks for a change, identify which layer it belongs to (plugin, upstream MCP, or AHPRA scripts) before writing code. The "Architecture" section above maps the territory.

**Important** - the GitHub release tag is the source of truth for what's actually shipped, not local `git log`. A release tag can sit on any commit. For example, v0.3.0 was tagged directly on the substantive PyPI-switch commit `906f5180`, not on a separate "Release v0.3.0" version-bump commit. So local `git log --oneline` alone can mislead you into thinking the latest release is older than it is. `make orient` cross-checks the latest published tag against `plugin.json` for you. If those diverge, find out why before assuming the working tree is shippable or that a "Release vX.Y.Z" commit is missing.

# Scribe Plugin

Context document for AI agents and contributors picking up this project in a new session. The README.md is for end users; this file is for whoever is editing the repo. Last refreshed 2026-05-08.

## What this project is

A Claude Code plugin that wraps [taylorwilsdon's `workspace-mcp`](https://github.com/taylorwilsdon/google_workspace_mcp) (Python, on PyPI). The plugin contributes -

- Six skills (`skills/<name>/SKILL.md`) that teach Claude when and how to use the MCP tools, plus user-invokable slash-style helpers for OAuth setup, account switching, and pushing markdown into Drive.

- An MCP server declaration (`mcpServers` block in plugin.json) that uvx-pulls a pinned version of `workspace-mcp` from PyPI and pre-configures three env vars so the credential flow works out of the box.

- Documentation, install hooks, and a multi-org switching helper script.

The plugin's distinctive value is the integration polish, not the underlying MCP server's capability. The capability is upstream's. We made the install one command, the OAuth setup five minutes, and the cross-Workspace-org workflow tractable.

## Current state - as of 2026-05-08

- **Plugin version** - 0.3.0 (in plugin.json + marketplace.json)
- **Pinned upstream version** - `workspace-mcp@1.20.4` from PyPI
- **Distribution** - GitHub at `juliandickie/scribe-plugin`, public, MIT licensed, with v0.3.0 release tagged
- **Marketplace install** - `/plugin marketplace add juliandickie/scribe-plugin` then `/plugin install scribe`
- **Direct download** - `https://github.com/juliandickie/scribe-plugin/archive/refs/tags/v0.3.0.zip`

## Architecture - where this fits in the broader ecosystem

Three repositories work together. This is one of them.

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
│ Claude Code plugin - 6 skills + manifest + hooks + docs.              │
│ Distributed via the official Claude Code plugin marketplace flow.     │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ juliandickie/google_workspace_mcp (OUR FORK, historical)              │
│ Was the staging ground for PR #727. Now mostly retired.               │
│ main is in sync with upstream main. fork-extension branch is the      │
│ historical record of the contribution but no live consumer pulls      │
│ from it anymore. Could be archived; not urgent.                       │
└──────────────────────────────────────────────────────────────────────┘
```

A FOURTH repo - `juliandickie/Documents/GitHub/ahpra-writing-research-cc` - consumes this work via Python library imports against the fork's local checkout (`scripts/gdocs/push_phase_f.py` etc.). Changes to the Scribe plugin do NOT directly affect that repo's batch scripts; it has its own pin.

## Repo structure

```
scribe-plugin/
├── .claude-plugin/
│   ├── plugin.json              # MCP server declaration + manifest
│   └── marketplace.json         # registry entry for /plugin marketplace add
├── skills/
│   ├── workspace/SKILL.md       # AUTO-activated; teaches Claude Workspace context
│   ├── auth-init/SKILL.md       # USER-invoked (disable-model-invocation: true)
│   ├── auth-add/SKILL.md        # USER-invoked
│   ├── auth-status/SKILL.md     # USER-invoked
│   ├── push/SKILL.md            # BOTH user-invoked AND auto-activated
│   └── client-resolve/SKILL.md  # USER-invoked (AHPRA-specific repo convention)
├── hooks/
│   └── post-install.sh          # Optional manual pre-install of workspace-mcp
├── scripts/
│   └── switch.sh                # Multi-org OAuth client symlink switcher
├── docs/
│   ├── multi-org-setup.md       # Detailed cross-Workspace setup
│   └── images/                  # Hero/architecture/before-after/icon assets
├── Makefile                     # help/validate/publish/icons targets
├── README.md                    # User-facing overview
├── CLAUDE.md                    # This file - dev context
├── LICENSE                      # MIT
└── .gitignore                   # .DS_Store
```

## Skills - the modern shape

Claude Code's plugin spec moved from `commands/` (legacy) to `skills/` (current). Every user-invokable surface is a skill with frontmatter `disable-model-invocation: true` so Claude will not auto-trigger it. Skills without that flag are auto-activated when their description matches user context.

Five of our six skills are user-invoked only -

- `/scribe:auth-init` - First-run Google Cloud + OAuth setup
- `/scribe:auth-add` - Authenticate an additional Google account
- `/scribe:auth-status` - List authenticated accounts
- `/scribe:client-resolve <CLIENT-ID>` - Resolve AHPRA-style client to account+folder
- `/scribe:push <file> [flags]` - Push markdown to Drive (also auto-activates on natural-language prompts like "push this to my Drive folder")

The sixth is the auto-activated context skill -

- `workspace` - Loaded automatically when Claude detects Google Workspace context in user prompts. Teaches Claude the tool patterns (when to use `manage_doc_tab populate_from_markdown` vs `import_to_google_doc`, how to find tab IDs via `inspect_doc_structure`, etc.).

The skill named `scribe` was renamed to `workspace` in v0.2.0 to avoid the awkward `/scribe:scribe` invocation name. The auto-activated skill is at `skills/workspace/SKILL.md` even though the plugin name and command prefix are still `scribe`.

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

2. MCP-server-level fixes (tool behaviour, scope handling, retry policy, new tools) - file an issue at taylorwilsdon/google_workspace_mcp first if it requires design discussion, or open a PR directly if the right answer is mechanically clear. Each PR should be one focused branch off your fork's main (not off fork-extension which is historical). See the issue #731 and PR #742 thread for the contribution-style template that worked.

3. AHPRA-specific workflow concerns - those go in the AHPRA repo's `scripts/gdocs/` rather than here. Don't pull AHPRA conventions into this plugin's general-purpose surface.

## Important conventions and gotchas

### Tool sandbox

The MCP server's `import_to_google_doc` enforces `ALLOWED_FILE_DIRS` (defaults to `~/.workspace-mcp/attachments` per our manifest). Files outside that path are rejected. **Symlinks do NOT bypass the sandbox** because the server resolves with `realpath()` before checking. The `skills/push/SKILL.md` walks Claude through auto-copying outside-sandbox files into `~/.workspace-mcp/attachments/scribe-session/` instead of trying symlinks.

### Multi-org OAuth

Internal-type OAuth consent screens only accept identities from the owning Workspace org. So a user with two Workspaces needs TWO OAuth clients - one per org. The `scripts/switch.sh` helper plus the symlink-swap pattern documented in `docs/multi-org-setup.md` is how Scribe handles this. Token caches at `~/.workspace-mcp/credentials/<email>.json` are self-contained and unaffected by which OAuth client is currently active, so authentication only happens once per email.

### Skills frontmatter

The `disable-model-invocation: true` flag in skill frontmatter prevents Claude from auto-triggering a skill based on context matching. Use it for skills that should ONLY run when the user explicitly types the slash command. Five of our six skills have it. The `workspace` skill does NOT have it (it's auto-activated context). The `push` skill does NOT have it either (we want both - explicit `/scribe:push` invocation AND auto-activation when the user says "push this markdown to Drive").

The `argument-hint` field in skill frontmatter is the modern equivalent of `arguments` arrays from the legacy commands/ format. Use a string like `<file> [--folder <id>] [--account <email>]` rather than a structured list.

### Icon regeneration

`docs/images/icon-1024.png` is the source of truth for all icon variants. To regenerate the smaller sizes -

```bash
make icons
```

Don't hand-edit the smaller variants. They get overwritten. If the brand mark needs a redesign, regenerate icon-1024.png via the `creators-studio:create-image` skill, then run `make icons`.

### "What about commands/?"

Don't add a `commands/` directory. The legacy commands/ format is deprecated in favour of skills/. The plugin install warning that appeared in v0.1 ("uses the legacy commands/ format - consider migrating") was the trigger for our v0.2.0 migration. The current state is correct; don't undo it.

## Don't do this

- Don't pin upstream `workspace-mcp` to a major version range like `>=1.20`. Always pin to an exact version. Upstream patch releases occasionally introduce schema changes that need testing.

- Don't add a `commands/` directory. Skills cover both auto-activation and user invocation per the current Claude Code spec.

- Don't reference the fork URL `git+https://github.com/juliandickie/google_workspace_mcp.git@fork-extension` anywhere in user-facing files. The fork's branch is historical only. All install paths should reference `workspace-mcp@<version>` from PyPI.

- Don't include AHPRA-specific conventions in skill prose. The `client-resolve` skill is intentionally scoped as "AHPRA-style repo convention" and explicitly says it's a no-op in non-AHPRA repos. Don't extend other skills with AHPRA tab-label expectations or condition-id assumptions.

- Don't generate emojis in skills, README, or commit messages unless explicitly requested. The user's CLAUDE.md preference is to avoid emoji.

- Don't autonomously create new GitHub repos, push to public visibility, or send messages to upstream maintainers without explicit user confirmation. PR creation, issue filing, and repo public-private settings all require an explicit instruction from the user.

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
3. Skim the six SKILL.md files to understand the runtime behavior.
4. Run `make validate` to confirm the repo is in a clean state.
5. Run `git log --oneline -10` to see recent work.
6. Check `gh issue list --repo juliandickie/scribe-plugin` for any reported friction.
7. Check `gh issue view 771 --repo taylorwilsdon/google_workspace_mcp` for the open upstream design discussion.

If the user asks for a change, identify which layer it belongs to (plugin, upstream MCP, or AHPRA scripts) before writing code. The "Architecture" section above maps the territory.

# Scribe - attachment accuracy, cross-service file handling, and onboarding - design

Status - draft, awaiting Julian's review
Date - 2026-06-13
Author - Claude (brainstormed with Julian)
Target Scribe version - 1.1.0 (adds one new skill, so MINOR not patch)

## Background

This work began from `dev-docs/2026-06-13-gmail-draft-attachment-gaps.md`, a field report captured while drafting a real client email with PDF attachments and a Send As alias. That doc found the gmail skill undersells `draft_gmail_message` and omits the attachment-path sandbox constraint.

During brainstorming the scope widened by explicit decision to also cover the cross-service version of the attachment story, the known `populate_from_markdown` table bug, and the onboarding experience (a discoverability command plus an auth first-run pass).

All claims below were verified against the live `workspace-mcp@1.20.4` tool schemas on 2026-06-13, not taken from the field report alone. Where a claim is unverified it is marked as such.

## What the live schemas actually show

The field report was correct and incomplete. The verified surface of `draft_gmail_message` and `send_gmail_message` (identical except `to` is optional for draft and required for send) is -

- `attachments` - a list where each item is one of three shapes - `{url}`, `{path}`, or `{content, filename}` - with optional `mime_type` (auto-detected). The schema explicitly states `url` accepts the MCP attachment URLs returned by `get_drive_file_download_url` and `get_gmail_attachment_content`.

- `from_email` plus `from_name` - Gmail Send As alias support.

- `include_signature` (default true) - appends the Gmail signature.

- `body_format` - `plain` or `html`. The field report missed this entirely; it means Scribe can draft and send real HTML email.

- threading - `thread_id`, `in_reply_to`, `references`, `quote_original`.

The premise correction that drives the design - the field report frames "copy the file into the managed attachments directory first" as the way to attach. It is only one of three ways, and the least convenient. For a file already in Drive or already on an email, the `url` mode skips staging entirely. Staging is required only for a genuinely-local file (for example a PDF sitting on the Desktop) passed via `path`.

## Goals

- Make the gmail skill describe the real `draft_gmail_message` and `send_gmail_message` surface, including attachments, Send As, signature control, HTML body, and threading.

- Give Scribe one coherent mental model for referencing files across `gmail attachments`, `create_drive_file`, and `import_to_google_doc`, including the param-name inconsistency and when the sandbox applies.

- Stop the `populate_from_markdown` table bug from biting at runtime by surfacing the known workaround where Claude will see it.

- Give a freshly-installed user an in-product entry point that orients them without reading the README.

- Resolve the one genuinely-open auth-init issue (Windows `${HOME}`) and retire the now-stale auth issues doc.

- Make Claude's self-discovery on a direct invocation (no `/scribe:start`) fast and self-correcting - the right skill loads reliably, the common tool choice is answered up front, and a failed call recovers in one step rather than by trial and error.

## Non-goals

- No change to the upstream `workspace-mcp` server. Everything here is plugin-level (skill prose, manifest, docs).

- No re-litigation of the auth flow that already works on macOS. The auth work is bounded to the Windows path item, a callback clarity line, and archiving the stale doc.

- No new workflow skills beyond the single discoverability command.

- No version bump or publish as part of this design. Per Julian's scope-check rule, publishing is a separate, explicitly-approved step after implementation.

## Design

### Cluster A - Gmail skill accuracy

File - `skills/gmail/SKILL.md`.

Current state - the `draft_gmail_message` entry is a single line ("Create a draft. Same parameter shape as send.") and the `send_gmail_message` entry lists only `to`, `subject`, `body`, `cc`, `bcc`, `user_google_email`.

Change -

- Rewrite the `send_gmail_message` entry to document the full verified surface - `from_email`, `from_name`, `include_signature`, `body_format`, the threading params, and `attachments` (with a pointer to the new Attachments subsection).

- Rewrite the `draft_gmail_message` entry to state it shares that full surface, and call out the one real difference - `to` is optional for a draft (you can save a recipient-less draft) but required for send.

- Add an "Attachments" subsection describing the three modes and when to use each -

  1. `url` - for a file already in Drive or on an email. Get its URL from `get_drive_file_download_url` or `get_gmail_attachment_content` and pass it straight through. No staging.

  2. `path` - for a genuinely-local file. Subject to the `ALLOWED_FILE_DIRS` sandbox; the file must live in `~/.workspace-mcp/attachments` (or a configured allowed dir) first. Point to the router's file-handling section and the push skill's staging decision tree rather than restating them.

  3. `content` plus `filename` - for bytes already in memory. Standard base64, not urlsafe.

- Add a Gotchas bullet - the `path` mode is the one bound by the sandbox; the `url` mode is the escape hatch for Drive- and Gmail-sourced files.

Rationale - this is the literal fix the field report asked for, expanded to the real surface. Keeping the staging mechanics as a pointer (not a restatement) avoids drift between three copies of the same rule.

### Cluster B - Cross-service file-handling map

Files - `skills/workspace/SKILL.md` (primary), `skills/drive/SKILL.md` (supporting), `skills/gmail/SKILL.md` (pointer, covered in A).

Current state - the router has a "Sandbox and attachment rules" section, but it only covers the upload/staging direction (the `path` side). It does not mention the `url` mode or the fact that file-reference param names differ across tools. The detailed staging decision tree lives in `push/SKILL.md`. The drive skill's `get_drive_file_download_url` entry is one line and does not say it returns a servable URL or saves locally.

Change -

- Expand the router's "Sandbox and attachment rules" into a "File and attachment handling" section that presents the three reference modes once, states that Drive- and Gmail-sourced files use their MCP url and skip staging, and includes a small param-name table so Claude stops guessing -

  | Tool | Local-file param | Remote/URL param | Inline param |
  |---|---|---|---|
  | `send_gmail_message` / `draft_gmail_message` | `path` (in `attachments[]`) | `url` (in `attachments[]`) | `content` + `filename` |
  | `create_drive_file` | via `fileUrl` with `file://` | `fileUrl` (http/https) | `content` |
  | `import_to_google_doc` | `file_path` (local or `file://`) | `file_url` (http/https) | `content` |

- Keep `push/SKILL.md` as the deep-dive for the staging decision tree; the router section points to it. No duplication.

- Expand the drive skill's `get_drive_file_download_url` entry. Two follow-ups it enables - feeding its result into a gmail attachment `url` (the send/draft schema names this tool explicitly), and reading the file locally (a prior session observed it saving bytes into the managed attachments directory and returning a local path). The exact return shape (servable URL, local path, or both) must be verified live before the prose is written, because the schema comment and that prior observation describe it differently.

Open verification item - the schema confirms the sandbox applies to gmail `path` and `import_to_google_doc` `file_path`. Whether `create_drive_file`'s `fileUrl` with a `file://` URL is also sandbox-checked is unverified. The spec marks the table cell accordingly; implementation should verify before asserting it in prose.

Rationale - the router is the cross-cutting map by design (it holds chaining patterns and the credential scan). The attachment-reference model is exactly that kind of cross-cutting knowledge. Service skills keep their own service-specific detail; push keeps the staging mechanics.

### Cluster C - populate_from_markdown structure rendering (tables, lists, paragraphs)

Files - `skills/docs/SKILL.md` (primary), `skills/workspace/SKILL.md` (one-line caution), plus the content-generation guidance wherever Scribe writes markdown into Docs.

Failures in the markdown-to-Google-Doc conversion (`populate_from_markdown`, and `import_to_google_doc`) -

- Tables - GFM tables render as raw pipe text rather than real Doc tables. Tracked in `docs/issues/populate-from-markdown-table-rendering.md`.

- Line breaks - markdown's single newline is a soft break, so the converter joins consecutive lines into one run-on paragraph even though they look line-per-line in the source. This is standard markdown behaviour, not a bug, and it is the root of the "one big paragraph" problem. The fix depends on intent, and the intent is NOT always a bulleted list.

Change -

- Document both line-handling patterns for Doc-bound markdown, and which to use -

  - Real bulleted or numbered list - a consistent marker (`- ` or `1. `) with a blank line before and after the list; tight items render as real Google Docs bullets.

  - Separate plain paragraphs (each line on its own line, no bullets - the common case) - a blank line between each line, because a single newline collapses them into one paragraph. This is correct markdown for separate paragraphs, not a hack, and it does not turn them into bullets.

- Do not force content into structured lists to fix the collapse; most of the time the goal is just separate paragraph lines, which the blank line achieves on its own.

- Add a docs-skill Gotchas bullet covering the two line patterns above plus the table fallback (express tabular data as a properly-formatted list, or build a real table with `create_table_with_data`). Verify with `inspect_doc_structure(detailed=true)` - `tables: 0` means a table did not render; a single paragraph where several lines were expected means a soft-break collapse.

- Add a one-line caution at the `populate_from_markdown` recommendation in the router's "Email to Doc" chaining pattern.

Confidence - the mechanism is standard markdown soft-break semantics and matches the failure Julian observed, so the patterns are high-confidence. An optional controlled scratch-Doc test can confirm `populate_from_markdown` is CommonMark-compliant if we want certainty, but it is no longer load-bearing.

Rationale - tables, lists, and plain paragraphs are one family (markdown structure surviving the Doc conversion). The blank-line habit is correct for the separate-paragraphs case and unnecessary for true lists; documenting both stops the over-application that bloats skill files.

### Cluster D1 - discoverability command

File - new `skills/start/SKILL.md`, invoked as `/scribe:start`.

Frontmatter - `disable-model-invocation: true` (user-only), an `argument-hint` if any, and `last-validated`.

Behaviour -

1. Run the credential scan (the same `ls ~/.workspace-mcp/credentials/*.json` logic the router and auth-status already use; Windows variant included).

2. If no accounts exist - say so plainly, route to `/scribe:auth-init`, and give a one-line teaser of what authenticating unlocks. This is the genuine first-run path.

3. If accounts exist - list them, then present the 14 workflows grouped by use case (daily ops, client work, email, setup), then a "or just ask in plain English" line with two concrete example utterances. Close with a pointer to `/scribe:auth-add EMAIL` for more accounts and `/scribe:auth-status` for deep token health.

Composition - `start` reuses the credential-scan logic and defers deep token-health inspection to `auth-status` rather than duplicating the JSON parsing. It restates the workflow catalog that currently lives only inside the router (which Claude sees but the user never does); if maintenance duplication becomes a concern, a later step can extract the catalog to `docs/workflows.md` as the single source and have both reference it.

Rationale - the plugin has 30 skills and 14 workflows with no in-product way to discover them. A `start` command is the highest-leverage onboarding improvement, matches the ecosystem convention, and doubles as the first-run greeter.

### Cluster D2 - auth Windows hardening and cleanup

Files - `.claude-plugin/plugin.json`, `skills/auth-init/SKILL.md`, `docs/issues/scribe-auth-init-issues.md` (archive), new `docs/issues/legacy/README.md`.

Context - of the 11 issues in the 0.3.0-era report, 9 are fixed in the current v1.0 auth-init skill and 1 (callback server) is moot in the plugin-managed stdio flow. Only Issue 11 (`${HOME}` may not expand on Windows) is genuinely open, and it is currently documented only reactively in troubleshooting.

Change -

- Resolve the `${HOME}` question in `plugin.json`. All three env vars use `${HOME}`. Implementation must first verify what Claude Code's plugin MCP launcher actually expands in `mcpServers.env` on Windows (via the plugin-dev docs or the claude-code-guide agent) and NOT guess. Based on that finding, either switch to a token Claude Code expands cross-platform, or keep `${HOME}` and make the Windows `.claude/settings.json` override a prominent proactive step rather than buried troubleshooting.

- Add one clarifying line to auth-init explaining how the OAuth callback completes in the plugin-managed flow (the server is already running and receives the redirect), so the "wait for the success page" instruction has a stated mechanism.

- Move `docs/issues/scribe-auth-init-issues.md` to `docs/issues/legacy/` and add `docs/issues/legacy/README.md` noting what was archived, when, and why (per Julian's archive-over-delete rule) - specifically that v1.0 resolved 9 of 11 items and the rest are addressed here.

Honesty constraint - the developer here is on macOS. The Windows fix is best-effort from documented behavior and reasoning. The spec and the eventual change must state plainly that Windows behavior is unverified and needs Julian's confirmation on a Windows machine. "Fixed" is not claimable for Windows from this environment.

Rationale - matches the evidence (most of the friction is gone) while honoring the explicit choice to harden Windows. The discoverability command, not an auth-init rewrite, is the real "easier initialisation" win.

### Cluster E - Fast self-discovery and self-correction

Files - `skills/workspace/SKILL.md`, a new `skills/workspace/references/tool-index.md`, and all ten service skills (`gmail`, `calendar`, `docs`, `drive`, `sheets`, `slides`, `contacts`, `tasks`, `forms`, `chat`).

Context - `/scribe:start` is a human orientation screen and primes nothing; skills load per turn by relevance. On a direct invocation Claude self-discovers from three layers - the live MCP tool schemas (always the floor), the auto-loaded `workspace` router, and the matching service skill. Clusters A, B, and C already improve the latter two for the direct path. Cluster E adds a deliberate fast path and a self-correction layer on top.

Change -

- E1 - Error-recovery map in the router. A compact table mapping the known failure signatures to cause and one-step fix - sandbox rejection becomes "use the `url` attachment mode or stage the file"; "invalid grant" or "token expired" becomes "re-auth that account via `/scribe:auth-add`"; "Scope not authorized" becomes "enable the API and re-run `start_google_auth` for that service"; `inspect_doc_structure` reporting `tables: 0` becomes "use lists, the markdown table did not render"; a multi-org wrong-client failure becomes "switch the active OAuth client". This converts learn-by-failure (several failed round-trips) into one-step recovery. Kept in the always-on router because it is small and cross-cutting.

- E2 - Tool-selection and gotcha index in a new `references/` file the router points to. Intent mapped to tool, the one gotcha that bites most, and which service skill carries the depth. Lives in `references/` (progressive disclosure) so it loads only when Claude needs the map, keeping the always-on router lean. The router carries a one-line pointer, not the matrix.

- E3 - Service-skill description audit. Tune each service skill's `description` against the phrasings users actually use, since the description is the auto-activation trigger - if it does not match, the skill body never loads and Claude operates from schemas alone (capable but gotcha-blind). This is the first-order lever for self-discovery.

- E4 - Trim duplicated param lists from the service skills. The live schemas already carry param names, types, defaults, and required-ness. The skills currently re-list these, which costs context and drifts from reality (that drift is why the gmail skill under-listed `draft` params). Replace the rote re-listing with a curated key-params digest - the three to five params that matter for the common case, plus non-obvious interactions the schema does not spell out (for example `quote_original` needs `thread_id`, or `to` optional-for-draft) - and keep selection guidance, gotchas, and chaining. Trust the schemas for the exhaustive and rare params.

Deferred-tools caveat (important, and the refinement Julian should sign off) - in this very session, scribe's MCP tools were deferred and had to be loaded via ToolSearch before their schemas were visible. Where tools are deferred, "trust the schemas" carries a round-trip cost, not just a context saving. That is the explicit reason E4 keeps a curated key-params digest in each skill rather than deleting params outright - the common case must remain answerable from the skill without forcing a schema lookup. Implementation should confirm whether the typical deployment runs scribe tools deferred or in-context and tune digest depth accordingly. Wholesale deletion is the wrong reading of "trim params."

Rationale - the schemas are the WHAT (tools and params); the skills are the HOW and the WATCH-OUT-FOR (selection, gotchas, recovery, chaining). E sharpens that division of labour so the common case is fast and failures self-correct, without bloating the always-on context.

### Phasing

Cluster E roughly doubles the surface of this work (it touches all ten service skills), so the writing-plans phase should sequence it as a second wave -

- Wave 1 - accuracy and onboarding - clusters A, B, C, D1, D2. Self-contained and shippable on its own.

- Wave 2 - self-discovery refactor - cluster E. Builds on Wave 1's gotcha placements; can ship as a follow-on if Wave 1 needs to land first.

This keeps each release reviewable and lets E1 plus E2 (the high-value, low-risk fast path) land even if E4 (the broader param trim) needs more iteration.

## Files touched - summary

- `skills/gmail/SKILL.md` - A, B pointer, E3 description, E4 param trim

- `skills/workspace/SKILL.md` - B, C caution, E1 error-recovery map, E2 pointer

- `skills/workspace/references/tool-index.md` - E2 (new)

- `skills/drive/SKILL.md` - B, E3 description, E4 param trim

- `skills/docs/SKILL.md` - C, E3 description, E4 param trim

- `skills/calendar`, `sheets`, `slides`, `contacts`, `tasks`, `forms`, `chat` SKILL.md - E3 description audit and E4 param trim

- `skills/start/SKILL.md` - D1 (new)

- `.claude-plugin/plugin.json` - D2

- `skills/auth-init/SKILL.md` - D2

- `docs/issues/scribe-auth-init-issues.md` to `docs/issues/legacy/` plus a `legacy/README.md` note - D2 archive (filesystem-only; `docs/issues/` is gitignored)

- `.claude-plugin/marketplace.json` - skill count and version, at publish time only

- `README.md` and `CLAUDE.md` - reflect the new skill, the corrected skill count (30 to 31), the v1.1.0 state, and a corrected writing-style rule 3 (blank-line-between-items is a Google-Doc list workaround, not a blanket rule for all docs and skills)

## Validation plan

- `make validate` - JSON parse plus skill structure check.

- `plugin-dev:plugin-validator` agent - catches frontmatter and manifest schema issues the Makefile misses, especially for the new `start` skill.

- Manual smoke - invoke `/scribe:start` in both states (no credentials, and with at least one account) and confirm the routing and catalog render correctly.

- Style grep - `grep -rn` for em dashes across the changed files; confirm no colons in new headings; straight quotes only.

- Windows items - explicitly left as "needs Julian to confirm on Windows," not marked done.

- Cluster E - for each trimmed service skill, confirm the common-case task is still answerable from the skill alone without a forced schema lookup; spot-check that the audited descriptions still auto-activate the right skill across a handful of real phrasings; confirm the `references/` index loads on demand and the router pointer resolves.

## Writing-style compliance

The plugin's own house style (CLAUDE.md) plus Julian's global rules apply to every file touched -

- No em dashes or en dashes anywhere.

- No colons in headings; use " - ".

- Blank lines between lines are for Google-Doc paragraph fidelity (markdown soft breaks otherwise collapse lines into one paragraph; see cluster C), not a blanket rule and not always about lists. Do not pad content with blank lines in the SKILL.md files this work touches - they are read as markdown. The plugin's CLAUDE.md rule 3 overstates this and is corrected as part of the CLAUDE.md update.

- Straight quotes only; strip trademark and ligature glyphs.

## Open questions for the writing-plans phase

- The exact `${HOME}` expansion behavior in Claude Code's plugin MCP launcher on Windows (must verify, not guess).

- Whether `create_drive_file`'s `fileUrl` with `file://` is sandbox-checked (verify before asserting).

- The exact return shape of `get_drive_file_download_url` (servable URL, local path, or both). The send/draft schema implies a URL; a prior session observed a local path. Verify live before writing the drive prose.

- Skill count moves from 30 to 31 with `start`. CLAUDE.md has a pre-existing inconsistency (it states 30 total but elsewhere references 6 infra skills where there are 5). Reconcile when updating CLAUDE.md.

- Naming - `/scribe:start` is the recommendation; `/scribe:help` is the alternative if Julian prefers a reference framing over a first-run framing.

- Whether to extract the workflow catalog to `docs/workflows.md` as a single source now, or accept the temporary duplication between the router and the new `start` skill and defer extraction.

- Whether the typical deployment runs scribe's MCP tools deferred (ToolSearch-loaded) or in-context. This sets how aggressively E4 can trim params without forcing a schema round-trip.

- Where the E2 index file should live - per-skill at `skills/workspace/references/` (recommended, travels with the router) or a plugin-level references directory.

# gworkspace

**Claude Code writes directly to your Google Docs. No more copy-paste dance.**

![gworkspace hero](docs/images/hero.png)

---

## The problem you keep solving the hard way

You live in Google Docs. Your client reviews happen there. Your team comments happen there. Your finished content ships from there.

But everything you write lives somewhere else first - in markdown, in your editor, in your Claude Code session. Getting it from "written" to "in the right Google Doc with the right formatting in the right tab" is a manual slog -

- Copy the file

- Paste into Drive as markdown (hope the "convert" option is on today)

- Click into the right tab (or remember to make one)

- Compare against the source to catch missing sections

- Repeat 96 times for a full client push

Half your production day becomes clipboard theatre. Client review slips a week because the docs aren't ready. You automate your markdown pipeline, your CI, your tests - but this one last mile stays stubbornly manual.

![Before and after](docs/images/before-after.png)

## The guide

`gworkspace` is a Claude Code plugin that gives your Claude session direct API-level access to Google Workspace. Once installed, Claude can -

- Read any Google Doc (including tab structure and per-tab content)

- Write markdown into any Doc, tab by tab, with correct formatting preserved

- Create or update Drive folders and files

- Search Gmail threads and read Calendar events

It wraps the [`workspace-mcp`](https://github.com/juliandickie/google_workspace_mcp/tree/fork-extension) server - a fork of [taylorwilsdon's google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) extended with a high-fidelity markdown-to-Google-Docs writer.

## How it works

![Architecture diagram](docs/images/architecture.png)

Three layers, one install -

1. **Your Claude Code session** issues a natural-language request ("update the Blog Article tab in the D01 doc with the latest markdown")

2. **The plugin** matches the request to the right skill and routes the call to its MCP server

3. **The MCP server** handles OAuth, calls Google's Drive + Docs + Gmail + Calendar APIs, and returns the result

You never touch a browser tab. The markdown to Google Doc conversion happens server-side with full fidelity - headings, bold and italic, lists, code blocks, blockquotes, links, all preserved. And because it is Claude writing the commands, you can speak to it naturally - no memorised CLI flags.

## The plan - three commands to a working install

```bash
# 1. Add this plugin's marketplace
/plugin marketplace add juliandickie/gworkspace-plugin

# 2. Install the plugin
/plugin install gworkspace

# 3. Guided OAuth setup
/gws-auth-init
```

First MCP invocation takes a few seconds while `uvx` downloads the server from the fork. Every subsequent call is instant.

## Google Cloud setup - 5 minutes, one time

Before the plugin can talk to Google, you need your own OAuth client credentials. No shared client IDs - you own your quota, your consent screen, your trust boundary.

1. Visit [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account

2. Create a new project (suggest the name `gworkspace-personal`)

3. Under **APIs & Services > Library**, enable -

    - **Google Drive API** (mandatory)

    - **Google Docs API** (mandatory)

    - **Gmail API** (optional, for mail operations)

    - **Google Calendar API** (optional, for calendar reads)

4. Under **APIs & Services > OAuth consent screen**, configure a minimal consent screen

    - User type - External

    - App name - anything (e.g., "gworkspace personal")

    - Support and developer email - your own

5. Under **APIs & Services > Credentials**, click **Create Credentials > OAuth client ID**

    - Application type - **Desktop app**

    - Name - "gworkspace desktop client"

6. Download the JSON. Save to `~/.workspace-mcp/oauth_client.json`.

7. Run `/gws-auth-init` in Claude Code and follow the prompts.

Your credentials never leave your machine. Tokens are stored encrypted at `~/.workspace-mcp/`.

## Slash command reference

| Command | What it does |
|---|---|
| `/gws-auth-init` | Guided first-run Google Cloud and OAuth setup |
| `/gws-auth-add` | Authenticate an additional Google account |
| `/gws-auth-status` | List authenticated accounts and token validity |
| `/gws-push` | Push a markdown file to Drive as a new or updated Doc |
| `/gws-client-resolve` | Resolve a CLIENT-ID (AHPRA-style repos) to account and folder |

## Multi-account support

Got a personal Google and a work Google Workspace? Or one per client engagement? The plugin handles multiple authenticated accounts concurrently. Pass `user_google_email` as a parameter to any MCP tool call, set `USER_GOOGLE_EMAIL` in your shell session, or store it in a project's config file. The skill teaches Claude to resolve the right account automatically when it can.

## Troubleshooting

**"No cached token"** - run `/gws-auth-init`. You have not completed OAuth consent for any account yet.

**"Invalid grant" or "unauthorized"** - OAuth consent may have been revoked at [myaccount.google.com](https://myaccount.google.com/permissions). Re-run `/gws-auth-init` to re-consent.

**Token expired** - the MCP server auto-refreshes on next call. If refresh fails (rare), re-authenticate via `/gws-auth-init`.

**API quota exceeded** - Google's default quota is 60 requests per minute per user. Heavy batch operations may need you to request a quota increase on your Cloud Console.

**First install is slow** - the `mcpServers` declaration in `plugin.json` uses `uvx` to pull the server from GitHub on first invocation. Subsequent calls use the cached install and are near-instant.

**Want to pre-install instead of waiting for first use** - an optional convenience script is at `hooks/post-install.sh` in the plugin's install directory. Run it manually to eagerly pip-install the server.

## What this enables

Real examples from production use of the underlying fork -

- **Agency batch content push** - one agency populates 12 condition documents × 8 content tabs each (96 tabs) for a clinic client in under 4 minutes, end-to-end. The equivalent browser-paste workflow used to take close to an hour.

- **In-session edits** - "update the second paragraph of the Pricing page to reflect the new numbers" works as a one-shot in Claude Code. No context switch to a browser.

- **Read-and-reason** - "summarise the client comments on the Services doc and group them by theme" turns a tedious review into a one-request answer.

## Source

This plugin wraps the fork at [juliandickie/google_workspace_mcp](https://github.com/juliandickie/google_workspace_mcp) branch `fork-extension`. The fork adds `update_tab_from_markdown` and two bug fixes on top of [taylorwilsdon's google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) (the original upstream).

Issues, PRs, and feature requests to either repo.

## License

MIT. See [LICENSE](LICENSE).

---

Built by [Julian Dickie](https://github.com/juliandickie) for agencies that ship content faster than their tooling should allow.

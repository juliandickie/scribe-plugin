---
description: Bootstrap a new contact - create Drive folder, add Contacts entry, log row in a tracking sheet, draft welcome email. Invoke via /scribe:contact-onboard.
disable-model-invocation: true
argument-hint: <name-and-email> [--folder-parent ID] [--tracker-sheet ID] [--account email]
last-validated: 2026-05-15
---

# Scribe - Contact onboarding

For onboarding a new contact, client, or business relationship. Creates a structured Drive folder for them, adds them to Google Contacts, logs a row in the tracking sheet of the user's choice, and drafts a welcome email.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `<name-and-email>` (required) - in format `Sarah Smith <sarah@example.com>`.

- `--folder-parent ID` (optional) - parent folder for the new contact folder. Default - "Contacts" folder under My Drive.

- `--tracker-sheet ID` (optional, prompts if missing first run) - the contact tracker sheet.

- `--account email` (optional) - account to use.

## Tool call sequence

1. **Parse name and email** from input.

2. **Check for existing contact** - search Contacts by email. If exists, prompt user to confirm before duplicating.

3. **Create Contacts entry** - via the contacts skill.

4. **Resolve folder parent** - use `--folder-parent` or default to "Contacts" folder (create if absent).

5. **Create contact folder** - `create_drive_folder` for the contact's name as a subfolder.

6. **Share folder** (optional) - `manage_drive_access` to share the contact folder with the contact's email if user confirms.

7. **Log to tracker sheet** - append a row with `[date, name, email, folder_url, status="onboarding"]`.

8. **Draft welcome email** - `draft_gmail_message` with a welcome template - introducing the user, linking the shared folder, mentioning next steps.

9. **Return** - folder URL, draft URL, sheet row reference.

## Multi-account behaviour

Single account. Specified via `--account` or resolved from context.

## Cross-plugin composition

- **AC Builder plugin** - add contact to ActiveCampaign, apply default new-contact tag.

- **ClickUp plugin** - create an onboarding task series in the configured onboarding list.

- **Slack plugin** - if Slack channel invites are supported, optionally invite the contact to a shared channel.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Onboard Sarah Smith <sarah@example.com>"

- "Set up a new contact - John Brown john@example.com"

Explicit args:

- `/scribe:contact-onboard "Sarah Smith <sarah@example.com>" --tracker-sheet ABC...`

## Failure modes

- **Contact already exists** - prompt before duplicating.

- **Folder already exists at the path** - prompt before overwriting; default to appending date suffix.

- **Sharing fails** (external user, org policy) - surface and continue with rest of setup.

## Output

Always return:

- Folder URL

- Draft URL

- Sheet row link

- Cross-plugin steps skipped

---
description: Bootstrap a new educator - create their Drive folder structure with curriculum, planning, and course tracker, share access, and draft a welcome email. Invoke via /scribe:educator-setup.
disable-model-invocation: true
argument-hint: <name-and-email> [--parent-folder ID] [--tracker-sheet ID] [--course-name "..."]
last-validated: 2026-05-15
---

# Scribe - Educator setup

iDD-specific workflow for onboarding a new educator for a course. Creates a structured Drive folder set (curriculum, planning, course tracker), adds the educator as collaborator, logs them to the master educator tracker sheet, and drafts a welcome email with expectations and kickoff meeting suggestion.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `<name-and-email>` (required) - educator info, format `Dr Sarah Smith <sarah@example.com>`.

- `--parent-folder ID` (optional) - parent under which to create the educator folder. Default - "Educators" folder.

- `--tracker-sheet ID` (optional) - master educator tracker sheet.

- `--course-name "..."` (optional) - which course they'll teach.

## Tool call sequence

1. **Parse name and email** from input.

2. **Resolve parent folder** - use `--parent-folder` or default to "Educators" folder under My Drive (create if absent).

3. **Create educator folder** - `create_drive_folder` for `<educator-name>` under parent.

4. **Create subfolders** - inside the educator folder, `create_drive_folder` for `Curriculum`, `Planning`, `Recordings`.

5. **Create planning doc** - `create_doc` titled `<educator-name> - Course planning` in the Planning folder.

6. **Share folder** - `manage_drive_access` to share the educator folder with the educator's email at `writer` level.

7. **Log to tracker sheet** - append a row with `[date, name, email, folder_url, course_name, status="onboarding"]`.

8. **Draft welcome email** - `draft_gmail_message` with a welcome email - folder link, expectations summary, suggested kickoff date.

9. **Return** - folder URLs (parent and subfolders) plus draft URL.

## Multi-account behaviour

Uses the iDD account by default (resolved via user context). Single account.

## Cross-plugin composition

- **AC Builder plugin** - add the educator to the AC educators list, apply standard onboarding tags.

- **ClickUp plugin** - create educator onboarding task series in the designated list (e.g. "send first-week check-in to STUDENT", "schedule kickoff", "review curriculum").

- **Slack plugin** - invite to relevant Slack channels (or draft a message to the channel admin requesting invite).

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Set up Dr Sarah Smith as a new educator for the Implant course"

- "Onboard educator John Brown john@example.com"

Explicit args:

- `/scribe:educator-setup "Dr Sarah Smith <sarah@example.com>" --course-name "Implant placement masterclass"`

## Failure modes

- **Educator already exists** (folder name collision) - prompt before overwriting.

- **Sharing fails** (external user, org policy) - surface the issue and continue with rest of setup. Note the failure in the welcome email draft so the user can manually resolve.

- **Tracker sheet not found** - prompt user.

## Output

Always return:

- Educator folder URL

- Subfolder URLs

- Planning doc URL

- Welcome draft URL

- Tracker sheet row reference

- Cross-plugin steps skipped

---
description: Resolve a CLIENT-ID (AHPRA-style repo convention) to its Google account email and Drive folder ID from the client's profile.md frontmatter.
argument-hint: <client-id>
---

Read `clients/$1/profile.md` in the current working directory (or the nearest ancestor containing a clients/ folder).

Parse the YAML frontmatter. Report -

- Client ID

- google_account_email field value

- google_drive_folder_id field value (if present)

- Content dir path (`clients/$1/content/`)

- Website dir path (`clients/$1/website/`)

If the profile.md is missing the required fields, explain which fields are needed and offer to add them.

This command is AHPRA-specific and assumes the repo follows the clients/{CLIENT-ID}/profile.md convention. In non-AHPRA repos this command has no effect.

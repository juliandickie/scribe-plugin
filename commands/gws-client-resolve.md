---
name: gws-client-resolve
description: Resolve a CLIENT-ID (AHPRA-style repo convention) to its Google account email and Drive folder ID from the client's profile.md frontmatter.
arguments:
  - name: client_id
    description: Client identifier (e.g. HONOUR-HEALTH-01)
    required: true
---

Read `clients/{client_id}/profile.md` in the current working directory (or the nearest ancestor containing a clients/ folder).

Parse the YAML frontmatter. Report -

- Client ID

- google_account_email field value

- google_drive_folder_id field value (if present)

- Content dir path (clients/{client_id}/content/)

- Website dir path (clients/{client_id}/website/)

If the profile.md is missing the required fields, explain which fields are needed and offer to add them.

This command is AHPRA-specific and assumes the repo follows the clients/{CLIENT-ID}/profile.md convention. In non-AHPRA repos this command has no effect.

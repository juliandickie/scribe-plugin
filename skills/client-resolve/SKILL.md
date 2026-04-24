---
description: Resolve a CLIENT-ID (AHPRA-style repo convention) to its Google account email and Drive folder ID from the client's profile.md frontmatter.
disable-model-invocation: true
---

# Scribe - Client Resolve

Resolve a client identifier to its Google Workspace configuration.

The user provides a CLIENT-ID in $ARGUMENTS (for example `HONOUR-HEALTH-01`).

Read `clients/$ARGUMENTS/profile.md` in the current working directory (or the nearest ancestor containing a clients/ folder).

Parse the YAML frontmatter. Report -

- Client ID

- google_account_email field value

- google_drive_folder_id field value (if present)

- Content dir path (clients/{CLIENT-ID}/content/)

- Website dir path (clients/{CLIENT-ID}/website/)

If the profile.md is missing the required fields, explain which fields are needed and offer to add them.

This skill is AHPRA-specific and assumes the repo follows the clients/{CLIENT-ID}/profile.md convention. In non-AHPRA repos this skill has no effect.

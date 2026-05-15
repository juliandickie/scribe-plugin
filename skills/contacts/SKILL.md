---
description: Use when the user's request involves Google Contacts - looking up a person by name or email, creating contacts, searching the address book, or enriching email addresses with contact metadata. Triggers on contact, person, address book, who is X.
last-validated: 2026-05-15
---

# Scribe - Contacts

Enables Claude to read and create Google Contacts via the People API - useful for resolving names to emails, enriching contact info, and creating new contact entries.

## When to use

Use this skill when the user's request involves -

- Looking up a contact by name to find their email

- Looking up by email to find their name and other metadata

- Creating a new contact

- Listing contacts in a specific group

## MCP tool reference

The exact tool names depend on the workspace-mcp version - inspect the MCP tools panel for the current set. Typical operations:

### read_contact / get_contact

Look up a contact by ID or email.

Parameters: `contact_id` or `email`, `user_google_email`.

Returns: contact metadata (name, email(s), phone, organisation, notes).

### search_contacts

Search by name or query.

Parameters: `query`, `user_google_email`.

### list_contacts

List contacts.

Parameters: `user_google_email`, optional pagination.

### create_contact

Create a new contact entry.

Parameters: `name`, `email`, optional fields (phone, organisation, notes), `user_google_email`.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel.**

## Common patterns

### Resolve a name to an email

1. `search_contacts` with the name as query.

2. Return the matching email(s). If multiple matches, prompt user to disambiguate.

### Enrich an email

1. Given an email, `read_contact` (or search by email).

2. Surface name, organisation, phone if present.

## Gotchas

- The People API distinguishes between contacts (people you've explicitly added) and "other contacts" (people you've emailed but not added). Both may be searchable.

- Workspace org contacts (directory) are separate from personal contacts. The API exposes both differently - some tools return one, some both.

- Display names can differ from primary email's display field. Treat name and email as separate identity facets.

## Account selection

Pass `user_google_email` on every call. Note that contacts are per-account - a contact in julian@idd is not visible to julian@pro. If looking up across accounts, loop over accounts.

## Cross-service handoff

When resolving a contact for a downstream operation (drafting email, looking up calendar history), this skill ends after returning the contact metadata. The orchestration layer chains to Gmail, Calendar, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Contacts (People API). Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

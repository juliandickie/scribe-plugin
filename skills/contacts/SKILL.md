---
description: Use when the user's request involves Google Contacts - looking up a person by name or email, creating contacts, searching the address book, or enriching email addresses with contact metadata. Triggers on contact, person, address book, who is X.
last-validated: 2026-05-15
---

# Scribe - Contacts

Enables Claude to read, create, search, and manage Google Contacts via the People API - useful for resolving names to emails, enriching contact info, creating new contact entries, and grouping contacts.

## When to use

Use this skill when the user's request involves -

- Looking up a contact by name to find their email

- Looking up by email to find their name and other metadata

- Creating, updating, or deleting a contact entry

- Listing contacts in a specific contact group

- Bulk-managing many contacts at once

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Contacts. Pass `user_google_email` on every call. Mutations (create/update/delete) flow through `manage_contact` or `manage_contacts_batch` with action verbs.

### list_contacts

List the user's contacts.

Parameters: `user_google_email`, optional pagination, optional field mask.

### get_contact

Read a specific contact by resource name (returned from search/list as something like `people/c12345`).

Parameters: `resource_name`, `user_google_email`, optional field mask.

### search_contacts

Search contacts by name, email, or other fields.

Parameters: `query`, `user_google_email`.

Returns: list of matching contacts with resource names.

### manage_contact

Create, update, or delete a single contact - action-based interface.

Parameters:

- `action` - `"create"`, `"update"`, or `"delete"`

- `resource_name` - required for update/delete

- Contact fields - `names`, `email_addresses`, `phone_numbers`, `organizations`, `biographies`, etc. (passed as structured data for create/update)

- `user_google_email`

### list_contact_groups

List contact groups (labels/categories).

### get_contact_group

Read a single contact group, including member contacts.

### manage_contact_group

Create, update, or delete a contact group.

Parameters: `action`, group fields, `user_google_email`.

### manage_contacts_batch

Apply create/update/delete to many contacts in a single batched call.

Parameters: `action`, list of contact payloads (each with its own fields and, for update/delete, resource_name), `user_google_email`.

## Common patterns

### Resolve a name to an email

1. `search_contacts` with the name as query.

2. Inspect the results' `email_addresses` field. If multiple matches, prompt user to disambiguate.

### Enrich an email

1. `search_contacts` with the email as query (works because the API matches across fields).

2. From the matching contact, surface name, organisation, phone numbers if present.

### Create a new contact

1. `manage_contact` with `action="create"`, populated `names`, `email_addresses`, and any other fields the user provided.

2. The response includes the new contact's `resource_name`.

### Add a contact to a group

1. `manage_contact_group` (or specific membership operations exposed by upstream) - check `get_contact_group` for membership semantics in the current API surface.

## Gotchas

- The People API uses **resource names** like `people/c12345` for contact identifiers, not raw IDs. Always pass the full resource_name returned by list/search/get.

- The People API distinguishes between contacts (people you've explicitly added) and "other contacts" (people you've emailed but not added). `search_contacts` searches your saved contacts by default; "other contacts" may need a different field mask or call.

- Workspace org contacts (directory) are separate from personal contacts. Within an org, the directory is searchable via the same People API but the result set may differ depending on org settings.

- All mutations route through `manage_contact` (or `manage_contacts_batch` for bulk). There is no separate `create_contact` or `delete_contact` tool.

## Account selection

Pass `user_google_email` on every call. Contacts are per-account - a contact saved under julian@idd is not visible to julian@pro. For cross-account lookups, loop over accounts using the credentials directory scan.

## Cross-service handoff

When resolving a contact for a downstream operation (drafting email, looking up calendar history), this skill ends after returning the contact metadata. The orchestration layer chains to Gmail, Calendar, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Contacts (People API). Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

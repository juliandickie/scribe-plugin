---
description: Given a contact name or email and a topic, pull prior email history with that contact for context and draft a contextual reply. Invoke via /scribe:smart-reply.
disable-model-invocation: true
argument-hint: <contact> <topic-or-message> [--account email]
last-validated: 2026-05-15
---

# Scribe - Smart reply

For composing a contextual email without needing to read through full thread history first. Given a contact (name or email) and a topic or message intent, pulls the user's recent email history with that contact, then drafts a reply that fits the relationship tone and references relevant prior context.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `<contact>` (required) - name or email of the recipient.

- `<topic-or-message>` (required) - what the email is about.

- `--account email` (optional) - sender account. Default - resolved from context.

If either positional arg missing, ask user.

## Tool call sequence

1. **Resolve contact email** - if name given, search Contacts. If multiple matches, prompt to disambiguate.

2. **Pull email history** - `search_gmail_messages` with `query="from:<contact-email> OR to:<contact-email>"`, limit to 5-10 most recent.

3. **Read context** - `get_gmail_messages_content_batch` for the relevant threads.

4. **Compose reply** - in the user's voice, referencing prior context where relevant. Match the tone of past correspondence with this contact (formal vs casual).

5. **Draft email** - `draft_gmail_message` with the reply.

6. **Return** - draft URL and a preview of the draft text.

## Multi-account behaviour

Single account (the sender). The history search is bound to that account.

## Cross-plugin composition

- **AC Builder plugin** - enrich contact context with AC tags and recent automation history (e.g. "this contact is in the Lead - Hot list, was last touched 3 weeks ago").

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Draft an email to Sarah about the proposal deadline"

- "Smart reply to john@example.com - we need to push the meeting"

Explicit args:

- `/scribe:smart-reply "Sarah" "Q3 proposal deadline pushback" --account julian@idd`

## Failure modes

- **Contact not found** - prompt for email.

- **No prior history** - draft anyway but note the lack of context in the response.

- **Multiple contacts match a name** - prompt user to pick.

## Output

Always return:

- Draft URL

- Preview of draft text (first 100 chars)

- Note on prior-history depth ("Drafted with 3 prior threads as context")

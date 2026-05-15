---
description: {Trigger phrase a user would actually type for this workflow. Must be specific. Max 1024 chars. Example - "Scan support inbox for new inquiries, log to a tracking sheet, draft responses."}
disable-model-invocation: true
argument-hint: {Argument signature. Single positional - "<contact-or-email>". Multi-arg - "[--account email] [--client CLIENT-ID] [--since 7d]". Empty if no args.}
last-validated: 2026-05-15
---

# Scribe - {Workflow name}

{One-paragraph description of what this workflow does and why a user would invoke it.}

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `{param1}` (optional) - {description, default if omitted}

- `{param2}` (optional) - {description, default if omitted}

If a parameter is missing and required for the workflow to proceed, ask the user once.

## Tool call sequence

1. **{Step name}** - {service} - call {tool_name} with `param1=X, param2=Y`. Why: {rationale}.

2. **{Step name}** - {service} - call {tool_name} with `param1=X`. Use the result from step 1's `field_name`.

3. **{Step name}** - {service} - call {tool_name}. {Note about parameter sourcing.}

4. **Summary** - return the resulting URL/ID and a one-line summary to the user.

## Multi-account behaviour

{One of:}

- This workflow operates on a single account. Resolve via the rules in workspace/SKILL.md.

- This workflow loops across all authenticated accounts when intent is explicit ("check both inboxes"). Otherwise uses the resolved single account.

## Cross-plugin composition

After the Scribe tool chain completes, check whether these plugins are installed and chain accordingly:

- **ClickUp plugin** - {what to do, e.g. "create a follow-up task with the doc URL in the list named X"}

- **Slack plugin** - {what to do, e.g. "post a one-line summary to channel Y"}

- **Spiffy plugin** - {what to do, omit if not relevant}

- **AC Builder plugin** - {what to do, omit if not relevant}

If a referenced plugin is not available, skip its step silently and note it in the final summary ("Posted to Drive; ClickUp plugin not installed, no task created").

## Example invocations

Natural language:

- "{Natural phrase 1}"

- "{Natural phrase 2}"

Explicit args:

- `/scribe:{workflow-slug} {example-arg-string}`

## Failure modes

- **No matching {data, e.g. emails}** - {what to do}

- **No accounts authenticated** - direct to `/scribe:auth-init`

- **Sandbox rejection on file copy** - link the user to push/SKILL.md sandbox section

- **Permission scope error** - tell the user which API they need to enable in Cloud Console

## Output

Always return:

- A short one-line summary of what happened

- URLs/IDs of any artifacts created (Doc URL, Sheet URL, draft IDs)

- A note for any cross-plugin steps that were skipped

---
description: Convert an email thread into a structured Google Doc; save any attachments into a client or contact subfolder in Drive. Invoke via /scribe:thread-to-doc.
disable-model-invocation: true
argument-hint: [--thread-id ID] [--client CLIENT-ID] [--folder ID]
last-validated: 2026-05-15
---

# Scribe - Thread to doc

Converts an email thread to a Google Doc and organises its attachments into a client folder. The doc contains the thread structured chronologically with sender, timestamp, and body per message. Attachments are saved into a per-thread subfolder under the chosen client or contact root.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--thread-id ID` (optional, prompts if missing) - the thread to convert.

- `--client CLIENT-ID` (optional) - AHPRA-style client. Resolves the destination folder via the client-resolve skill.

- `--folder ID` (optional) - explicit destination folder if not using a client.

## Tool call sequence

1. **Resolve thread** - prompt user if no `--thread-id`; offer search by sender or subject.

2. **Fetch thread content** - `get_gmail_thread_content` to pull the full thread with all messages.

3. **Resolve destination folder** - use `--folder`, OR resolve via client-resolve skill if `--client`, OR default to a "Conversations" folder under My Drive.

4. **Create thread subfolder** - `create_drive_folder` for `<thread-subject>-<date>` as a subfolder of destination.

5. **Save attachments** - per message in thread, if attachments present, `get_gmail_attachment_content` then `create_drive_file` into the thread subfolder.

6. **Create doc** - `create_doc` titled `Email thread - <subject>` in the thread subfolder.

7. **Populate doc** - `manage_doc_tab populate_from_markdown` with structured thread content. Each message as a section with sender/timestamp/body, separated by horizontal rules.

8. **Return** - the doc URL plus the subfolder URL plus an attachment count.

## Multi-account behaviour

Single account - the account that owns the thread.

## Cross-plugin composition

- **ClickUp plugin** - if the thread suggests a follow-up task, create one with the doc URL attached.

- **AC Builder plugin** - log the conversation reference against the contact's AC record.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Save this email thread to a doc"

- "Convert the thread about Q3 planning to a doc, save attachments to the iDD-internal client folder"

Explicit args:

- `/scribe:thread-to-doc --thread-id 18b... --client IDD-ED-001`

## Failure modes

- **Thread has many large attachments** - inform user of attachment sizes (sum total), ask for confirmation before downloading anything over a threshold (e.g. 100MB total).

- **Sandbox rejection on attachment save** - attachments save to Drive (not local), so the sandbox doesn't apply. If a Drive operation fails, surface the error.

- **Folder permission denied** - if the destination folder doesn't allow write, prompt user for an alternative.

## Output

Always return:

- The doc URL

- The subfolder URL

- Count of attachments saved

- Cross-plugin steps skipped

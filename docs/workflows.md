# Scribe Workflows Reference

Detailed reference for the 14 named workflow slash commands in Scribe v1.0. Each entry covers what the workflow does, parameters, full tool sequence, multi-account behaviour, cross-plugin composition options, examples, and failure modes.

For shorter prose loaded into Claude at runtime, see the individual `skills/<workflow>/SKILL.md` files. This document is a maintainer and user reference rather than a runtime-loaded skill.


---


# Scribe - Daily briefing

Compiles a daily morning briefing across all the user's authenticated Google accounts. Scans inboxes for unread/flagged messages received in the last 24 hours, pulls today's calendar events from every account's primary calendar, and surfaces anything tagged urgent or from named-VIP senders. Output is a short, scannable summary the user can read in 60 seconds.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (optional) - restrict to a single account. Default - loop across all authenticated accounts.

- `--date YYYY-MM-DD` (optional) - the day to brief on. Default - today in user's local timezone.

If a parameter is missing and required, ask the user once.

## Tool call sequence

1. **Enumerate accounts** - if `--account` was specified, use it. Otherwise list authenticated accounts by scanning `~/.workspace-mcp/credentials/*.json` filenames (see workspace skill "Enumerating authenticated accounts"). If empty, route to `/scribe:auth-init`.

2. **Per account - unread email scan** - `search_gmail_messages` with `query="(is:unread OR is:starred) newer_than:1d"`. Capture top 10 by recency.

3. **Per account - today's calendar** - `get_events` with `calendar_id="primary"`, `time_min=<date 00:00>`, `time_max=<date 23:59>`. Capture all events.

4. **Compose the briefing** - structured output with sections: Today's Calendar (per account), Unread/Flagged Email (per account), Anything Urgent (VIPs or marked urgent in subject/body).

5. **Return** - the briefing as a markdown response. Do NOT save to Drive unless the user asks.

## Multi-account behaviour

Loops across all authenticated accounts by default. Single account when `--account` is specified. This is explicit multi-account intent ("daily briefing" implies the whole picture), so auto-loop without prompting.

## Cross-plugin composition

After the Scribe tool chain completes, check whether these plugins are installed and chain accordingly:

- **ClickUp plugin** - if installed, also surface any tasks due today across configured ClickUp lists.

- **Slack plugin** - if installed, surface DMs or @mentions from the last 24 hours.

- **AC Builder plugin** - if installed, enrich unread emails from new contacts with AC tag info (e.g. "from a Lead - Course tag contact").

If a referenced plugin is not available, skip its step silently and note it in the final summary ("ClickUp plugin not installed, no task list pulled").

## Example invocations

Natural language:

- "What's on my plate today?"

- "Give me a daily briefing"

- "Daily briefing for julian@idd only"

Explicit args:

- `/scribe:daily-briefing --account julian@idd`

- `/scribe:daily-briefing --date 2026-05-16`

## Failure modes

- **No accounts authenticated** - direct to `/scribe:auth-init`.

- **Some accounts fail** (token expired for one) - skip those, note in summary, continue with the rest. Don't fail the whole briefing because of one bad account.

- **No emails or events** - produce a "Quiet day" briefing rather than empty output.

## Output

Always return:

- A short one-line summary ("3 accounts scanned, 12 unread, 4 events today, 1 urgent")

- Per-section content (Calendar, Unread, Urgent)

- A note for any cross-plugin steps that were skipped or any accounts that errored

---


# Scribe - Inbox triage

Triages the user's Gmail inbox(es). Categorises unread messages into Action (needs a reply), FYI (just read), and Noise (archive candidate). Applies appropriate labels. For Action items, drafts a reply in the user's voice (saved as draft, never sent automatically).

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (optional) - single account. Default - all authenticated accounts.

- `--since 7d` (optional) - time window. Default - 24 hours.

- `--no-drafts` (optional flag) - skip the draft-reply step.

## Tool call sequence

1. **Resolve accounts** - `--account` if specified, otherwise list authenticated accounts by scanning `~/.workspace-mcp/credentials/*.json` filenames (see workspace skill "Enumerating authenticated accounts").

2. **Per account - fetch unread** - `search_gmail_messages` with `query="is:unread newer_than:<since>"`.

3. **Per message - read content** - `get_gmail_message_content` for body and headers.

4. **Classify each message** - Action / FYI / Noise based on sender, subject patterns, and content cues. Examples - direct questions to user = Action; newsletters = FYI; "unsubscribe" footers prominent = Noise.

5. **Label setup** - `list_gmail_labels` to find or create `Triage/Action`, `Triage/FYI`, `Triage/Noise`. Use `manage_gmail_label` to create any missing.

6. **Apply labels** - `batch_modify_gmail_message_labels` to apply categorisation in one call per account.

7. **Draft replies** (unless `--no-drafts`) - for each Action message, `draft_gmail_message` with a contextual reply.

8. **Return summary** - counts per category, list of drafted replies with links to drafts.

## Multi-account behaviour

Loops across all authenticated accounts by default. Single account when `--account` is specified.

## Cross-plugin composition

- **ClickUp plugin** - for Action items that look like task creation requests, create a ClickUp task and link the email URL.

- **Slack plugin** - post a one-line triage summary to a designated channel ("Triaged 47 emails - 8 Action, 12 FYI, 27 Noise").

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Triage my inbox"

- "Sort my unread from the last week"

- "Inbox triage but don't draft replies"

Explicit args:

- `/scribe:inbox-triage --since 3d --no-drafts`

- `/scribe:inbox-triage --account julian@idd`

## Failure modes

- **Label creation forbidden** - some Workspace orgs restrict label creation. Fall back to categorisation in the output without applying labels.

- **Draft creation fails** - the user's scope may be readonly. Surface what would have been drafted as text in the response.

- **No unread** - report clean inbox.

## Output

Always return:

- Category counts per account

- Drafted replies with draft URLs

- Any cross-plugin steps skipped

---


# Scribe - Support inquiry scan

Designed for support inbox triage. Scans a specified account's inbox for new inquiries in the time window, classifies each (general inquiry, complaint, refund, course-question, other), logs each row to a designated tracking sheet, and drafts an initial response in the support team's voice.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--account email` (required if user has multiple accounts) - the support inbox to scan.

- `--sheet-id ID` (required first time) - the tracking sheet ID. Cached in conversation for repeat invocations.

- `--since 1d` (optional) - time window. Default - 1 day.

If `--sheet-id` is missing, ask the user once.

## Tool call sequence

1. **Validate parameters** - if `--sheet-id` missing, ask user. If user has multiple accounts and no `--account`, ask which.

2. **Scan inbox** - `search_gmail_messages` with `query="is:unread newer_than:<since>"` on the support account.

3. **Per message - read thread** - `get_gmail_thread_content` for full context including any prior reply.

4. **Classify intent** - rule-based or LLM judgment in prose. Categories - inquiry, complaint, refund, course-question, other.

5. **Per inquiry - log to sheet** - append row with `[timestamp, sender, subject, classification, thread_url, status="new"]`.

6. **Per inquiry - draft response** - `draft_gmail_message` with a context-aware reply that acknowledges and asks any clarifying questions.

7. **Return summary** - counts per category, sheet URL with rows added, list of drafted responses with draft URLs.

## Multi-account behaviour

Single account (the designated support inbox). Requires `--account` if the user has multiple authenticated accounts.

## Cross-plugin composition

- **ClickUp plugin** - for inquiries classified as bugs/complaints, create a ClickUp task in the support list with the email URL.

- **Slack plugin** - post new urgent inquiries (complaints, refund requests) to a `#support` channel.

- **Spiffy plugin** - for refund or credit inquiries, look up purchase history and credit balance before drafting the response. Include the lookup result in the draft.

- **AC Builder plugin** - enrich sender info with AC tags before classification (e.g. "this contact is in the Course - Implant 2026 list").

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Scan our support inbox"

- "Run support triage on julian@idd, log to the support tracker"

Explicit args:

- `/scribe:support-scan --account support@idd --sheet-id 1AB...XYZ --since 12h`

## Failure modes

- **Sheet not found** - prompt user for correct sheet ID or offer to create one.

- **No new inquiries** - report "No new inquiries in window" and exit clean.

- **Classification ambiguous** - default to "other" and surface for human review in the sheet status column.

## Output

Always return:

- One-line summary - "Logged X new inquiries, drafted Y responses"

- Sheet URL

- Per-category counts

- Draft URLs

- Cross-plugin steps skipped

---


# Scribe - Meeting prep

Builds a structured prep doc for a meeting. Pulls the calendar event (next upcoming OR specified by title or ID), looks up related emails from each attendee across the user's accounts, and assembles a doc with Attendees, Context, Discussion topics, and Open questions sections.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--event "title"` OR `--event-id ID` - specifies the event. If neither, use the next upcoming event on the primary calendar.

- `--account email` (optional) - account that owns the event. Default - resolved per the standard rules.

- `--folder ID` (optional) - Drive folder for the prep doc. Default - a folder named "Meeting briefings" under the user's My Drive, created if absent.

## Tool call sequence

1. **Resolve event** - `get_events` with appropriate `time_min`/`time_max` to find next upcoming, OR `get_events` with `event_id=<id>` if `--event-id` provided, OR `get_events` with `query=<title>` if `--event "title"` provided.

2. **Extract attendees** - parse attendee emails from the event.

3. **Per attendee - find recent threads** - `search_gmail_messages` with `query="from:<attendee> OR to:<attendee>"`, capture top 5 by recency. Loop across accounts if multiple.

4. **Resolve target folder** - `search_drive_files` for "Meeting briefings", `create_drive_folder` if absent.

5. **Create prep doc** - `create_doc` titled `Meeting prep - <event title> - <date>`.

6. **Populate the doc** - `manage_doc_tab populate_from_markdown` with sections - Attendees (names + emails + brief context), Meeting context (event description, location, time), Recent communication (links to top emails per attendee), Agenda (placeholder), Open questions (placeholder).

7. **Return** - the doc URL plus a one-line summary of attendees and recent context found.

## Multi-account behaviour

Uses the account that owns the event by default. Cross-account email search per attendee uses all authenticated accounts (an attendee might appear in either inbox).

## Cross-plugin composition

- **ClickUp plugin** - if the event title or description mentions a ClickUp task or list, link it in the prep doc.

- **AC Builder plugin** - enrich attendee context with AC tags and recent automation history.

- **Slack plugin** - find prior Slack discussions about the meeting topic or attendees, link in the doc.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Prep for my next meeting"

- "Meeting prep for the Q3 planning event"

- "Build a briefing doc for tomorrow's call with Sarah"

Explicit args:

- `/scribe:meeting-prep --event-id ABC123 --folder DEF456`

## Failure modes

- **No upcoming events** - tell user and offer to search by title.

- **Multiple events match a title query** - prompt user to pick.

- **Attendees list empty** (solo event) - skip the attendee section, build the doc with just the event context.

## Output

Always return:

- The prep doc URL

- A one-line summary ("Meeting prep doc created for 'Q3 planning' with 4 attendees, 18 related emails surfaced")

- Cross-plugin steps skipped

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

---


# Scribe - Client digest

Builds a comprehensive activity digest for a specific client, contact, or company. Surfaces all email threads, calendar events, and Drive document activity (comments, suggested edits, recent modifications) related to that entity within the time window.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `<client-or-contact>` (positional, required) - name, email, or AHPRA CLIENT-ID.

- `--since 7d` (optional) - time window. Default - 7 days.

- `--account email` (optional) - account to scope to. Default - all accounts.

If positional arg missing, ask user.

## Tool call sequence

1. **Resolve the contact** - if AHPRA CLIENT-ID, use the client-resolve skill. If name, search Contacts. If email, use directly.

2. **Resolve accounts** - all unless `--account` specified.

3. **Per account - email scan** - `search_gmail_messages` with `query="from:<email> OR to:<email> newer_than:<since>"`.

4. **Per account - calendar scan** - `get_events` with `query=<contact-name>` (note - the parameter is `query`, not `q`) or filter events with the contact as attendee.

5. **Drive search** - `search_drive_files` for docs that mention the contact's name or are shared with their email.

6. **Per matching doc - comment activity** - `list_document_comments` to surface comment activity in the time window.

7. **Assemble digest** - sections - Emails (per account), Calendar events, Drive activity (modified, shared, commented).

8. **Return** - as markdown summary OR save to a doc if user prefers (ask once if not specified).

## Multi-account behaviour

Loops all accounts by default. Single account if `--account` specified.

## Cross-plugin composition

- **AC Builder plugin** - include the contact's AC tags, list memberships, and recent automation history.

- **Slack plugin** - search Slack channels for mentions of the contact or company name.

- **Spiffy plugin** - if the contact is a customer, include purchase history, course progress, and credit balance.

- **ClickUp plugin** - surface any open ClickUp tasks tied to the contact (search for the contact name in task titles or descriptions).

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Tell me everything about Sarah Smith"

- "Client digest for IDD-ED-007 over the last 30 days"

- "What's been happening with john@example.com lately?"

Explicit args:

- `/scribe:client-digest "sarah@example.com" --since 30d`

## Failure modes

- **No matches** - report "No activity found in window for <contact>".

- **Multiple contacts match a name** - prompt user to pick by listing options with disambiguating info (organisation, last contact date).

## Output

Always return:

- One-line summary - "Found X emails, Y events, Z Drive docs with activity for <contact>"

- Per-section content

- Cross-plugin steps skipped

---


# Scribe - Weekly wrap

Generates a weekly summary report compiling all the user's activity across Gmail, Calendar, and Drive into a structured doc. Sections include emails sent and received, meetings attended, docs created or significantly edited.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--week current|last|N` (optional) - default `last`. `current` = this week so far, `last` = last full week, `N` = N weeks ago.

- `--output-folder ID` (optional) - destination Drive folder. Default - "Weekly wraps" folder under My Drive, created if absent.

- `--account email` (optional) - single account. Default - all accounts.

## Tool call sequence

1. **Compute week date range** - based on `--week`. "last" = previous Monday-Sunday window in user's timezone.

2. **Resolve accounts** - all unless `--account` specified.

3. **Per account - email received** - `search_gmail_messages` with `query="newer_than:<7d> older_than:<0d>"` (adjusted for the chosen week).

4. **Per account - email sent** - same, with `in:sent` filter.

5. **Per account - calendar events** - `get_events` for the week's range.

6. **Drive activity** - `search_drive_files` for files modified in the week's range owned by the user.

7. **Resolve output folder** - `search_drive_files` for "Weekly wraps", `create_drive_folder` if absent.

8. **Create wrap doc** - `create_doc` titled `Weekly wrap - <week-of-date>` in output folder.

9. **Populate doc** - sections - Activity overview (counts), Notable emails sent and received, Meetings attended, Documents created and edited.

10. **Return** - the doc URL plus a one-line summary.

## Multi-account behaviour

Loops all accounts by default. The output doc surfaces per-account breakdowns in each section.

## Cross-plugin composition

- **ClickUp plugin** - include tasks completed and tasks created in the week from configured lists.

- **Spiffy plugin** - include the week's enrollment, refund, and credit activity.

- **Slack plugin** - include count of messages sent in monitored channels.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Give me a weekly wrap"

- "Compile last week's activity into a report"

- "Weekly wrap for two weeks ago"

Explicit args:

- `/scribe:weekly-wrap --week last --output-folder ABC...`

- `/scribe:weekly-wrap --week 2`

## Failure modes

- **No activity** - produce a doc anyway with "Quiet week" sections.

- **Output folder creation fails** - save to My Drive root with a fallback name.

- **Some accounts fail** - skip those, note in the doc.

## Output

Always return:

- The wrap doc URL

- One-line summary - "Compiled X emails, Y events, Z docs from N accounts"

- Cross-plugin steps skipped

---


# Scribe - Follow-up tracker

Identifies sent emails that haven't received a reply after a configurable threshold (default 7 days). Optionally drafts polite follow-up replies for each.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--days N` (optional, default 7) - how many days without reply before flagging.

- `--account email` (optional) - single account. Default - all accounts.

- `--draft-replies` (optional flag) - also draft a follow-up reply for each.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Per account - sent emails in window** - `search_gmail_messages` with `query="in:sent older_than:<days>d newer_than:<days+30>d"` (cap at 30 days back to avoid an unbounded scan).

3. **Per message - check for reply** - `get_gmail_thread_content` to see whether a reply came after the original sent message.

4. **Filter** - to those with no reply (threads where the latest message is the user's sent one, with no incoming after).

5. **Optional draft** - if `--draft-replies`, `draft_gmail_message` per item with a polite follow-up referencing the original.

6. **Return** - list with subject, recipient, days-since-sent, and (if drafted) draft URLs.

## Multi-account behaviour

Loops all accounts by default.

## Cross-plugin composition

- **ClickUp plugin** - for follow-ups that look task-related (e.g. follow-up on a quote, proposal, deliverable), create a "follow up" task with the email URL.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "What emails am I waiting on replies to?"

- "Find emails I sent two weeks ago that haven't been answered, draft follow-ups"

Explicit args:

- `/scribe:follow-up-tracker --days 14 --draft-replies`

- `/scribe:follow-up-tracker --account julian@idd`

## Failure modes

- **No unanswered emails** - report clean inbox.

- **Thread structure ambiguous** (user replied to self after sending) - filter heuristic should ignore self-replies as "no reply received."

- **Recipients with autoresponders** - autoresponder text may look like a reply. Treat single-message responses with "out of office" patterns as non-replies.

## Output

Always return:

- One-line summary - "X emails awaiting reply older than Y days"

- List of emails with subject, recipient, days-since

- Draft URLs if drafted

- Cross-plugin steps skipped

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

---


# Scribe - Doc review chaser

Finds Google Docs that have been shared for review but haven't been touched (no comments, suggested edits, or content changes) within the time window. Drafts polite reminder emails to the inactive reviewers.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--folder ID` (optional) - scope to docs in this folder. Default - all docs owned by the user.

- `--days N` (optional, default 7) - inactivity threshold.

- `--account email` (optional) - single account.

- `--draft-reminders` (optional flag) - also draft reminder emails.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Find candidate docs** - `search_drive_files` (or `list_docs_in_folder` if folder specified) for Docs owned by the user, modified more than `--days` ago.

3. **Per doc - find reviewers** - `get_drive_file_permissions` to find users with commenter or writer role (not owner).

4. **Per doc - check activity** - `list_document_comments` to check for recent comment activity in the inactivity window.

5. **Filter** - to docs with reviewers AND no comment/edit activity.

6. **Draft reminders** (if `--draft-reminders`) - per doc, per inactive reviewer, `draft_gmail_message` with a polite nudge linking the doc.

7. **Return** - list of stale docs with reviewer emails and draft URLs.

## Multi-account behaviour

Single account by default unless explicit multi-account intent.

## Cross-plugin composition

- **Slack plugin** - for reviewers in shared Slack workspaces, optionally DM them instead of email (faster response loop for internal reviewers).

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "What docs am I waiting on review for?"

- "Chase up outstanding doc reviews from last week"

Explicit args:

- `/scribe:doc-chase --folder ABC --days 10 --draft-reminders`

## Failure modes

- **No stale docs** - report clean state.

- **Multiple reviewers per doc** - draft separate reminders per reviewer (each personalised).

- **Doc is in a Shared Drive with org-wide access** - skip "all org" reviewers, only nudge specific named reviewers.

## Output

Always return:

- One-line summary - "Found X stale docs with Y inactive reviewers"

- List of docs with reviewer emails

- Draft URLs if drafted

- Cross-plugin steps skipped

---


# Scribe - Attachment vault

Periodic attachment archival. Scans Gmail for emails with attachments in the time window, downloads each attachment, and organises them into Drive folders by sender (default) or by project (heuristic on subject line).

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--since 30d` (optional) - time window. Default - 30 days.

- `--by sender|project` (optional) - organisation strategy. Default - `sender`.

- `--vault-root ID` (optional) - parent Drive folder. Default - "Attachment vault" under My Drive.

- `--account email` (optional) - single account or default to all.

## Tool call sequence

1. **Resolve accounts** - all unless `--account` specified.

2. **Per account - find emails with attachments** - `search_gmail_messages` with `query="has:attachment newer_than:<since>"`.

3. **Per message - extract metadata** - sender, subject, attachment list (name, size).

4. **Resolve vault root** - `search_drive_files` for "Attachment vault", `create_drive_folder` if absent.

5. **Determine destination subfolder** per attachment - `Vault/<sender-domain>/<sender>` for sender mode; `Vault/<project-tag>` for project mode where project-tag is heuristic on subject (e.g. extract bracketed prefixes like `[Project X]`).

6. **Create subfolders** as needed - `create_drive_folder`.

7. **Download and save attachments** - `get_gmail_attachment_content` then `create_drive_file` into the appropriate subfolder.

8. **Return** - summary of counts per subfolder, total attachments archived, total bytes.

## Multi-account behaviour

Loops all accounts by default.

## Cross-plugin composition

None specific. This is a pure Workspace workflow.

## Example invocations

Natural language:

- "Archive all my email attachments from the last month"

- "Save attachments to a vault by sender"

Explicit args:

- `/scribe:attach-vault --since 60d --by project`

- `/scribe:attach-vault --vault-root ABC...`

## Failure modes

- **Very large attachments** - confirm before downloading anything over a threshold (e.g. 50MB single file or 1GB cumulative).

- **Duplicate filenames** - append `-<timestamp>` to disambiguate.

- **Sandbox issues** - attachments save to Drive (not local), so the sandbox doesn't apply. If a Drive operation fails, surface the error.

## Output

Always return:

- Summary of counts per subfolder

- Total attachments archived

- Total bytes (rough)

- Any download skips with reason

---


# Scribe - Event recap

Post-meeting workflow. Pulls the most recent past calendar event (or specified by ID), gathers any emails from attendees since the event happened, creates a notes and action-items doc, and drafts a follow-up email to attendees.

## Parameters

User input arrives in `$ARGUMENTS` as a free-form string. Parse for:

- `--event-id ID` (optional) - default - most recent past event.

- `--account email` (optional) - account that owns the event.

- `--folder ID` (optional) - destination for the recap doc. Default - "Meeting recaps" folder under My Drive.

## Tool call sequence

1. **Resolve event** - most recent past event via `get_events` with `time_max=<now>` (sort desc, take first), OR by ID via `get_events` with `event_id=<id>`.

2. **Extract metadata** - attendees, original event description, location, time range.

3. **Per attendee - find post-event emails** - `search_gmail_messages` with `query="from:<attendee> newer_than:<event-time-iso>"` for follow-up communication.

4. **Resolve recap folder** - `search_drive_files` for "Meeting recaps", `create_drive_folder` if absent.

5. **Create recap doc** - `create_doc` titled `Recap - <event title> - <date>`.

6. **Populate doc** - sections - Event summary (title, time, attendees, original description), Attendees (with their post-event emails linked), Notes (placeholder), Action items (placeholder), Post-meeting emails (links).

7. **Draft follow-up** - `draft_gmail_message` to all attendees with the doc link and a brief summary.

8. **Return** - doc URL plus draft URL.

## Multi-account behaviour

Single account (the event owner's).

## Cross-plugin composition

- **ClickUp plugin** - for action items detected or added later in the notes section, offer to create ClickUp tasks (this is more of a "next step" suggestion than an automatic action).

- **Slack plugin** - post the recap doc link to a designated channel.

If a referenced plugin is not available, skip and note in summary.

## Example invocations

Natural language:

- "Recap my last meeting"

- "Build a recap doc from this morning's call"

Explicit args:

- `/scribe:event-recap --event-id ABC123`

- `/scribe:event-recap --folder DEF456`

## Failure modes

- **No recent past event** - prompt user to specify.

- **Multi-day or recurring event** - clarify which occurrence to recap.

- **No attendees** (solo blocked time) - skip the follow-up draft.

## Output

Always return:

- Recap doc URL

- Follow-up draft URL (if attendees present)

- One-line summary

- Cross-plugin steps skipped

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

---

## Cross-workflow patterns

These patterns recur across multiple workflows -

- **Multi-account loop** - workflows that scan or compile across accounts enumerate authenticated accounts by scanning the credentials directory (`~/.workspace-mcp/credentials/*.json`). The orchestration router (`workspace/SKILL.md` "Enumerating authenticated accounts") documents the exact command. `workspace-mcp` does NOT expose a `list_authenticated_accounts` MCP tool.

- **Attachment handling** - workflows that download attachments use `get_gmail_attachment_content` then `create_drive_file`. The sandbox at `~/.workspace-mcp/attachments` constrains local file uploads only, not Drive operations.

- **Cross-plugin defer** - any workflow can chain into ClickUp, Slack, Spiffy, AC Builder, or other plugins by referencing them in prose. Claude reads the hint and chains naturally.

## Authoring new workflows

Add a new workflow skill in v1.1+ by copying `docs/skill-templates/workflow-skill-template.md` to `skills/<workflow-slug>/SKILL.md`, filling in the placeholders, and adding the slug to the validation loop in `Makefile`.

---
description: Use when the user's request involves Google Slides - reading or updating slide content, creating presentations, modifying slide elements, generating decks from outlines. Triggers on presentation, deck, slide, slides, slideshow.
last-validated: 2026-05-15
---

# Scribe - Slides

Enables Claude to read, create, and update Google Slides presentations. All structural updates flow through `batch_update_presentation` with a list of requests (mirroring the Google Slides API's batchUpdate pattern).

## When to use

Use this skill when the user's request involves -

- Reading the content of an existing deck

- Creating new presentations from a structure or outline

- Adding or updating slides within a deck

- Modifying text on specific slides

- Getting thumbnails of specific slides

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Slides. Pass `user_google_email` on every call.

### create_presentation

Create a new presentation (new file in Drive).

Parameters: `title`, optional `parent_folder_id`, `user_google_email`.

### get_presentation

Read a presentation's full structure - all pages (slides), all elements, layouts.

Parameters: `presentation_id`, `user_google_email`.

### batch_update_presentation

The workhorse mutation tool. Accepts a list of update requests. All slide creation, deletion, text edits, image inserts, layout changes go through this.

Parameters:

- `presentation_id`

- `requests[]` - list of update request objects. Each follows the Google Slides API batchUpdate shape (e.g. `{"createSlide": {...}}`, `{"insertText": {...}}`, `{"deleteObject": {...}}`).

- `user_google_email`

### get_page

Read a single slide (page) by ID.

### get_page_thumbnail

Get a thumbnail image of a specific slide.

## Common patterns

### Generate a deck from an outline

1. `create_presentation` with the deck title - returns the new presentation ID and the default first slide ID.

2. `batch_update_presentation` with a request list that adds one slide per outline section. For each new slide, also include `insertText` requests to populate title and body placeholders. Batch them in one call where possible - it's atomic and faster.

### Read existing deck and summarise

1. `get_presentation` to fetch all slides.

2. Walk the pages array; for each page surface its title and key text content as a structured summary.

### Add a slide at a specific position

1. `batch_update_presentation` with a `createSlide` request including `insertionIndex` and `slideLayoutReference`.

### Replace text on a specific slide

1. `batch_update_presentation` with a `replaceAllText` request scoped to the specific page object ID, or with `deleteText` + `insertText` requests targeting a specific element.

## Gotchas

- All structural changes flow through `batch_update_presentation`. There is NO separate `add_slide` or `update_slide_content` tool - those operations are individual request objects within a batchUpdate call.

- Layouts are template-driven. Use `slideLayoutReference` with predefined layout IDs (e.g. `TITLE_AND_BODY`, `TITLE`, `SECTION_HEADER`) when creating slides. Custom layouts have their own IDs visible in `get_presentation` output.

- `batch_update_presentation` is atomic - if any request in the list fails, none are applied. Group operations that should succeed-or-fail together.

- Slide IDs are different from indexes. The first slide is at index 0 but its object ID is a random string (or "p" prefix for default). Always use IDs from `get_presentation` rather than guessing.

- Placeholders (title, body, etc.) have their own object IDs distinct from the slide's ID. To insert text into a title placeholder, target the placeholder's object ID, not the slide ID.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` for account selection rules.

## Cross-service handoff

When generating a deck from a Doc or other source, this skill handles the slide creation. The orchestration layer handles chaining to other services (e.g. reading the source Doc first).

## Source

This skill wraps `workspace-mcp` tools for Google Slides. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

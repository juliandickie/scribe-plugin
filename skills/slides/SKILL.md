---
description: Use when the user's request involves Google Slides - reading or updating slide content, creating presentations, modifying slide elements, generating decks from outlines. Triggers on presentation, deck, slide, slides, slideshow.
last-validated: 2026-10-01
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

The following tools are exposed by workspace-mcp@2.5.0 for Slides. Pass `user_google_email` on every call.

### create_presentation

Create a new presentation (new file in Drive).

Parameters: `title`, `user_google_email`. No folder parameter on the pinned 2.5.0 - it lands in My Drive root; move it with `update_drive_file`.

### get_presentation

Read a deck by `action`. Rebuilt in workspace-mcp 2.5.0 - the `include_speaker_notes`, `include_geometry` and `include_styles` flags and the separate `get_page` tool are gone; a bare call still works because `action` defaults to `"deck"`.

Parameters:

- `presentation_id`, `user_google_email`

- `action` - `"deck"` (default) lists the title, URL, revision and, per slide, its ID, title, layout, element counts and notes length, then the layouts with their placeholders, 100 slides per call (continue with `offset`); `"page"` returns every element on one slide in z-order with all text, table cells, image sources and speaker notes, no geometry or styling (start here for content); `"markup"` returns one slide, or chosen elements, as compact JSON with boxes in points, text runs and a shared styles table; `"layouts"` lists every layout grouped by master (continue with `after`)

- `page_id` - the slide object ID from `"deck"`; required for `"page"` and `"markup"`

- `offset` - for `"deck"`, the first slide index to list, from the note at the end of the previous call

- `after` - for `"layouts"`, a slide ID or `"start"`, listing only the layouts a slide inserted there can use

- `targets` - for `"markup"`, element IDs to return instead of the whole slide, plus `"notes"` for the speaker notes (the notes shape ID lets notes be replaced or appended through `batch_update_presentation`)

### batch_update_presentation

The workhorse mutation tool. Accepts a list of update requests. All slide creation, deletion, text edits, image inserts, layout changes go through this.

Parameters:

- `presentation_id`

- `requests[]` - list of update request objects. Each follows the Google Slides API batchUpdate shape (e.g. `{"createSlide": {...}}`, `{"insertText": {...}}`, `{"deleteObject": {...}}`).

- `user_google_email`

### render_page_to_image

Render a slide (or any page, including a notes page) to an image and return it as image content, so you can look at its layout and visuals directly. Replaced `get_page_thumbnail` in workspace-mcp 2.2.0, which returned a thumbnail URL instead of the image.

Parameters:

- `presentation_id`

- `page_object_id` - the slide's object ID (from `get_presentation`)

- `size` - `"SMALL"` (200px, layout only, text unreadable), `"MEDIUM"` (800px, the default, reads titles and body text), `"LARGE"` (1600px, for small text such as tables, chart labels and footnotes) or `"WIDTH2000_PX"` (rarely reads more than LARGE). Start at MEDIUM; LARGE costs about four times the image tokens.

- `user_google_email`

## Common patterns

### Generate a deck from an outline

1. `create_presentation` with the deck title - returns the new presentation ID and the default first slide ID.

2. `batch_update_presentation` with a request list that adds one slide per outline section. For each new slide, also include `insertText` requests to populate title and body placeholders. Batch them in one call where possible - it's atomic and faster.

### Read existing deck and summarise

1. `get_presentation` with the default `"deck"` action to list the slides, then `action: "page"` with each `page_id` whose text you need.

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

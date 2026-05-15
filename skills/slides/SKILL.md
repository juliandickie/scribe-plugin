---
description: Use when the user's request involves Google Slides - reading or updating slide content, creating presentations, modifying slide elements, or working with decks. Triggers on presentation, deck, slide, slides, slideshow.
last-validated: 2026-05-15
---

# Scribe - Slides

Enables Claude to read, create, and update Google Slides presentations - slide content, layout, and text.

## When to use

Use this skill when the user's request involves -

- Reading the content of an existing deck

- Creating new presentations from a structure or outline

- Adding or updating slides within a deck

- Modifying text on specific slides

## MCP tool reference

The exact tool names exposed for Slides depend on the workspace-mcp version. At runtime, inspect the available MCP tools panel for the current set. Typical operations:

### read_presentation / get_presentation

Returns all slide contents.

Parameters: `presentation_id`, `user_google_email`.

### create_presentation

Create a new presentation in Drive.

Parameters: `title`, `parent_folder_id` (optional), `user_google_email`.

### add_slide

Add a slide to an existing presentation.

Parameters: `presentation_id`, `layout` (e.g. `"TITLE"`, `"TITLE_AND_BODY"`), `index` (optional position), `user_google_email`.

### update_slide_content

Modify text or elements on a specific slide.

Parameters: `presentation_id`, `slide_id`, content updates, `user_google_email`.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel and update this section.**

## Common patterns

### Generate a deck from an outline

1. `create_presentation` with the deck title.

2. Per outline section, `add_slide` with the appropriate layout.

3. `update_slide_content` to set title and body text per slide.

### Read existing deck and summarise

1. `read_presentation` to fetch all slides.

2. Surface slide titles and key text content as a structured summary.

## Gotchas

- Slides has rich layout primitives (text boxes, shapes, images). Don't assume a slide is just a title and bullets.

- Layouts are template-driven. Changing a slide's layout often requires understanding the master slide structure.

- Slide IDs are different from page numbers. Always work with IDs returned from `read_presentation` or `add_slide`.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` for account selection rules.

## Cross-service handoff

When generating a deck from a Doc or other source, this skill handles the slide creation. The orchestration layer handles chaining to other services.

## Source

This skill wraps `workspace-mcp` tools for Google Slides. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

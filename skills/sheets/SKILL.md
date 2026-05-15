---
description: Use when the user's request involves Google Sheets - reading cell values, writing data, appending rows, working with ranges in A1 notation, formulas, or creating new spreadsheets. Triggers on spreadsheet, sheet, rows, columns, cells, range, formula, csv data.
last-validated: 2026-05-15
---

# Scribe - Sheets

Enables Claude to read and write Google Sheets - ranges, individual cells, full sheets, formulas, and structured data tables.

## When to use

Use this skill when the user's request involves -

- Reading data from a specific Sheet or range

- Appending rows to a tracking sheet

- Updating cells with computed values or formulas

- Creating new sheets or duplicating templates

- Exporting structured data into a Sheet

## MCP tool reference

The exact tool names exposed for Sheets depend on the workspace-mcp version. At runtime, inspect the available MCP tools panel for the current set. The typical operations exposed are:

### read_range / get_sheet_values

Return cell values for an A1-notated range.

Parameters:

- `spreadsheet_id`

- `range` - A1 notation, e.g. `"Sheet1!A1:C10"`

- `user_google_email`

Returns: 2D array of cell values.

### write_range / update_sheet_values

Overwrite cell values for a range.

Parameters:

- `spreadsheet_id`

- `range`

- `values[][]` - 2D array

- `user_google_email`

### append_row / append_values

Add a new row at the bottom of the data region.

Parameters:

- `spreadsheet_id`

- `sheet_name` (or range with sheet specified)

- `values[]` - row contents

- `user_google_email`

### create_spreadsheet

Create a new spreadsheet (new file in Drive).

Parameters: `title`, `parent_folder_id` (optional), `user_google_email`.

### create_sheet / add_sheet

Add a new tab (sheet) to an existing spreadsheet.

### clear_range

Empty cells without deleting the structure.

**At implementation time, verify the actual tool names by inspecting the MCP tools panel and update this section.** The patterns below describe the conceptual operations regardless of exact tool names.

## Common patterns

### Log a support inquiry

1. Read header row to confirm column layout (e.g. `range="Tracker!A1:F1"`).

2. Append row with `[timestamp, sender, subject, link_to_thread, classification, status]`.

### Read a config sheet

1. Read named range like `Config!A1:B20`.

2. Parse rows into key-value pairs.

### Bulk update

- Prefer batched range writes over per-cell calls for performance. One write to a 10x10 range is much faster than 100 individual cell writes.

## Gotchas

- Sheets use A1 notation (`Sheet1!A1:B10`) - not R1C1. Always include the sheet name when working with a multi-sheet spreadsheet.

- Empty cells return as missing values, not empty strings. Be defensive when parsing rows - check for `None` or undefined.

- Sheet IDs (`gid` in URLs) are different from spreadsheet IDs. The spreadsheet ID is the long random string in the URL; the sheet ID is the small numeric `gid` parameter.

- Append-row finds the first empty row in a sheet, not necessarily after the last data row. If a sheet has gaps, append may slot into a gap. For strict append-at-end behaviour, read the last-row index first and write to that row + 1.

- Date and time values are returned as serial numbers unless the column is formatted as date. Format the column or convert in-prose.

## Account selection

Pass `user_google_email` on every call. The full account selection logic lives in `skills/workspace/SKILL.md` under "Multi-account routing."

## Cross-service handoff

When a request spans services (e.g. logging an email to a sheet), this skill's role ends after the sheet operation. The orchestration layer handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Sheets. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

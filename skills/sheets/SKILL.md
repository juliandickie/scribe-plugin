---
description: Use when the user's request involves Google Sheets - reading cell values, writing data, appending rows, working with ranges in A1 notation, formulas, formatting, or creating new spreadsheets. Triggers on spreadsheet, sheet, rows, columns, cells, range, formula, csv data.
last-validated: 2026-05-15
---

# Scribe - Sheets

Enables Claude to read and write Google Sheets - ranges, individual cells, full sheets, formulas, structured data tables, and formatting.

## When to use

Use this skill when the user's request involves -

- Reading data from a specific Sheet or range

- Appending rows to a tracking sheet (using a structured table)

- Updating cells with computed values or formulas

- Creating new spreadsheets or sheets (tabs)

- Formatting cells, ranges, or applying conditional formatting

- Listing spreadsheets, sheets, or tables

## MCP tool reference

The following tools are exposed by workspace-mcp@1.20.4 for Sheets. Pass `user_google_email` on every call.

### list_spreadsheets

List spreadsheets visible to the user (paginates Drive for Sheet-type files).

### get_spreadsheet_info

Get metadata for a spreadsheet (title, sheets list with IDs, named ranges).

Parameters: `spreadsheet_id`, `user_google_email`.

### read_sheet_values

Read cell values for an A1-notated range.

Parameters: `spreadsheet_id`, `range` (e.g. `"Sheet1!A1:C10"`), `user_google_email`.

Returns: 2D array of cell values.

### modify_sheet_values

Write cell values for a range. Supports overwrite and append modes.

Parameters: `spreadsheet_id`, `range`, `values` (2D array), `user_google_email`, and a mode/option to control overwrite vs. append.

### format_sheet_range

Apply formatting (font, color, borders, number formats) to a range.

### manage_conditional_formatting

Add, update, or remove conditional formatting rules.

### create_spreadsheet

Create a new spreadsheet (new file in Drive).

Parameters: `title`, optional `parent_folder_id`, `user_google_email`.

### create_sheet

Add a new sheet (tab) to an existing spreadsheet.

Parameters: `spreadsheet_id`, `title`, `user_google_email`.

### list_sheet_tables

List structured tables defined within a spreadsheet (named tables, not raw data regions).

### append_table_rows

Append one or more rows to a structured table. This is the canonical pattern for tracking sheets where you want strict append semantics.

Parameters: `spreadsheet_id`, `table_name` (or table reference), `rows[][]`, `user_google_email`.

### resize_sheet_dimensions

Resize rows or columns (e.g. set column widths).

### move_sheet_rows

Move rows within a sheet.

## Common patterns

### Log a support inquiry into a tracking table

1. `list_sheet_tables` (or `get_spreadsheet_info`) to confirm the target table exists.

2. `append_table_rows` with `[timestamp, sender, subject, link_to_thread, classification, status]`.

If the target sheet is not a structured table, use `modify_sheet_values` instead to write the row at the next empty row found via `read_sheet_values` on the relevant column.

### Read a config sheet

1. `read_sheet_values` with `range="Config!A1:B20"`.

2. Parse rows into key-value pairs in prose.

### Bulk update

- Prefer batched range writes via `modify_sheet_values` over per-cell calls. One write to a 10x10 range is much faster than 100 individual cell writes.

## Gotchas

- Sheets use A1 notation (`Sheet1!A1:B10`) - not R1C1. Always include the sheet name when working with a multi-sheet spreadsheet.

- Empty cells return as missing values, not empty strings. Be defensive when parsing rows - check for `None` or undefined.

- Sheet IDs (`gid` in URLs) are different from spreadsheet IDs. The spreadsheet ID is the long random string in the URL; the sheet ID is the small numeric `gid` parameter.

- `append_table_rows` requires a structured table. If the sheet is just raw data without a defined table, use `modify_sheet_values` and compute the target row manually. The structured-table path is more robust for tracking sheets created specifically for logging.

- Date and time values are returned as serial numbers unless the column is formatted as date. Format via `format_sheet_range` or convert in prose.

## Account selection

Pass `user_google_email` on every call. See `skills/workspace/SKILL.md` "Multi-account routing" for the selection rules.

## Cross-service handoff

When a request spans services (e.g. logging an email to a sheet), this skill's role ends after the sheet operation. The orchestration layer in workspace/SKILL.md handles chaining to Gmail, Drive, etc.

## Source

This skill wraps `workspace-mcp` tools for Google Sheets. Upstream issues go to https://github.com/taylorwilsdon/google_workspace_mcp.

#!/usr/bin/env python3
"""
Populate an existing Google Doc tab from a Markdown FILE, then read the tab back to check it.

Why this exists. The `manage_doc_tab populate_from_markdown` tool takes its Markdown inline,
so a large tab (tens of KB) has to pass through the Claude session's context twice, once
read and once re-emitted, and every retype risks a transcription error. `import_to_google_doc`
takes a file path but only ever creates a NEW Doc. This helper runs the scribe server's own
converter (`gdocs.docs_markdown_writer.markdown_to_docs_requests` from the installed
`workspace-mcp` package) on a file, and sends the same requests the tool sends, so the result
is identical to the tool and no text crosses the session's context.

Run it through the wrapper next to this file, which picks the exact workspace-mcp version the
plugin pins (the same interpreter the scribe MCP server runs in):

    scripts/doc-tab-populate --account you@example.com --doc <doc id> --list-tabs
    scripts/doc-tab-populate --account you@example.com --doc <doc id> --tab <tab id> --file notes.md
    scripts/doc-tab-populate --account you@example.com --doc <doc id> --tab <tab id> --file notes.md --write --check

Without the wrapper (Windows, or a custom setup) run it with the pinned interpreter directly -

    uvx --from workspace-mcp==<pinned version> python scripts/doc-tab-populate.py <arguments>

Modes. With no mode flag it is a dry run - it reads the Doc, confirms the tab exists and prints
what it would send. --write clears the tab and writes the file (the tool's replace_existing=true).
--append writes after the existing content (replace_existing=false). --check reads the tab back
and confirms every text block of the file is present, then reports structure warnings (flattened
tables, flattened nested lists). A write or append is always followed by the check. --list-tabs
prints each tab's id, title and shareable URL and nothing else.

The check is on TEXT, not layout. Exit codes - 0 text present, 1 text missing, 2 usage or
environment error, 3 text present but a structure warning was raised and --strict was given.

Credentials. The helper reads the account's stored OAuth credential through the server's own
credential store, from the directory the plugin manifest configures (WORKSPACE_MCP_CREDENTIALS_DIR),
and never prints it or writes it back. Environment variables already set in the shell win over
the manifest defaults. The account must already be authenticated (`/scribe:auth-add`).

Sandbox. The server's ALLOWED_FILE_DIRS sandbox is NOT applied by default, because this helper
runs through the shell, where Claude Code's own permission layer sees the full command and path.
--sandbox applies it exactly as `import_to_google_doc` does. Well-known secret locations (the
credentials directory, .env files, .ssh, .aws, .gnupg, .kube, gcloud config, credential file
names) are always refused. Decision recorded in docs/superpowers/plans/2026-10-01-tab-populate-helper-plan.md.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

HELPER_VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / ".claude-plugin" / "plugin.json"

EXIT_OK, EXIT_MISSING, EXIT_USAGE, EXIT_STRUCTURE = 0, 1, 2, 3
RETRYABLE = {429, 500, 502, 503, 504}

SECRET_DIRS = {".ssh", ".aws", ".gnupg", ".kube"}
SECRET_NAMES = {
    ".credentials", ".credentials.json", "credentials.json", "client_secret.json",
    "client_secrets.json", "oauth_client.json", "service_account.json", "service-account.json",
    ".npmrc", ".pypirc", ".netrc", ".git-credentials",
}


class HelperError(Exception):
    """A clear, user-facing failure. Carries the exit code."""

    def __init__(self, message: str, code: int = EXIT_USAGE):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- manifest and environment

def manifest_info(path: Path = MANIFEST) -> tuple[str | None, dict]:
    """Return (pinned workspace-mcp version, env block) from the plugin manifest."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, {}
    server = data.get("mcpServers", {}).get("scribe", {})
    pin = next((a.split("@", 1)[1] for a in server.get("args", [])
                if isinstance(a, str) and a.startswith("workspace-mcp@")), None)
    return pin, dict(server.get("env", {}))


def apply_env_defaults(env: dict, environ=None) -> dict:
    """Set each manifest env var that the caller has not already set. Returns what was applied."""
    environ = os.environ if environ is None else environ
    applied = {}
    for key, value in env.items():
        if key not in environ:
            environ[key] = os.path.expanduser(os.path.expandvars(value))
            applied[key] = environ[key]
    return applied


def credentials_dir(environ=None) -> Path:
    """Mirror of the server's get_default_credentials_dir, without importing its auth module."""
    environ = os.environ if environ is None else environ
    for key in ("WORKSPACE_MCP_CREDENTIALS_DIR", "GOOGLE_MCP_CREDENTIALS_DIR"):
        if environ.get(key):
            return Path(os.path.expanduser(environ[key]))
    return Path.home() / ".google_workspace_mcp" / "credentials"


# ---------------------------------------------------------------- server code, guarded

def load_server():
    """Import the pieces of workspace-mcp the helper needs, failing clearly when absent."""
    try:
        from gdocs import docs_markdown_writer
    except ImportError as exc:
        raise HelperError(
            "not running under the workspace-mcp interpreter (could not import "
            f"'{exc.name}'). Run scripts/doc-tab-populate, the wrapper next to this file, or "
            "`uvx --from workspace-mcp==<pinned version> python scripts/doc-tab-populate.py ...`."
        )
    fn = getattr(docs_markdown_writer, "markdown_to_docs_requests", None)
    params = set(inspect.signature(fn).parameters) if callable(fn) else set()
    if not {"tab_id", "start_index"} <= params:
        raise HelperError(
            f"workspace-mcp {installed_version()} does not provide "
            "gdocs.docs_markdown_writer.markdown_to_docs_requests(markdown_text, tab_id=, start_index=), "
            "which this helper depends on. The upstream API changed - re-test the helper against this "
            "version (see the pin-bump checklist in the plugin's CLAUDE.md) before using it."
        )
    return fn


def installed_version() -> str:
    try:
        return importlib.metadata.version("workspace-mcp")
    except importlib.metadata.PackageNotFoundError:
        return "(not installed)"


# ---------------------------------------------------------------- tabs and requests

def iter_tabs(tabs, depth: int = 0):
    """Yield (tab, depth) for every tab, walking child tabs."""
    for tab in tabs or []:
        yield tab, depth
        yield from iter_tabs(tab.get("childTabs"), depth + 1)


def find_tab(doc: dict, tab_id: str):
    return next((t for t, _ in iter_tabs(doc.get("tabs"))
                 if t.get("tabProperties", {}).get("tabId") == tab_id), None)


def tab_end_index(doc: dict, tab_id: str):
    """End index of a tab's body. Same contract as the server's private
    gdocs.docs_tools._find_tab_end_index, which the offline tests compare against."""
    tab = find_tab(doc, tab_id)
    if tab is None or "documentTab" not in tab:
        return None
    content = tab["documentTab"].get("body", {}).get("content", [])
    return content[-1].get("endIndex", 1) if content else 1


def build_requests(to_requests, markdown: str, tab_id: str, end: int, append: bool) -> list:
    """The exact request list manage_doc_tab populate_from_markdown sends (workspace-mcp 1.26.1)."""
    if append:
        insert_at = end - 1 if end > 2 else 1
        return to_requests(markdown, tab_id=tab_id, start_index=insert_at)
    requests = []
    if end > 2:
        requests.append({"deleteContentRange": {
            "range": {"startIndex": 1, "endIndex": end - 1, "tabId": tab_id}}})
    requests.extend(to_requests(markdown, tab_id=tab_id))
    return requests


def tab_url(doc_id: str, tab_id: str) -> str:
    return f"https://docs.google.com/document/d/{doc_id}/edit?tab={tab_id}"


# ---------------------------------------------------------------- reading the tab back

def walk_elements(elements, visit):
    """Call visit(paragraph) for every paragraph, descending into tables and tables of contents."""
    for el in elements or []:
        if "paragraph" in el:
            visit(el["paragraph"])
        elif "table" in el:
            visit({"__table__": True})
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    walk_elements(cell.get("content"), visit)
        elif "tableOfContents" in el:
            walk_elements(el["tableOfContents"].get("content"), visit)


def read_tab(doc: dict, tab_id: str) -> dict:
    """Plain text of the tab plus the structure counts the check reports."""
    tab = find_tab(doc, tab_id)
    body = (tab or {}).get("documentTab", {}).get("body", {}).get("content", [])
    paras, stats = [], {"tables": 0, "pipe_paragraphs": 0, "bullets": 0, "nested_bullets": 0}

    def visit(p):
        if p.get("__table__"):
            stats["tables"] += 1
            return
        text = "".join(e.get("textRun", {}).get("content", "") for e in p.get("elements", []))
        paras.append(text)
        stripped = text.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            stats["pipe_paragraphs"] += 1
        if "bullet" in p:
            stats["bullets"] += 1
            if p["bullet"].get("nestingLevel", 0) > 0:
                stats["nested_bullets"] += 1

    walk_elements(body, visit)
    return {"text": normalize("\n".join(paras)), "stats": stats}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- what the file should produce

HTML_COMMENT = re.compile(r"^\s*<!--.*?-->\s*$", re.S)


def inline_text(children) -> str:
    """Render inline tokens to plain text the way the server's writer does."""
    parts = []
    for tok in children or []:
        if tok.type in ("text", "code_inline", "html_inline"):
            parts.append(tok.content)
        elif tok.type == "softbreak":
            parts.append(" ")
        elif tok.type == "hardbreak":
            parts.append("\n")
        elif tok.type == "image":
            parts.append(tok.content or dict(tok.attrs or {}).get("src", ""))
    return "".join(parts)


def source_blocks(markdown: str) -> tuple[list, dict]:
    """Every text block the file should put in the tab, plus structure counts.

    Parses with markdown-it, the writer's own parser, with the table extension on so table
    cells are checked one by one (they are present whether a table renders natively or as
    flattened pipe text)."""
    from markdown_it import MarkdownIt

    tokens = MarkdownIt("commonmark").enable("table").parse(markdown)
    blocks, stats = [], {"tables": 0, "list_items": 0, "nested_items": 0}
    depth = 0
    for tok in tokens:
        if tok.type in ("bullet_list_open", "ordered_list_open"):
            depth += 1
        elif tok.type in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
        elif tok.type == "list_item_open":
            stats["list_items"] += 1
            stats["nested_items"] += depth > 1
        elif tok.type == "table_open":
            stats["tables"] += 1
        elif tok.type == "inline":
            blocks.extend(inline_text(tok.children).split("\n"))
        elif tok.type in ("fence", "code_block"):
            blocks.extend(tok.content.splitlines())
        elif tok.type == "html_block" and not HTML_COMMENT.match(tok.content):
            blocks.extend(tok.content.splitlines())
    return [b for b in (normalize(x) for x in blocks) if b], stats


def check(markdown: str, doc: dict, tab_id: str) -> dict:
    expected, src = source_blocks(markdown)
    got = read_tab(doc, tab_id)
    missing = [b for b in expected if b not in got["text"]]
    warnings = []
    tab = got["stats"]
    if src["tables"] and (tab["tables"] < src["tables"] or tab["pipe_paragraphs"]):
        warnings.append(
            f"tables flattened - source has {src['tables']}, tab has {tab['tables']} native and "
            f"{tab['pipe_paragraphs']} pipe-text paragraphs. Run the table repair pass in the docs skill Gotchas.")
    if src["nested_items"] and tab["nested_bullets"] < src["nested_items"]:
        warnings.append(
            f"nested lists flattened - source has {src['nested_items']} nested list items, tab has "
            f"{tab['nested_bullets']} nested bullets. The converter renders every list level flat.")
    return {"expected": len(expected), "missing": missing, "warnings": warnings,
            "source": src, "tab": tab}


# ---------------------------------------------------------------- file safety

def read_source(path: str, creds_dir: Path, sandbox: bool) -> tuple[Path, str]:
    p = Path(path).expanduser()
    if not p.is_file():
        raise HelperError(f"--file {path} is not a readable file")
    resolved = p.resolve()
    parts = [x.lower() for x in resolved.parts]
    home = Path.home().resolve()
    creds = creds_dir.expanduser().resolve()
    gcloud = home / ".config" / "gcloud"
    secret = (
        any(x == ".env" or x.startswith(".env.") for x in parts)
        or any(x in SECRET_DIRS for x in parts)
        or resolved.name.lower() in SECRET_NAMES
        or resolved.name.lower().startswith("client_secret")
        or resolved == creds or creds in resolved.parents
        or gcloud in resolved.parents
    )
    if secret:
        raise HelperError(f"refusing to read {resolved} - it is in a location that holds secrets")
    if sandbox:
        from core.utils import validate_file_path
        try:
            resolved = validate_file_path(str(resolved))
        except (ValueError, FileNotFoundError) as exc:
            raise HelperError(f"--sandbox - {exc}")
    try:
        return resolved, resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HelperError(f"--file {resolved} is not UTF-8 text")


# ---------------------------------------------------------------- Google API

def docs_service(account: str, creds_dir: Path):
    from auth.credential_store import get_credential_store
    from googleapiclient.discovery import build

    backend = os.environ.get("WORKSPACE_MCP_CREDENTIAL_STORE_BACKEND", "").strip().lower()
    if backend in ("", "local_directory") and not creds_dir.is_dir():
        raise HelperError(f"credentials directory {creds_dir} does not exist. Authenticate first "
                          "with /scribe:auth-init, or pass --credentials-dir.")
    creds = get_credential_store().get_credential(account)
    if creds is None:
        known = sorted(f.stem for f in creds_dir.glob("*@*.json")) if creds_dir.is_dir() else []
        raise HelperError(f"no stored credential for {account} in {creds_dir}. Authenticated "
                          f"accounts there - {', '.join(known) or 'none'}. Add it with /scribe:auth-add {account}.")
    return build("docs", "v1", credentials=creds, cache_discovery=False)


def execute(request, what: str, retry: bool):
    """Run a Google API request. Reads retry transient errors, writes never do."""
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError

    attempts = 3 if retry else 1
    for attempt in range(1, attempts + 1):
        try:
            return request.execute()
        except RefreshError:
            raise HelperError("the stored credential could not be refreshed (expired or revoked). "
                              "Re-authenticate this account with /scribe:auth-add, then re-run.")
        except HttpError as exc:
            status = getattr(exc.resp, "status", 0)
            if retry and status in RETRYABLE and attempt < attempts:
                time.sleep(2 ** attempt)
                continue
            detail = exc.reason if hasattr(exc, "reason") else str(exc)
            hint = (" The batch is atomic, so a 4xx applied nothing; after a 5xx run --check to see "
                    "whether it landed." if not retry else "")
            raise HelperError(f"{what} failed - HTTP {status} {detail}.{hint}")


def get_doc(svc, doc_id: str) -> dict:
    return execute(svc.documents().get(documentId=doc_id, includeTabsContent=True),
                   f"reading document {doc_id}", retry=True)


# ---------------------------------------------------------------- command line

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="doc-tab-populate",
        description="Populate an existing Google Doc tab from a Markdown file and check it by reading it back.",
        epilog="Dry run unless --write or --append. Full notes in the docstring of doc-tab-populate.py.")
    ap.add_argument("--account", help="Google account whose scribe credential to use")
    ap.add_argument("--doc", help="document id")
    ap.add_argument("--tab", help="tab id (see --list-tabs)")
    ap.add_argument("--file", help="Markdown file to write into the tab")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="clear the tab and write the file (replace_existing=true)")
    mode.add_argument("--append", action="store_true", help="write the file after the existing content (replace_existing=false)")
    mode.add_argument("--list-tabs", action="store_true", help="print tab ids, titles and URLs, nothing else")
    ap.add_argument("--check", action="store_true", help="read the tab back and confirm the file's text is there")
    ap.add_argument("--strict", action="store_true", help="exit 3 when the check raises a structure warning")
    ap.add_argument("--sandbox", action="store_true", help="only read --file from ALLOWED_FILE_DIRS, like import_to_google_doc")
    ap.add_argument("--credentials-dir", help="override WORKSPACE_MCP_CREDENTIALS_DIR")
    ap.add_argument("--version", action="store_true", help="print helper, installed and pinned versions")
    a = ap.parse_args(argv)
    if a.version:
        return a
    need = ["account", "doc"] + ([] if a.list_tabs else ["tab", "file"])
    missing = [f"--{n}" for n in need if not getattr(a, n)]
    if missing:
        ap.error(f"missing {', '.join(missing)}")
    return a


def run(argv=None) -> int:
    a = parse_args(argv)
    logging.disable(logging.INFO)  # the server modules log INFO lines on import
    pin, env = manifest_info()
    if a.credentials_dir:
        os.environ["WORKSPACE_MCP_CREDENTIALS_DIR"] = a.credentials_dir
    apply_env_defaults(env)
    if a.version:
        print(f"doc-tab-populate {HELPER_VERSION}, workspace-mcp installed {installed_version()}, "
              f"plugin pin {pin or '(manifest not found)'}")
        return EXIT_OK

    to_requests = load_server()
    installed = installed_version()
    if pin and installed != pin:
        print(f"WARNING - workspace-mcp {installed} is running this helper but the plugin pins {pin}. "
              "Use the wrapper so both match.", file=sys.stderr)

    creds_dir = credentials_dir()
    source = None
    if not a.list_tabs:
        path, source = read_source(a.file, creds_dir, a.sandbox)

    svc = docs_service(a.account, creds_dir)
    doc = get_doc(svc, a.doc)
    tabs = [(t["tabProperties"].get("tabId"), t["tabProperties"].get("title", ""), d)
            for t, d in iter_tabs(doc.get("tabs"))]

    if a.list_tabs:
        print(f"{doc.get('title', '')} ({a.doc}) - {len(tabs)} tab(s)")
        for tid, title, d in tabs:
            print(f"{'  ' * d}{tid}\t{title}\t{tab_url(a.doc, tid)}")
        return EXIT_OK

    end = tab_end_index(doc, a.tab)
    if end is None:
        listing = "; ".join(f"{tid} '{title}'" for tid, title, _ in tabs)
        raise HelperError(f"tab {a.tab} not found in {a.doc}. Tabs are - {listing}")
    title = next(t for tid, t, _ in tabs if tid == a.tab)
    requests = build_requests(to_requests, source, a.tab, end, a.append)
    action = "append after" if a.append else "replace"
    print(f"{doc.get('title', '')} - tab '{title}' ({a.tab}); {path.name} {len(source)} chars; "
          f"{len(requests)} requests; {action} {max(0, end - 2)} existing chars")

    if a.write or a.append:
        if not requests:
            print("NOTHING TO WRITE - the file produced no requests")
        else:
            execute(svc.documents().batchUpdate(documentId=a.doc, body={"requests": requests}),
                    "writing the tab", retry=False)
            print(f"WRITTEN - {tab_url(a.doc, a.tab)}")
    elif not a.check:
        print("DRY RUN - nothing written (--write to replace, --append to add, --check to read back)")
        return EXIT_OK

    result = check(source, get_doc(svc, a.doc), a.tab)
    status = "OK" if not result["missing"] else "MISSING TEXT"
    print(f"CHECK {status} - {result['expected']} text blocks, {len(result['missing'])} missing "
          "(the check is on text, not layout)")
    for m in result["missing"][:15]:
        print(f"   missing - {m[:140]}")
    if len(result["missing"]) > 15:
        print(f"   ... and {len(result['missing']) - 15} more")
    for w in result["warnings"]:
        print(f"WARN - {w}")
    if result["missing"]:
        return EXIT_MISSING
    if result["warnings"] and a.strict:
        return EXIT_STRUCTURE
    return EXIT_OK


def main():
    try:
        sys.exit(run())
    except HelperError as exc:
        print(f"ERROR - {exc}", file=sys.stderr)
        sys.exit(exc.code)


if __name__ == "__main__":
    main()

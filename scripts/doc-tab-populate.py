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
and confirms every text block of the file is present, in order, then reports structure warnings
(flattened tables, flattened nested lists, characters that shift the converter's offsets). A
write or append is always followed by the check, and after an append only the appended part of
the tab counts. --list-tabs prints each tab's id, title and shareable URL and nothing else.

Safety. A write is refused when the file has no text at all (a truncated export would otherwise
blank the tab) unless --allow-empty is given; when the file holds emoji or other characters
outside the Basic Multilingual Plane (the converter's offsets drift and every later paragraph
inherits the wrong style) unless --allow-astral is given; and when the running workspace-mcp is
not the version the plugin pins. When appending to a tab whose last paragraph has text, the
helper inserts a paragraph break first - the tool glues the first appended paragraph onto it. The write carries the Doc's revision id, so a Doc edited between the
read and the write fails loudly instead of being cleared at stale offsets.

The check is on TEXT, not layout. Exit codes -
    0  every text block is present
    1  text is missing (or the file had no text to check)
    2  usage, environment or API error; nothing was written
    3  text present, but a structure warning was raised and --strict was given
    4  a write was sent but its outcome is unknown, or it landed and the read-back failed;
       run --check before anything else, and never re-run an --append blindly

Credentials. The helper reads the account's stored OAuth credential through the server's own
credential store, from the directory the plugin manifest configures (WORKSPACE_MCP_CREDENTIALS_DIR),
and never prints it or writes it back. Environment variables already set in the shell win over
the manifest defaults. The account must already be authenticated (`/scribe:auth-add`).

Sandbox. The server's ALLOWED_FILE_DIRS sandbox is NOT applied by default, because this helper
runs through the shell, where Claude Code's own permission layer sees the full command and path.
--sandbox applies it exactly as `import_to_google_doc` does. Secret locations are always refused -
everything under ~/.workspace-mcp except attachments, both credential directory defaults, .env
files, .ssh, .aws, .gnupg, .kube, .docker, gcloud and gh config, private keys and credential
file names. Decision recorded in docs/superpowers/plans/2026-10-01-tab-populate-helper-plan.md.
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

HELPER_VERSION = "1.1.0"
HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / ".claude-plugin" / "plugin.json"

EXIT_OK, EXIT_MISSING, EXIT_USAGE, EXIT_STRUCTURE, EXIT_UNKNOWN_WRITE = 0, 1, 2, 3, 4
RETRYABLE = {429, 500, 502, 503, 504}

SECRET_DIRS = {".ssh", ".aws", ".gnupg", ".kube", ".docker"}
SECRET_NAMES = {
    ".credentials", ".credentials.json", "credentials.json", "client_secret.json",
    "client_secrets.json", "oauth_client.json", "service_account.json", "service-account.json",
    ".npmrc", ".pypirc", ".netrc", ".git-credentials", ".envrc",
}
SECRET_PREFIXES = ("client_secret", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519")
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", "token.json", "tokens.json")


class HelperError(Exception):
    """A clear, user-facing failure. Carries the exit code."""

    def __init__(self, message: str, code: int = EXIT_USAGE):
        super().__init__(message)
        self.code = code


# ---------------------------------------------------------------- manifest and environment

def manifest_info(path: Path = MANIFEST) -> tuple[str | None, dict]:
    """Return (pinned workspace-mcp version, env block) from the plugin manifest.
    Raises HelperError when the manifest exists but cannot be parsed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, {}
    except (OSError, ValueError) as exc:
        raise HelperError(f"cannot read the plugin manifest {path} - {exc}")
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


def append_index(end: int) -> int:
    return end - 1 if end > 2 else 1


def last_paragraph_has_text(doc: dict, tab_id: str) -> bool:
    tab = find_tab(doc, tab_id)
    content = (tab or {}).get("documentTab", {}).get("body", {}).get("content", [])
    last = content[-1] if content else {}
    text = "".join(e.get("textRun", {}).get("content", "")
                   for e in last.get("paragraph", {}).get("elements", []))
    return bool(text.strip())


def build_requests(to_requests, markdown: str, tab_id: str, end: int, append: bool,
                   break_first: bool = False) -> list:
    """The exact request list manage_doc_tab populate_from_markdown sends (workspace-mcp 1.26.1),
    with one deliberate difference - when appending to a tab whose last paragraph has text
    (break_first), the tool glues the first appended paragraph onto it (confirmed live
    2026-10-01), so the helper inserts a paragraph break first."""
    if append:
        at = append_index(end)
        if break_first:
            location = {"index": at, "tabId": tab_id}
            return ([{"insertText": {"location": location, "text": "\n"}}]
                    + to_requests(markdown, tab_id=tab_id, start_index=at + 1))
        return to_requests(markdown, tab_id=tab_id, start_index=at)
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
    """Call visit(paragraph, start_index) for every paragraph, descending into tables and
    tables of contents. A table is reported as visit({"__table__": True}, start_index)."""
    for el in elements or []:
        start = el.get("startIndex", 0)
        if "paragraph" in el:
            visit(el["paragraph"], start)
        elif "table" in el:
            visit({"__table__": True}, start)
            for row in el["table"].get("tableRows", []):
                for cell in row.get("tableCells", []):
                    walk_elements(cell.get("content"), visit)
        elif "tableOfContents" in el:
            walk_elements(el["tableOfContents"].get("content"), visit)


def read_tab(doc: dict, tab_id: str, from_index: int = 0) -> dict:
    """The tab's paragraphs (normalized, in document order) at or after from_index, plus the
    structure counts the check reports for that same part of the tab."""
    tab = find_tab(doc, tab_id)
    body = (tab or {}).get("documentTab", {}).get("body", {}).get("content", [])
    paras, stats = [], {"tables": 0, "pipe_paragraphs": 0, "bullets": 0, "nested_bullets": 0}

    def visit(p, start):
        if p.get("__table__"):
            if start >= from_index:
                stats["tables"] += 1
            return
        runs = [(e.get("startIndex", start), e.get("textRun", {}).get("content", ""))
                for e in p.get("elements", [])]
        text = "".join(c for _, c in runs)
        if start + len(text) <= from_index:
            return
        if start < from_index:
            # An append lands just before the tab's final newline, so its first paragraph can be
            # glued onto the old last paragraph. Keep only the part at or after the append point.
            text = "".join(c[max(0, from_index - i):] for i, c in runs if i + len(c) > from_index)
        paras.append(normalize(text))
        stripped = text.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            stats["pipe_paragraphs"] += 1
        if "bullet" in p:
            stats["bullets"] += 1
            if p["bullet"].get("nestingLevel", 0) > 0:
                stats["nested_bullets"] += 1

    walk_elements(body, visit)
    return {"paras": paras, "text": " ".join(x for x in paras if x), "stats": stats}


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
    """Every text block the file should put in the tab, in order, plus structure counts.

    Parses with markdown-it, the writer's own parser, with the table extension on so table
    cells are checked one by one (they are present whether a table renders natively or as
    flattened pipe text)."""
    from markdown_it import MarkdownIt

    tokens = MarkdownIt("commonmark").enable("table").parse(markdown)
    blocks = []
    stats = {"tables": 0, "list_items": 0, "nested_items": 0,
             "astral": sum(1 for ch in markdown if ord(ch) > 0xFFFF)}
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


def match_in_order(expected: list, paras: list) -> list:
    """Blocks that are not found in order. Each block must appear inside a paragraph at or after
    the point where the previous block matched, so a dropped block cannot be satisfied by the
    same text elsewhere earlier in the tab, and repeats must each be present."""
    missing, p, off = [], 0, 0
    for block in expected:
        q, o = p, off
        while q < len(paras):
            i = paras[q].find(block, o)
            if i >= 0:
                p, off = q, i + len(block)
                break
            q, o = q + 1, 0
        else:
            missing.append(block)
    return missing


def check(markdown: str, doc: dict, tab_id: str, from_index: int = 0) -> dict:
    expected, src = source_blocks(markdown)
    got = read_tab(doc, tab_id, from_index)
    missing = match_in_order(expected, got["paras"])
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
    if src["astral"]:
        warnings.append(astral_warning(src["astral"]))
    return {"expected": len(expected), "missing": missing, "warnings": warnings,
            "source": src, "tab": tab}


def astral_warning(n: int) -> str:
    return (f"{n} character(s) outside the Basic Multilingual Plane (emoji and similar). The converter "
            "counts them as one index where Google Docs counts two, so every insert after the first one "
            "lands a character early - later paragraphs inherit the previous paragraph's style (live on "
            "1.26.1, one emoji in a heading turned every later paragraph into a heading) and inline "
            "styles shift. Remove them from the source, or use import_to_google_doc for a new Doc.")


# ---------------------------------------------------------------- file safety

def _under(path: Path, base: Path) -> bool:
    """Case-insensitive containment, because macOS volumes usually are."""
    p, b = str(path).lower(), str(base).lower().rstrip("/")
    return p == b or p.startswith(b + "/")


def protected_dirs(creds_dir: Path) -> list:
    home = Path.home()
    return [creds_dir.expanduser(), home / ".google_workspace_mcp" / "credentials",
            home / ".config" / "gcloud", home / ".config" / "gh"]


def is_secret(path: Path, creds_dir: Path) -> bool:
    resolved = path.resolve()
    parts = [x.lower() for x in resolved.parts]
    name = resolved.name.lower()
    home = Path.home().resolve()
    scribe_home = home / ".workspace-mcp"
    if _under(resolved, scribe_home) and not _under(resolved, scribe_home / "attachments"):
        return True
    if any(_under(resolved, d.resolve()) for d in protected_dirs(creds_dir)):
        return True
    return (
        any(x == ".env" or x.startswith(".env.") for x in parts)
        or any(x in SECRET_DIRS for x in parts)
        or name in SECRET_NAMES
        or name.startswith(SECRET_PREFIXES)
        or name.endswith(SECRET_SUFFIXES)
    )


def read_source(path: str, creds_dir: Path, sandbox: bool) -> tuple[Path, str]:
    p = Path(path).expanduser()
    if not p.is_file():
        raise HelperError(f"--file {path} is not a readable file")
    resolved = p.resolve()
    if is_secret(resolved, creds_dir):
        raise HelperError(f"refusing to read {resolved} - it is in a location that holds secrets")
    if sandbox:
        from core.utils import validate_file_path
        try:
            resolved = validate_file_path(str(resolved))
        except (ValueError, FileNotFoundError) as exc:
            raise HelperError(f"--sandbox - {exc}")
    try:
        return resolved, resolved.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise HelperError(f"--file {resolved} is not UTF-8 text")
    except OSError as exc:
        raise HelperError(f"cannot read --file {resolved} - {exc.strerror or exc}")


# ---------------------------------------------------------------- Google API

def docs_service(account: str, creds_dir: Path):
    from auth.credential_store import get_credential_store
    from googleapiclient.discovery import build

    backend = os.environ.get("WORKSPACE_MCP_CREDENTIAL_STORE_BACKEND", "").strip().lower()
    local = backend in ("", "local_directory")
    if local and not creds_dir.is_dir():
        raise HelperError(f"credentials directory {creds_dir} does not exist. Authenticate first "
                          "with /scribe:auth-init, or pass --credentials-dir.")
    creds = get_credential_store().get_credential(account)
    if creds is None:
        if local and any(f.stem.lower() == account.lower() for f in creds_dir.glob("*.json")):
            raise HelperError(f"a credential file for {account} exists in {creds_dir} but could not be "
                              f"parsed. Re-authenticate with /scribe:auth-add {account}.")
        known = sorted(f.stem for f in creds_dir.glob("*@*.json")) if local else []
        raise HelperError(f"no stored credential for {account} in {creds_dir}. Authenticated "
                          f"accounts there - {', '.join(known) or 'none'}. Add it with /scribe:auth-add {account}.")
    return build("docs", "v1", credentials=creds, cache_discovery=False)


def _transport_errors() -> tuple:
    errors = [OSError]
    try:
        import httplib2
        errors.append(httplib2.HttpLib2Error)
    except ImportError:
        pass
    try:
        from google.auth.exceptions import TransportError
        errors.append(TransportError)
    except ImportError:
        pass
    return tuple(errors)


UNKNOWN_WRITE_HINT = ("The write may or may not have landed. Run --check against the same file "
                      "before anything else, and do NOT re-run an --append until the check says what is there.")


def execute(request, what: str, write: bool = False):
    """Run a Google API request. Reads retry transient failures, writes never do."""
    from googleapiclient.errors import HttpError
    from google.auth.exceptions import RefreshError

    attempts = 1 if write else 3
    for attempt in range(1, attempts + 1):
        try:
            return request.execute()
        except RefreshError:
            raise HelperError("the stored credential could not be refreshed (expired or revoked). "
                              "Re-authenticate this account with /scribe:auth-add, then re-run.")
        except HttpError as exc:
            status = getattr(exc.resp, "status", 0)
            detail = getattr(exc, "reason", "") or str(exc)
            if not write and status in RETRYABLE and attempt < attempts:
                time.sleep(2 ** attempt)
                continue
            if write and status >= 500:
                raise HelperError(f"{what} failed - HTTP {status} {detail}. {UNKNOWN_WRITE_HINT}",
                                  EXIT_UNKNOWN_WRITE)
            hint = (" The batch is atomic, so nothing was applied. If the Doc changed after it was "
                    "read, just re-run." if write else "")
            raise HelperError(f"{what} failed - HTTP {status} {detail}.{hint}")
        except _transport_errors() as exc:
            if not write and attempt < attempts:
                time.sleep(2 ** attempt)
                continue
            msg = f"{what} failed - network error {type(exc).__name__}: {exc}."
            if write:
                raise HelperError(f"{msg} {UNKNOWN_WRITE_HINT}", EXIT_UNKNOWN_WRITE)
            raise HelperError(msg)


def get_doc(svc, doc_id: str) -> dict:
    return execute(svc.documents().get(documentId=doc_id, includeTabsContent=True),
                   f"reading document {doc_id}")


# ---------------------------------------------------------------- command line

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="doc-tab-populate",
        description="Populate an existing Google Doc tab from a Markdown file and check it by reading it back.",
        epilog="Dry run unless --write or --append. Exit codes and full notes are in the docstring of "
               "doc-tab-populate.py - 0 ok, 1 text missing, 2 error, 3 strict warning, 4 write outcome unknown.")
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
    ap.add_argument("--allow-empty", action="store_true", help="allow --write with a file that has no text (clears the tab)")
    ap.add_argument("--allow-astral", action="store_true", help="allow a write whose file has emoji (styles will shift, see the docstring)")
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
    if pin is None:
        print(f"WARNING - no workspace-mcp pin found in {MANIFEST}; manifest env defaults not applied.",
              file=sys.stderr)
    if a.credentials_dir:
        os.environ["WORKSPACE_MCP_CREDENTIALS_DIR"] = a.credentials_dir
    apply_env_defaults(env)
    if a.version:
        print(f"doc-tab-populate {HELPER_VERSION}, workspace-mcp installed {installed_version()}, "
              f"plugin pin {pin or '(manifest not found)'}")
        return EXIT_OK

    to_requests = load_server()
    installed = installed_version()
    mismatch = bool(pin) and installed != pin
    if mismatch:
        if a.write or a.append:
            raise HelperError(f"workspace-mcp {installed} is running this helper but the plugin pins {pin}. "
                              "Writes are refused on a mismatch - use the wrapper, scripts/doc-tab-populate.")
        print(f"WARNING - workspace-mcp {installed} is running this helper but the plugin pins {pin}.",
              file=sys.stderr)

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
    blocks, src = source_blocks(source)
    break_first = a.append and last_paragraph_has_text(doc, a.tab)
    requests = build_requests(to_requests, source, a.tab, end, a.append, break_first)
    action = "append after" if a.append else "replace"
    print(f"{doc.get('title', '')} - tab '{title}' ({a.tab}); {path.name} {len(source)} chars, "
          f"{len(blocks)} text blocks; {len(requests)} requests; {action} {max(0, end - 2)} existing chars")
    if src["astral"]:
        print(f"WARN - {astral_warning(src['astral'])}")

    from_index = append_index(end) + break_first if a.append else 0
    if a.write or a.append:
        if src["astral"] and not a.allow_astral:
            raise HelperError(f"{path.name} contains {src['astral']} emoji or other character(s) outside the "
                              "Basic Multilingual Plane, which corrupt the tab's paragraph styles on this "
                              "workspace-mcp (see the WARN above). Remove them, or pass --allow-astral to "
                              "write anyway.")
        if not blocks and not a.allow_empty:
            raise HelperError(f"{path.name} has no text to write. Refusing to "
                              f"{'clear the tab' if a.write else 'append nothing'} - "
                              "pass --allow-empty if clearing the tab is really intended.")
        if not requests:
            print("NOTHING TO WRITE - the file produced no requests")
        else:
            body = {"requests": requests}
            if doc.get("revisionId"):
                body["writeControl"] = {"requiredRevisionId": doc["revisionId"]}
            execute(svc.documents().batchUpdate(documentId=a.doc, body=body),
                    "writing the tab", write=True)
            print(f"WRITTEN - {tab_url(a.doc, a.tab)}")
        try:
            after = get_doc(svc, a.doc)
        except HelperError as exc:
            raise HelperError(f"the write landed, but reading the tab back failed ({exc}). Run --check "
                              "before anything else, and do NOT re-run an --append.", EXIT_UNKNOWN_WRITE)
    elif not a.check:
        print("DRY RUN - nothing written (--write to replace, --append to add, --check to read back)")
        return EXIT_OK
    else:
        after = doc

    result = check(source, after, a.tab, from_index)
    if result["expected"] == 0:
        print("CHECK EMPTY - the file has no text blocks, so there is nothing to confirm")
        return EXIT_OK if a.allow_empty else EXIT_MISSING
    status = "OK" if not result["missing"] else "MISSING TEXT"
    scope = "the appended part of the tab" if a.append else "the tab"
    print(f"CHECK {status} - {result['expected']} text blocks, {len(result['missing'])} missing, "
          f"matched in order against {scope} (the check is on text, not layout)")
    for m in result["missing"][:15]:
        print(f"   missing - {m[:140]}")
    if len(result["missing"]) > 15:
        print(f"   ... and {len(result['missing']) - 15} more")
    for w in result["warnings"]:
        if not w.startswith(f"{src['astral']} character"):
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
    except KeyboardInterrupt:
        print("ERROR - interrupted. If a write was in progress, run --check before anything else.",
              file=sys.stderr)
        sys.exit(EXIT_UNKNOWN_WRITE)
    except Exception as exc:  # never a traceback, never exit 1 (which means text missing)
        print(f"ERROR - unexpected {type(exc).__name__}: {exc}. If a write was in progress, "
              "run --check before anything else.", file=sys.stderr)
        sys.exit(EXIT_USAGE)


if __name__ == "__main__":
    main()

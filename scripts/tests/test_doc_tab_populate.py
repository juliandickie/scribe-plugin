"""Offline tests for scripts/doc-tab-populate.py.

Run under the pinned workspace-mcp interpreter, which `make test` does -
    uvx --from workspace-mcp==<pin> python -m unittest discover -s scripts/tests -v

No network and no credentials. A small simulator applies the Docs API requests the helper
builds to an in-memory tab, so write-then-check runs end to end.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dtp", SCRIPTS / "doc-tab-populate.py")
dtp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dtp)

TO_REQUESTS = dtp.load_server()


# ---------------------------------------------------------------- Docs API simulator

class FakeTab:
    """A tab body as a list of [char, is_bullet, nesting] cells. Index 1 is the first char."""

    def __init__(self, text="\n"):
        self.cells = [[c, False, 0] for c in text]

    def apply(self, requests, tab_id):
        for req in requests:
            if "insertText" in req:
                loc = req["insertText"]["location"]
                assert loc.get("tabId") == tab_id, req
                i = loc["index"] - 1
                assert 0 <= i < len(self.cells), (i, len(self.cells))
                self.cells[i:i] = [[c, False, 0] for c in req["insertText"]["text"]]
            elif "deleteContentRange" in req:
                rng = req["deleteContentRange"]["range"]
                assert rng.get("tabId") == tab_id, req
                assert rng["endIndex"] <= len(self.cells), "must not delete the final newline"
                del self.cells[rng["startIndex"] - 1:rng["endIndex"] - 1]
            elif "createParagraphBullets" in req:
                rng = req["createParagraphBullets"]["range"]
                for cell in self.cells[rng["startIndex"] - 1:rng["endIndex"] - 1]:
                    cell[1] = True

    def paragraphs(self):
        out, start, cur = [], 1, []
        for idx, cell in enumerate(self.cells, start=1):
            cur.append(cell)
            if cell[0] == "\n":
                out.append((start, idx + 1, cur))
                start, cur = idx + 1, []
        return out

    def content(self):
        body = [{"startIndex": 0, "endIndex": 1, "sectionBreak": {}}]
        for start, end, cells in self.paragraphs():
            para = {"elements": [{"startIndex": start, "endIndex": end,
                                  "textRun": {"content": "".join(c[0] for c in cells)}}]}
            if cells[0][1]:
                para["bullet"] = {"listId": "l", "nestingLevel": cells[0][2]}
            body.append({"startIndex": start, "endIndex": end, "paragraph": para})
        return body


def fake_doc(tabs):
    """tabs - list of (tab_id, title, FakeTab or None for a tab without documentTab, children)."""
    def one(tid, title, tab, children=()):
        t = {"tabProperties": {"tabId": tid, "title": title}}
        if tab is not None:
            t["documentTab"] = {"body": {"content": tab.content()}}
        if children:
            t["childTabs"] = [one(*c) for c in children]
        return t
    return {"title": "Scratch", "tabs": [one(*t) for t in tabs]}


class FakeService:
    """Just enough of googleapiclient's docs service for run()."""

    def __init__(self, tabs):
        self.tabs = tabs  # tab_id -> FakeTab
        self.writes = []

    def documents(self):
        return self

    def get(self, documentId, includeTabsContent):
        return self._req(lambda: fake_doc([(tid, tid.upper(), t) for tid, t in self.tabs.items()]))

    def batchUpdate(self, documentId, body):
        def go():
            self.writes.append(body["requests"])
            for tid, tab in self.tabs.items():
                mine = [r for r in body["requests"] if tid in str(r)]
                tab.apply(mine, tid)
            return {}
        return self._req(go)

    @staticmethod
    def _req(fn):
        return type("R", (), {"execute": staticmethod(fn)})()


RICH = """# Heading one

Intro paragraph with **bold**, *italic*, `code` and a [link](https://example.com).
A soft break continues the paragraph &amp; an entity.

- first bullet
- second bullet

1. one
2. two

> A quoted line.

```
fenced line one
fenced line two
```

---

Closing paragraph.
"""


# ---------------------------------------------------------------- tests

class ManifestAndEnv(unittest.TestCase):
    def test_manifest_pin_and_env(self):
        pin, env = dtp.manifest_info()
        self.assertRegex(pin, r"^\d+\.\d+\.\d+$")
        self.assertEqual(pin, dtp.installed_version(), "run the tests under the pinned interpreter")
        for key in ("WORKSPACE_MCP_CREDENTIALS_DIR", "ALLOWED_FILE_DIRS", "GOOGLE_CLIENT_SECRET_PATH"):
            self.assertIn(key, env)

    def test_env_defaults_expand_and_never_override(self):
        environ = {"HOME": "/home/u", "ALLOWED_FILE_DIRS": "/mine"}
        with mock.patch.dict(os.environ, {"HOME": "/home/u"}):
            applied = dtp.apply_env_defaults(
                {"WORKSPACE_MCP_CREDENTIALS_DIR": "${HOME}/.workspace-mcp/credentials",
                 "ALLOWED_FILE_DIRS": "${HOME}/x"}, environ)
        self.assertEqual(environ["WORKSPACE_MCP_CREDENTIALS_DIR"], "/home/u/.workspace-mcp/credentials")
        self.assertEqual(environ["ALLOWED_FILE_DIRS"], "/mine")
        self.assertEqual(list(applied), ["WORKSPACE_MCP_CREDENTIALS_DIR"])

    def test_credentials_dir_precedence(self):
        self.assertEqual(dtp.credentials_dir({"WORKSPACE_MCP_CREDENTIALS_DIR": "/a", "GOOGLE_MCP_CREDENTIALS_DIR": "/b"}), Path("/a"))
        self.assertEqual(dtp.credentials_dir({"GOOGLE_MCP_CREDENTIALS_DIR": "/b"}), Path("/b"))


class ServerGuard(unittest.TestCase):
    def test_markdown_to_docs_requests_signature(self):
        self.assertTrue(callable(TO_REQUESTS))

    def test_guard_fails_clearly_when_function_missing(self):
        import gdocs.docs_markdown_writer as w
        with mock.patch.object(w, "markdown_to_docs_requests", None):
            with self.assertRaises(dtp.HelperError) as cm:
                dtp.load_server()
        self.assertIn("pin-bump checklist", str(cm.exception))

    def test_tab_end_index_matches_server(self):
        try:
            from gdocs.docs_tools import _find_tab_end_index
        except ImportError:
            self.skipTest("server no longer has _find_tab_end_index, the helper's own copy is authoritative")
        doc = fake_doc([
            ("t.0", "One", FakeTab("hello\nworld\n"), [("t.c", "Child", FakeTab("child text\n"))]),
            ("t.1", "Empty", FakeTab()),
            ("t.2", "No body", None),
        ])
        doc["tabs"].append({"tabProperties": {"tabId": "t.3"}, "documentTab": {"body": {"content": []}}})
        for tid in ("t.0", "t.c", "t.1", "t.2", "t.3", "missing"):
            self.assertEqual(dtp.tab_end_index(doc, tid), _find_tab_end_index(doc, tid), tid)


class Requests(unittest.TestCase):
    def test_replace_clears_then_writes(self):
        reqs = dtp.build_requests(TO_REQUESTS, "# Hi\n", "t.0", end=40, append=False)
        self.assertEqual(reqs[0], {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 39, "tabId": "t.0"}}})
        self.assertEqual(reqs[1:], TO_REQUESTS("# Hi\n", tab_id="t.0"))

    def test_replace_on_empty_tab_does_not_delete(self):
        reqs = dtp.build_requests(TO_REQUESTS, "text\n", "t.0", end=2, append=False)
        self.assertEqual(reqs, TO_REQUESTS("text\n", tab_id="t.0"))

    def test_append_starts_before_final_newline(self):
        reqs = dtp.build_requests(TO_REQUESTS, "more\n", "t.0", end=40, append=True)
        self.assertEqual(reqs, TO_REQUESTS("more\n", tab_id="t.0", start_index=39))
        self.assertEqual(dtp.build_requests(TO_REQUESTS, "more\n", "t.0", end=2, append=True),
                         TO_REQUESTS("more\n", tab_id="t.0", start_index=1))

    def test_every_request_targets_the_tab(self):
        for r in dtp.build_requests(TO_REQUESTS, RICH, "t.9", end=50, append=False):
            self.assertIn("'tabId': 't.9'", str(r))

    def test_tab_url(self):
        self.assertEqual(dtp.tab_url("D", "t.x"), "https://docs.google.com/document/d/D/edit?tab=t.x")


class Check(unittest.TestCase):
    def write(self, md, existing="old content\nmore old\n", append=False):
        tab = FakeTab(existing)
        end = dtp.tab_end_index(fake_doc([("t.0", "T", tab)]), "t.0")
        tab.apply(dtp.build_requests(TO_REQUESTS, md, "t.0", end, append), "t.0")
        return fake_doc([("t.0", "T", tab)])

    def test_rich_markdown_round_trips(self):
        result = dtp.check(RICH, self.write(RICH), "t.0")
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["expected"], 10)

    def test_replace_removes_old_text_and_append_keeps_it(self):
        doc = self.write("new\n")
        self.assertNotIn("old content", dtp.read_tab(doc, "t.0")["text"])
        doc = self.write("new\n", append=True)
        text = dtp.read_tab(doc, "t.0")["text"]
        self.assertIn("old content", text)
        self.assertLess(text.index("old content"), text.index("new"))

    def test_missing_text_is_reported(self):
        doc = self.write("# Title\n\nOnly this.\n")
        result = dtp.check("# Title\n\nOnly this.\n\nAnd this line that was never written.\n", doc, "t.0")
        self.assertEqual(result["missing"], ["And this line that was never written."])

    def test_tables_flatten_warning(self):
        md = "Intro.\n\n| A | B |\n| --- | --- |\n| 1 | 2 |\n"
        result = dtp.check(md, self.write(md), "t.0")
        self.assertEqual(result["missing"], [])
        if dtp.read_tab(self.write(md), "t.0")["stats"]["pipe_paragraphs"]:
            self.assertTrue(any("tables flattened" in w for w in result["warnings"]))

    def test_native_table_text_is_read(self):
        doc = fake_doc([("t.0", "T", FakeTab("before\n"))])
        doc["tabs"][0]["documentTab"]["body"]["content"].append({"table": {"tableRows": [
            {"tableCells": [{"content": [{"paragraph": {"elements": [{"textRun": {"content": "cell A\n"}}]}}]},
                            {"content": [{"paragraph": {"elements": [{"textRun": {"content": "cell B\n"}}]}}]}]}]}})
        got = dtp.read_tab(doc, "t.0")
        self.assertIn("cell A", got["text"])
        self.assertEqual(got["stats"]["tables"], 1)
        result = dtp.check("| H1 | H2 |\n| --- | --- |\n| cell A | cell B |\n", doc, "t.0")
        self.assertEqual(result["missing"], ["H1", "H2"])  # header cells absent from this fake tab

    def test_nested_list_warning(self):
        md = "- top\n  - nested one\n  - nested two\n- top two\n"
        blocks, stats = dtp.source_blocks(md)
        self.assertEqual(stats["nested_items"], 2)
        result = dtp.check(md, self.write(md), "t.0")
        self.assertEqual(result["missing"], [])
        self.assertTrue(any("nested lists flattened" in w for w in result["warnings"]))

    def test_check_reports_exactly_what_the_converter_drops(self):
        # On workspace-mcp 1.26.1 the converter silently drops all three of these. The assertion
        # is written so it stays true after an upstream fix - the check must flag a probe
        # exactly when the probe is absent from the written tab.
        md = ("Para.\n\n    indented code line\n\n<div>raw html block</div>\n\n"
              "- item first paragraph\n\n  item second paragraph\n\nEnd.\n")
        doc = self.write(md)
        text = dtp.read_tab(doc, "t.0")["text"]
        missing = dtp.check(md, doc, "t.0")["missing"]
        for probe in ("indented code line", "<div>raw html block</div>", "item second paragraph"):
            self.assertEqual(probe in missing, probe not in text, probe)

    def test_html_comments_are_not_expected(self):
        blocks, _ = dtp.source_blocks("<!-- note to self -->\n\nVisible.\n")
        self.assertEqual(blocks, ["Visible."])

    def test_entities_and_inline_markup(self):
        blocks, _ = dtp.source_blocks("A &amp; B with **bold** and [text](https://x.y)\n")
        self.assertEqual(blocks, ["A & B with bold and text"])


class FileSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.creds = self.tmp / "creds"
        self.creds.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def make(self, rel, text="# ok\n"):
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_reads_a_normal_file(self):
        p = self.make("notes.md")
        self.assertEqual(dtp.read_source(str(p), self.creds, sandbox=False)[1], "# ok\n")

    def test_refuses_secret_locations(self):
        for rel in (".env", "app/.env.local", ".ssh/id.md", ".aws/x.md", "credentials.json",
                    "client_secret_123.json", "oauth_client.json"):
            with self.subTest(rel=rel), self.assertRaises(dtp.HelperError):
                dtp.read_source(str(self.make(rel)), self.creds, sandbox=False)
        (self.creds / "me@example.com.json").write_text("{}")
        with self.assertRaises(dtp.HelperError):
            dtp.read_source(str(self.creds / "me@example.com.json"), self.creds, sandbox=False)

    def test_refuses_a_symlink_into_secrets(self):
        target = self.make(".ssh/key.md")
        link = self.tmp / "innocent.md"
        link.symlink_to(target)
        with self.assertRaises(dtp.HelperError):
            dtp.read_source(str(link), self.creds, sandbox=False)

    def test_sandbox_is_opt_in_and_matches_the_server(self):
        allowed = self.tmp / "allowed"
        inside = self.make("allowed/in.md")
        outside = self.make("elsewhere/out.md")
        with mock.patch.dict(os.environ, {"ALLOWED_FILE_DIRS": str(allowed)}):
            self.assertEqual(dtp.read_source(str(inside), self.creds, sandbox=True)[0], inside)
            with self.assertRaises(dtp.HelperError) as cm:
                dtp.read_source(str(outside), self.creds, sandbox=True)
            self.assertIn("--sandbox", str(cm.exception))
            self.assertEqual(dtp.read_source(str(outside), self.creds, sandbox=False)[0], outside)

    def test_rejects_non_utf8(self):
        p = self.tmp / "bin.md"
        p.write_bytes(b"\xff\xfe\x00bad")
        with self.assertRaises(dtp.HelperError):
            dtp.read_source(str(p), self.creds, sandbox=False)


class EndToEnd(unittest.TestCase):
    """run() against the simulator, with the credential and network layer replaced."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.md = self.tmp / "page.md"
        self.md.write_text(RICH, encoding="utf-8")
        self.svc = FakeService({"t.0": FakeTab("stale\n"), "t.1": FakeTab("other tab\n")})
        patcher = mock.patch.object(dtp, "docs_service", return_value=self.svc)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp)

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = dtp.run(["--account", "me@example.com", "--doc", "D", *args])
        return code, out.getvalue()

    def test_dry_run_writes_nothing(self):
        code, out = self.run_cli("--tab", "t.0", "--file", str(self.md))
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertEqual(self.svc.writes, [])

    def test_write_then_check(self):
        code, out = self.run_cli("--tab", "t.0", "--file", str(self.md), "--write", "--check")
        self.assertEqual(code, 0, out)
        self.assertIn("WRITTEN - https://docs.google.com/document/d/D/edit?tab=t.0", out)
        self.assertIn("CHECK OK", out)
        self.assertEqual(len(self.svc.writes), 1)
        self.assertIn("other tab", "".join(c[0] for c in self.svc.tabs["t.1"].cells), "other tab untouched")

    def test_check_alone_fails_before_write(self):
        code, out = self.run_cli("--tab", "t.0", "--file", str(self.md), "--check")
        self.assertEqual(code, 1)
        self.assertIn("MISSING TEXT", out)

    def test_strict_turns_structure_warning_into_exit_3(self):
        self.md.write_text("- a\n  - b\n", encoding="utf-8")
        code, out = self.run_cli("--tab", "t.0", "--file", str(self.md), "--write", "--strict")
        self.assertEqual(code, 3, out)
        self.assertIn("WARN - nested lists flattened", out)

    def test_unknown_tab_lists_the_real_ones(self):
        with self.assertRaises(dtp.HelperError) as cm:
            self.run_cli("--tab", "t.nope", "--file", str(self.md))
        self.assertIn("t.0 'T.0'", str(cm.exception))

    def test_list_tabs(self):
        code, out = self.run_cli("--list-tabs")
        self.assertEqual(code, 0)
        self.assertIn("t.1\tT.1\thttps://docs.google.com/document/d/D/edit?tab=t.1", out)


@unittest.skipUnless(shutil.which("uvx"), "uvx not installed")
class Wrapper(unittest.TestCase):
    def test_wrapper_uses_the_pinned_version(self):
        out = subprocess.run([str(SCRIPTS / "doc-tab-populate"), "--version"],
                             capture_output=True, text=True, timeout=300)
        self.assertEqual(out.returncode, 0, out.stderr)
        pin, _ = dtp.manifest_info()
        self.assertIn(f"installed {pin}, plugin pin {pin}", out.stdout)


if __name__ == "__main__":
    unittest.main()

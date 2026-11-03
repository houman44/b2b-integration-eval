"""Agentic workspace and loop, with a scripted fake model (no network)."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import run_agentic
from agentic.env import Workspace, build_env, manifest
from harness import openrouter as orc

ROOT = Path(__file__).resolve().parent.parent
FAKE_KEY = "sk-or-v1-FAKE-AGENTIC-KEY-0123456789"


class Env(unittest.TestCase):
    def test_deterministic(self):
        for t in ("T1", "U2"):
            self.assertEqual(manifest(build_env(t)[0]), manifest(build_env(t)[0]))

    def test_ticket_documents_are_in_the_workspace(self):
        files, b = build_env("U2")
        self.assertTrue(any(p.startswith("archive/") for p in files))
        self.assertIn(b.documents["interchange.edi"], files.values())
        self.assertTrue(any(p.startswith("gateway/gw1/trace-") for p in files))
        files, b = build_env("R2")
        wire = [p for p, t in files.items() if t == b.documents["interchange.edi"]]
        self.assertTrue(wire and wire[0].startswith("outbound-wire/"))

    def test_tools(self):
        w = Workspace({"a/b.txt": "one\ntwo\nthree", "c.txt": "x"})
        self.assertIn("a/", w.list_dir("/"))
        self.assertIn("2: two", w.read_file("/a/b.txt", 2, 1))
        self.assertIn("/a/b.txt:3: three", w.search("THREE"))
        self.assertIn("no such file", w.read_file("nope"))


def scripted(key, body, timeout=900):
    """Turn 1: list root; turn 2: answer with the reference."""
    n_tools = sum(1 for m in body["messages"] if m["role"] == "tool")
    tid = body["messages"][0]["content"].split()[2]
    ref = json.loads((ROOT / "reference" / f"{tid}.json").read_text())["answer"]
    if isinstance(ref.get("next_check"), list):
        ref = {**ref, "next_check": ref["next_check"][0]}
    if n_tools == 0:
        msg = {"content": "", "tool_calls": [{"id": "c1", "type": "function", "function": {
            "name": "list_dir", "arguments": json.dumps({"path": "/"})}}]}
    else:
        msg = {"content": f"Done ({key}).\n```json\n{json.dumps(ref)}\n```"}
    return 200, {"choices": [{"message": msg}], "usage": {"cost": 0.001}}, 0.01


class Loop(unittest.TestCase):
    def test_scripted_agent_passes_and_key_is_redacted(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(orc, "load_key", return_value=FAKE_KEY), \
                mock.patch.object(orc, "chat_raw", side_effect=scripted), \
                redirect_stdout(io.StringIO()):
            run_agentic.main(["--models", "test/model", "--tickets", "T1,U2", "--confirm-spend",
                              "--allow-draft", "--results-dir", d, "--parallel", "1"])
            run = next(Path(d).iterdir())
            s = json.loads((run / "summary.json").read_text())["summary"]["test/model"]
            self.assertEqual(s["pass_rate"], 1.0)
            for f in (run / "raw").glob("*.json"):
                text = f.read_text()
                self.assertNotIn(FAKE_KEY, text)
                self.assertEqual(json.loads(text)["tool_calls"], 1)


if __name__ == "__main__":
    unittest.main()

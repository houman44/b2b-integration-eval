"""Harness checks with a fake OpenRouter (no network, no spend)."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import run_eval
from harness import openrouter as orc

ROOT = Path(__file__).resolve().parent.parent
FAKE_KEY = "sk-or-v1-FAKE-KEY-FOR-TESTS-0123456789"
CATALOGUE = {"test/model": {"pricing": {"prompt": "0.000001", "completion": "0.000002"}}}


def fake_chat(key, model, prompt, *, temperature, max_tokens, seed=None, **kw):
    tid = prompt.split("\n", 1)[0].split()[-1]
    ref = json.loads((ROOT / "reference" / f"{tid}.json").read_text())["answer"]
    if isinstance(ref.get("next_check"), list):
        ref = {**ref, "next_check": ref["next_check"][0]}
    answer = ref if seed == 1 else {**ref, "owner": "receiver" if ref["owner"] != "receiver" else "sender"}
    text = f"Diagnosis (echoing {key}).\n```json\n{json.dumps(answer)}\n```"
    body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    payload = {"id": "gen-1", "model": model, "provider": "Fake",
               "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
               "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001}}
    return body, 200, payload, [{"status": 200, "latency_s": 0.01}]


class HarnessWithFakeAPI(unittest.TestCase):
    def run_fake(self, *extra):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(orc, "list_models", return_value=CATALOGUE), \
                mock.patch.object(orc, "load_key", return_value=FAKE_KEY), \
                mock.patch.object(orc, "chat", side_effect=fake_chat), \
                redirect_stdout(io.StringIO()):
            run_dir = run_eval.main(["--models", "test/model", "--trials", "2",
                                     "--confirm-spend", "--allow-draft", "--parallel", "1",
                                     "--results-dir", d, *extra])
            files = {p.name: p.read_text() for p in Path(run_dir).rglob("*") if p.is_file()}
            return run_dir, files

    def test_grades_logs_and_summarises(self):
        run_dir, files = self.run_fake()
        self.assertTrue(run_dir.name.startswith("draft-"))
        raws = [k for k in files if k.endswith(".json") and "__t" in k]
        self.assertEqual(len(raws), 2 * len(run_eval.ALL_TICKETS))   # tickets x 2 trials
        s = json.loads(files["summary.json"])["summary"]["test/model"]
        self.assertEqual(s["pass_rate"], 0.5)              # trial 1 right, trial 2 wrong owner
        self.assertEqual(s["pass_at_k"], 1.0)
        self.assertEqual(s["pass_hat_k"], 0.0)
        self.assertEqual(s["field_accuracy"]["owner"], 0.5)
        self.assertAlmostEqual(s["cost_usd"], 0.002 * len(run_eval.ALL_TICKETS))

    def test_key_never_written(self):
        _, files = self.run_fake()
        for name, text in files.items():
            self.assertNotIn(FAKE_KEY, text, name)
        self.assertTrue(any("[REDACTED]" in t for t in files.values()))

    def test_refuses_without_confirm_or_draft_flag(self):
        with mock.patch.object(orc, "list_models", return_value=CATALOGUE), \
                redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                run_eval.main(["--models", "test/model", "--allow-draft"])
            with self.assertRaises(SystemExit):
                run_eval.main(["--models", "test/model", "--confirm-spend"])

    def test_cost_cap(self):
        with mock.patch.object(orc, "list_models", return_value={"test/model": {"pricing": {
                "prompt": "0.01", "completion": "0.01"}}}), redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                run_eval.main(["--models", "test/model", "--confirm-spend", "--allow-draft",
                               "--max-cost", "0.5"])


if __name__ == "__main__":
    unittest.main()

"""Translation tasks: deterministic, reference passes, near-misses score below 1."""
import json
import unittest
from pathlib import Path

from translation.build import build_all
from translation.edifact import esc, split_elements, split_segments
from translation.grade import grade_translation

ROOT = Path(__file__).resolve().parent.parent


def ref(t):
    return json.loads((ROOT / "reference-translation" / f"{t}.json").read_text(encoding="utf-8"))


def ed(segs):
    return "Here it is.\n```edifact\n" + "'\n".join(segs) + "'\n```\n"


class Translation(unittest.TestCase):
    def test_reproducible_and_committed(self):
        a, b = build_all(), build_all()
        self.assertEqual(a, b)
        for p, t in a.items():
            self.assertEqual((ROOT / p).read_text(encoding="utf-8"), t, p)

    def test_reference_passes(self):
        r = ref("X2")
        self.assertTrue(grade_translation(ed(r["expected"]), r)["pass"])
        one_line = "```edifact\n" + "".join(s + "'" for s in r["expected"]) + "\n```"
        self.assertTrue(grade_translation(one_line, r)["pass"])
        r = ref("X1")
        self.assertTrue(grade_translation("```json\n" + json.dumps(r["expected"]) + "\n```", r)["pass"])
        # key order and int/float spelling do not matter
        e = json.loads(json.dumps(r["expected"]), parse_int=float)
        self.assertTrue(grade_translation("```json\n" + json.dumps(e, sort_keys=True) + "\n```", r)["pass"])

    def test_near_misses_fail(self):
        r = ref("X2")
        e = list(r["expected"])
        for bad in ([s.replace("?:", ":") for s in e],                       # escaping lost
                    [s.replace("MOA+203:5.63", "MOA+203:5.62") for s in e],   # banker's rounding
                    e[:-2] + ["UNT+29+1", e[-1]],                             # wrong count
                    e + ["UNS+S"]):                                           # extra segment
            g = grade_translation(ed(bad), r)
            self.assertFalse(g["pass"])
            self.assertLess(g["score"], 1.0)
        r = ref("X1")
        x = json.loads(json.dumps(r["expected"]))
        x["pallets"][1]["cartons"].reverse()                                  # wrong order
        self.assertFalse(grade_translation("```json\n" + json.dumps(x) + "\n```", r)["pass"])
        x = json.loads(json.dumps(r["expected"]))
        x["totals"][0]["quantity"] += 1
        g = grade_translation("```json\n" + json.dumps(x) + "\n```", r)
        self.assertFalse(g["pass"])
        self.assertGreater(g["score"], 0.9)

    def test_edifact_helpers(self):
        self.assertEqual(esc("A+B:C?D'E"), "A?+B?:C??D?'E")
        self.assertEqual(split_segments("A+B?'C'D+E'"), ["A+B?'C", "D+E"])
        self.assertEqual(split_elements("NAD+BY+++O?'NEIL?+SON"), [["NAD"], ["BY"], [""], [""], ["O'NEIL+SON"]])

    def test_x2_arithmetic(self):
        e = ref("X2")["expected"]
        unt = next(s for s in e if s.startswith("UNT+"))
        self.assertEqual(int(unt.split("+")[1]), len(e) - 2)


if __name__ == "__main__":
    unittest.main()

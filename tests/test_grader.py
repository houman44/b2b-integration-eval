"""Grader validation: run before any model run (brief, weekend 1 step 3).

* every reference answer scores 100%, also when reformatted the way a model
  might write it (no false fails);
* deliberately wrong answers score 0%, including an answer that lists every
  option (no false passes);
* answers wrong in one field get 3/4 and do not pass.
"""
import json
import unittest
from pathlib import Path

from graders.grade import extract_answer, grade, norm_location_token
from graders.schema import CAUSES, CHECKS, LAYERS, OWNERS, all_locations

ROOT = Path(__file__).resolve().parent.parent
TICKETS = ["T1", "T2", "E1", "E3", "R1", "R2", "S1", "U1", "U2", "U5"]


def ref(tid):
    return json.loads((ROOT / "reference" / f"{tid}.json").read_text())


def single(answer):
    """A reference answer as a model would give it (one value for every enum key that
    lists several accepted values, e.g. next_check, or R2's layer)."""
    a = dict(answer)
    for k in ("cause", "layer", "owner", "next_check"):
        if isinstance(a.get(k), list):
            a[k] = a[k][0]
    return a


def reply(answer, prose="I compared the documents.\n\n"):
    return prose + "```json\n" + json.dumps(single(answer)) + "\n```\n"


def other(values, exclude):
    excluded = set(exclude) if isinstance(exclude, list) else {exclude}
    return sorted(v for v in values if v not in excluded)[0]


# Plausible wrong answers per ticket: the mistakes a model is likely to make.
PLAUSIBLE_WRONG = {
    "U1": [
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"], "next_check": "none"},
        {"cause": "duplicate_virtual_file", "layer": "transport", "owner": "sender",
         "location": ["SFID.SFIDTIME"], "next_check": "none"},
        {"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
         "location": ["UNDETERMINED"], "next_check": "resend_with_new_identity"},
    ],
    "U2": [
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"], "next_check": "none"},
        {"cause": "certificate_problem", "layer": "transport", "owner": "sender",
         "location": ["NONE"], "next_check": "none"},
        {"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
         "location": ["UNDETERMINED"], "next_check": "resend_unchanged"},
    ],
    "E3": [
        {"cause": "syntax_identifier_not_agreed", "layer": "envelope", "owner": "receiver",
         "location": ["UNB.S001.0001"]},
        {"cause": "syntax_identifier_not_agreed", "layer": "envelope", "owner": "agreement",
         "location": ["UNB.S001.0001"]},
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"]},
        {"cause": "syntax_identifier_not_agreed", "layer": "envelope", "owner": "sender",
         "location": ["UNB.S001.0001", "UNB.S001.0002"]},
    ],
    "T2": [
        {"cause": "restart_position_invalid", "layer": "transport", "owner": "receiver",
         "location": ["SFPA.SFPAACNT"]},
        {"cause": "restart_position_invalid", "layer": "transport", "owner": "sender",
         "location": ["SFID.SFIDREST", "EFID.EFIDUCNT"]},
        {"cause": "file_too_large", "layer": "transport", "owner": "receiver",
         "location": ["SFID.SFIDFSIZ"]},
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"]},
    ],
    "T1": [
        {"cause": "intermediary_fault", "layer": "transport", "owner": "intermediary",
         "location": ["NERP.NERPCREA"]},
        {"cause": "duplicate_virtual_file", "layer": "transport", "owner": "receiver",
         "location": ["SFID.SFIDDATE", "SFID.SFIDTIME"]},
        {"cause": "duplicate_virtual_file", "layer": "transport", "owner": "sender",
         "location": ["SFID.SFIDDSN", "SFID.SFIDDATE", "SFID.SFIDTIME"]},
        {"cause": "duplicate_virtual_file", "layer": "transport", "owner": "sender",
         "location": ["SFID.SFIDTIME"]},
        {"cause": "duplicate_virtual_file", "layer": "transport", "owner": "sender",
         "location": ["NERP.NERPDATE", "NERP.NERPTIME"]},
        {"cause": "duplicate_interchange", "layer": "envelope", "owner": "sender",
         "location": ["UNB.0020"]},
    ],
    "E1": [
        {"cause": "interchange_control_count_mismatch", "layer": "envelope",
         "owner": "sender", "location": ["UNZ.0036"]},
        {"cause": "interchange_control_count_mismatch", "layer": "envelope",
         "owner": "sender", "location": ["UNZ.0036", "UNZ.0020", "UNB.0020"]},
        {"cause": "interchange_control_reference_mismatch", "layer": "envelope",
         "owner": "receiver", "location": ["UNB.0020", "UNZ.0020"]},
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"]},
        {"cause": "interchange_control_reference_mismatch", "layer": "envelope",
         "owner": "sender", "location": ["UNZ.0020"]},
    ],
    "R1": [
        {"cause": "certificate_problem", "layer": "transport", "owner": "sender",
         "location": ["NONE"]},
        {"cause": "session_parameters_not_negotiated", "layer": "transport", "owner": "sender",
         "location": ["SSID.SSIDSDEB", "SSID.SSIDCRED"]},
        {"cause": "test_indicator_mismatch", "layer": "envelope", "owner": "sender",
         "location": ["UNB.0031"]},
        {"cause": "test_indicator_mismatch", "layer": "envelope", "owner": "receiver",
         "location": ["UNB.0035"]},
        {"cause": "no_sender_side_fault", "layer": "none", "owner": "receiver",
         "location": ["NONE"]},
    ],
}


class ReferenceAnswersPass(unittest.TestCase):
    def test_reference_scores_100(self):
        for tid in TICKETS:
            r = ref(tid)
            g = grade(reply(r["answer"]), r)
            self.assertTrue(g["pass"], (tid, g))
            self.assertEqual(g["score"], 1.0)

    def test_reformatted_reference_still_passes(self):
        """Case, spacing, separators, order, bare OFTP2 field names,
        component-only EDIFACT names and value formatting must not cause a
        false fail."""
        for tid in TICKETS:
            r = ref(tid)
            a = single(r["answer"])
            kind = r["value_kind"]
            v = a["value"]
            if kind == "int":
                v_alt = f"{int(v):,}" if int(v) > 999 else "00" + v
            elif kind == "string":
                v_alt = "  " + v.lower() + " "
            else:
                v_alt = " " + v.rstrip("'") + " "
            variants = [
                {"cause": a["cause"].upper().replace("_", " "), "layer": a["layer"].title(),
                 "owner": " " + a["owner"].upper() + " ",
                 "location": [x.lower().replace(".", " ") for x in reversed(a["location"])],
                 "next_check": " " + single(a)["next_check"].upper(),
                 "value": v_alt},
                {**a, "location": [x.split(".")[-1] if x.startswith("SFID.") else
                                   x.replace(".", "/") for x in a["location"]]},
                {**a, "location": [x.replace("S002.", "").replace("S003.", "").replace("S004.", "")
                                   for x in a["location"]]},
            ]
            if kind == "int":
                variants.append({**a, "value": int(v)})
            for var in variants:
                for text in (reply(var), json.dumps(var), "Answer: " + json.dumps(var) + " (final)"):
                    g = grade(text, r)
                    self.assertTrue(g["pass"], (tid, var, g))

    def test_last_json_block_is_graded(self):
        r = ref("T1")
        wrong = {**r["answer"], "owner": "receiver"}
        self.assertTrue(grade(reply(wrong) + reply(r["answer"]), r)["pass"])
        self.assertFalse(grade(reply(r["answer"]) + reply(wrong), r)["pass"])


class WrongAnswersFail(unittest.TestCase):
    def test_list_every_option_scores_zero(self):
        for tid in TICKETS:
            r = ref(tid)
            hedge = {"cause": sorted(CAUSES), "layer": list(LAYERS), "owner": list(OWNERS),
                     "location": all_locations(), "next_check": list(CHECKS),
                     "value": [r["answer"]["value"], "0"]}
            g = grade("```json\n" + json.dumps(hedge) + "\n```", r)
            self.assertEqual(g["score"], 0.0, (tid, g))
            self.assertFalse(g["pass"])

    def test_or_strings_score_zero(self):
        for tid in TICKETS:
            r = ref(tid)
            a = single(r["answer"])
            hedge = {"cause": a["cause"] + " or " + other(CAUSES, a["cause"]),
                     "layer": a["layer"] + "|" + other(LAYERS, a["layer"]),
                     "owner": a["owner"] + "/" + other(OWNERS, a["owner"]),
                     "location": ", ".join(a["location"]),
                     "next_check": "none or request_transmitted_copy",
                     "value": a["value"] + " or 0"}
            g = grade(reply(hedge), r)
            self.assertEqual(g["score"], 0.0, (tid, g))

    def test_location_superset_and_subset_fail(self):
        for tid in TICKETS:
            r = ref(tid)
            a = r["answer"]
            sup = {**a, "location": a["location"] + ["UNH.0062"]}
            self.assertFalse(grade(reply(sup), r)["fields"]["location"]["correct"], tid)
            if len(a["location"]) > 1:
                sub = {**a, "location": a["location"][:-1]}
                self.assertFalse(grade(reply(sub), r)["fields"]["location"]["correct"], tid)

    def test_every_field_wrong_scores_zero(self):
        for tid in TICKETS:
            r = ref(tid)
            a = r["answer"]
            wrong = {"cause": other(CAUSES, a["cause"]), "layer": other(LAYERS, a["layer"]),
                     "owner": other(OWNERS, a["owner"]),
                     "location": ["NONE"] if a["location"] != ["NONE"] else ["UNB.0020"],
                     "next_check": "check_sender_clock", "value": "999"}
            g = grade(reply(wrong), r)
            self.assertEqual(g["score"], 0.0, (tid, g))

    def test_one_field_wrong_scores_five_sixths(self):
        for tid in TICKETS:
            r = ref(tid)
            a, full = single(r["answer"]), r["answer"]
            swaps = {"cause": other(CAUSES, full["cause"]), "layer": other(LAYERS, full["layer"]),
                     "owner": other(OWNERS, full["owner"]),
                     "location": ["NONE"] if a["location"] != ["NONE"] else ["UNB.0020"],
                     "next_check": "check_sender_clock", "value": "999"}
            for f, v in swaps.items():
                g = grade(reply({**a, f: v}), r)
                self.assertAlmostEqual(g["score"], 5 / 6, msg=(tid, f, g))
                self.assertEqual(g["diagnosis_pass"], f == "value")
                self.assertFalse(g["pass"])
                self.assertFalse(g["fields"][f]["correct"])

    def test_plausible_wrong_answers_do_not_pass(self):
        for tid, answers in PLAUSIBLE_WRONG.items():
            r = ref(tid)
            for a in answers:
                a = {"next_check": "none", **a, "value": r["answer"]["value"]}
                g = grade(reply(a), r)
                self.assertFalse(g["pass"], (tid, a, g))
                self.assertLess(g["score"], 1.0)

    def test_unparseable_and_missing(self):
        r = ref("E1")
        g = grade("The root cause is a mismatch between UNB and UNZ.", r)
        self.assertEqual(g["score"], 0.0)
        self.assertIsNotNone(g["parse_error"])
        g = grade("```json\n{\"cause\": \"interchange_control_reference_mismatch\",}\n```", r)
        self.assertEqual(g["score"], 0.0)
        g = grade(reply({"cause": r["answer"]["cause"]}), r)
        self.assertAlmostEqual(g["score"], 1 / 6)
        self.assertEqual(g["fields"]["owner"]["error"], "missing")

    def test_none_cannot_be_combined(self):
        r = ref("T1")
        a = {**r["answer"], "location": r["answer"]["location"] + ["NONE"]}
        self.assertFalse(grade(reply(a), r)["fields"]["location"]["correct"])


class FenceParsing(unittest.TestCase):
    """Regression: grader 1.0 mis-paired fences when a reply had other fenced
    blocks (```edifact, ```text) before the final ```json, and failed correct
    answers (gemini-4-argon, run draft-20261101T024015Z-b73385)."""

    def test_other_fenced_blocks_before_json(self):
        r = ref("E1")
        a = r["answer"]
        text = ("Analysis.\n\n```edifact\nUNB+UNOA:3+X:ZZZ+Y:ZZZ+261030:0725+00000122'\n```\n\n"
                "and the trailer:\n   ```text\n   UNZ+1+122'\n   ```\n\nFix it.\n\n"
                "```json\n" + json.dumps(a) + "\n```")
        self.assertTrue(grade(text, r)["pass"])

    def test_indented_and_unlabelled_blocks(self):
        r = ref("R1")
        a = r["answer"]
        text = "```\nsome log\n```\n\n  ```json\n  " + json.dumps(a) + "\n  ```\n"
        self.assertTrue(grade(text, r)["pass"])
        self.assertTrue(grade("```\n" + json.dumps(a) + "\n```", r)["pass"])
        self.assertTrue(grade("Final: ```json " + json.dumps(a) + " ```", r)["pass"])

    def test_wrong_json_after_correct_one_still_graded_last(self):
        r = ref("T1")
        wrong = {**r["answer"], "owner": "receiver"}
        text = "```json\n" + json.dumps(r["answer"]) + "\n```\n```edifact\nX\n```\n```json\n" + json.dumps(wrong) + "\n```"
        self.assertFalse(grade(text, r)["pass"])


class NextCheck(unittest.TestCase):
    def test_any_decisive_check_accepted(self):
        for tid in ("U1", "U2", "U5"):
            r = ref(tid)
            for c in r["answer"]["next_check"]:
                self.assertTrue(grade(reply({**r["answer"], "next_check": c}), r)["pass"], (tid, c))

    def test_determined_tickets_need_none(self):
        r = ref("T1")
        g = grade(reply({**r["answer"], "next_check": "request_receiver_gateway_log"}), r)
        self.assertFalse(g["pass"])

    def test_undetermined_cannot_be_combined(self):
        r = ref("U1")
        a = {**single(r["answer"]), "location": ["UNDETERMINED", "SFID.SFIDTIME"]}
        self.assertFalse(grade(reply(a), r)["fields"]["location"]["correct"])


class ValueField(unittest.TestCase):
    def test_value_kinds(self):
        from graders.grade import norm_value
        self.assertEqual(norm_value("33,554,432", "int")[0], "33554432")
        self.assertEqual(norm_value(33554432, "int")[0], "33554432")
        self.assertIsNone(norm_value("32768 blocks", "int")[0])
        self.assertIsNone(norm_value(True, "int")[0])
        self.assertEqual(norm_value(" 20261029  1421340001 ", "string")[0], "20261029 1421340001")
        self.assertEqual(norm_value("UNB+A'", "segment")[0], norm_value("UNB+A", "segment")[0])
        self.assertNotEqual(norm_value("UNB+A++++++'", "segment")[0], norm_value("UNB+A'", "segment")[0])
        self.assertIsNone(norm_value(["UNB+A'"], "segment")[0])


class Normalisation(unittest.TestCase):
    def test_tokens(self):
        cases = {"sfiddsn": "SFID.SFIDDSN", "SFID/SFIDTIME": "SFID.SFIDTIME",
                 "UNB S002 0004": "UNB.S002.0004", "unb.0004": "UNB.S002.0004",
                 "UNB:S003:0010": "UNB.S003.0010", "UNZ 0020": "UNZ.0020", "none": "NONE"}
        for k, v in cases.items():
            self.assertEqual(norm_location_token(k), v, k)

    def test_ambiguous_component_not_guessed(self):
        # 0007 occurs in both S002 and S003 of UNB: must not be mapped.
        self.assertEqual(norm_location_token("UNB 0007"), "UNB.0007")

    def test_extract_prefers_last_fence(self):
        obj, err = extract_answer("```json\n{\"a\": 1}\n```\ntext\n```json\n{\"a\": 2}\n```")
        self.assertEqual(obj, {"a": 2})


class AcceptedAlternatives(unittest.TestCase):
    def test_r2_layer_accepts_application_and_envelope(self):
        ref = json.loads((ROOT / "reference" / "R2.json").read_text())
        for layer in ("application", "envelope"):
            ans = {**ref["answer"], "layer": layer}
            g = grade("```json\n" + json.dumps(ans) + "\n```", ref)
            self.assertTrue(g["pass"], layer)
        g = grade("```json\n" + json.dumps({**ref["answer"], "layer": "transport"}) + "\n```", ref)
        self.assertFalse(g["pass"])
        g = grade("```json\n" + json.dumps({**ref["answer"], "layer": ["application", "envelope"]})
                  + "\n```", ref)
        self.assertFalse(g["fields"]["layer"]["correct"])      # listing both is still hedging


if __name__ == "__main__":
    unittest.main()

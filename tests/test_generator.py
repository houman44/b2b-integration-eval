"""Generator checks: byte-for-byte reproducibility, raw buffers match the RFC
5024 layouts, the planted fault is really present (and the red herrings are
ruled out by the documents), and nothing from reference/ leaks into a prompt."""
import json
import re
import unittest
from pathlib import Path

from generator.build import build_all, build_one
from generator.codes import ENTRIES
from generator.common import Ctx
from generator.oftp2raw import LAYOUTS, decode, encode, unshow
from generator.tickets import TICKETS
from graders.schema import CAUSES, LAYERS, OWNERS, all_locations

ROOT = Path(__file__).resolve().parent.parent
BUF = re.compile(r"^\S+ \S+ (\S+) (>>|<<) \[(.*)\]$")


def seg(text, tag):
    """Segments of an interchange as transmitted (no release characters are used)."""
    return [x.strip() for x in text.replace("\n", "").split("'") if x.strip().startswith(tag + "+")]


def events(log):
    """Decode every exchange buffer in a trace: [(session, dir, cmd, fields)]."""
    out = []
    for line in log.splitlines():
        m = BUF.match(line)
        if m:
            cmd, fields = decode(unshow(m.group(3)))
            out.append((m.group(1), m.group(2), cmd, fields))
    return out


def find(evs, cmd, direction=None):
    return [f for s, d, c, f in evs if c == cmd and (direction is None or d == direction)]


class Reproducible(unittest.TestCase):
    def test_two_builds_identical(self):
        a, _ = build_all()
        b, _ = build_all()
        self.assertEqual(a, b)

    def test_matches_committed_files(self):
        out, _ = build_all()
        for p, text in out.items():
            self.assertEqual((ROOT / p).read_bytes(), text.encode("utf-8"), p)

    def test_seed_matters(self):
        for tid, (seed, builder) in TICKETS.items():
            a = builder(Ctx(tid, seed)).documents
            b = builder(Ctx(tid, seed + 1)).documents
            self.assertNotEqual(a, b, tid)


class RawBuffers(unittest.TestCase):
    def test_fixed_offsets_match_rfc_tables(self):
        # positions quoted from the RFC 5024 5.3.x tables
        sfid = encode("SFID", [("SFIDDSN", "A"), ("SFIDDESCL", "000")])
        self.assertEqual(len(sfid), 165)                       # SFIDDESC starts at 165
        self.assertEqual(len(encode("SSID", [])), 61)          # SSIDCR at 60
        nerp = encode("NERP", [("NERPREASL", "000")])
        self.assertEqual(nerp[126:128], b"00")                 # NERPREAS at 126
        eerp = encode("EERP", [])
        self.assertEqual(len(eerp), 110)                       # HSHL at 106 (2) + SIGL (2)

    def test_every_buffer_round_trips(self):
        for tid in TICKETS:
            log = build_one(tid)[2].documents["oftp2_session.log"]
            for line in log.splitlines():
                m = BUF.match(line)
                if m:
                    raw = unshow(m.group(3))
                    cmd, fields = decode(raw)
                    if b"??" not in raw:
                        self.assertEqual(encode(cmd, fields.items()), raw, (tid, line))


class PlantedFault(unittest.TestCase):
    def setUp(self):
        self.b = {tid: build_one(tid)[2] for tid in TICKETS}
        self.assertEqual(set(self.b), {"T1", "T2", "E1", "E3", "R1", "R2", "S1", "U1", "U2", "U5"})

    def test_T1_resubmission_reuses_identity_of_acknowledged_file(self):
        b = self.b["T1"]
        f = b.facts
        v1, v2 = f["vfB"], f["vfB2"]
        for k in ("dsn", "date", "time"):
            self.assertEqual(v1[k], v2[k])
        self.assertNotEqual(v2["date"], "20261030")
        evs = events(b.documents["oftp2_session.log"])
        eerps = find(evs, "EERP", "<<")
        self.assertTrue(any(e["EERPDATE"] == v1["date"] and e["EERPTIME"] == v1["time"] for e in eerps))
        nerps = find(evs, "NERP", "<<")
        self.assertEqual(len(nerps), 2)
        for n in nerps:
            self.assertEqual(n["NERPCREA"], f["hub_id"])
            self.assertEqual((n["NERPDATE"], n["NERPTIME"]), (v1["date"], v1["time"]))
        self.assertEqual(find(evs, "SFNA"), [])
        self.assertTrue(any(e["EERPDATE"] == "20261030" for e in eerps))
        # busy day: other partners, interleaved; the status report blames the original
        self.assertGreater(len({s for s, *_ in evs}), 25)
        rep = b.documents["gateway_status.txt"]
        orig = [l for l in rep.splitlines() if f"{f['vfB_src']} " in l or l.rstrip().endswith(f["vfB_src"])]
        self.assertTrue(any("NOT DELIVERED" in l for l in rep.splitlines()))

    def test_E1_references_differ_only_in_leading_zeros(self):
        ic = self.b["E1"].documents["interchange.edi"]
        unb_ref = seg(ic, "UNB")[0].split("+")[5]
        unz = seg(ic, "UNZ")[0].split("+")
        self.assertNotEqual(unb_ref, unz[2])
        self.assertEqual(int(unb_ref), int(unz[2]))
        for h, t in zip(seg(ic, "UNH"), seg(ic, "UNT")):
            self.assertEqual(h.split("+")[1], t.split("+")[2])
        self.assertEqual(len(seg(ic, "UNG")), 1)
        self.assertEqual(int(unz[1]), 1)
        une = seg(ic, "UNE")[0].split("+")
        self.assertEqual(int(une[1]), len(seg(ic, "UNH")))
        self.assertEqual(int(self.b["E1"].answer["value"]), len(seg(ic, "UNH")))
        resp = self.b["E1"].documents["partner_response.txt"]
        self.assertIn("control count", resp)
        self.assertIn(f"UCI+{unb_ref}+", resp)

    def test_R1_only_the_test_indicator_is_wrong(self):
        b = self.b["R1"]
        ic = b.documents["interchange.edi"]
        agr = b.documents["partner_agreement.txt"]
        u = seg(ic, "UNB")[0].split("+")
        self.assertEqual(u[1], "UNOA:3")
        self.assertIn(f"(UNB S002 0004 / 0007): {u[2].split(':')[0]} / {u[2].split(':')[1]}", agr)
        self.assertIn(f"(UNB S003 0010 / 0007): {u[3].split(':')[0]} / {u[3].split(':')[1]}", agr)
        date, time = u[4].split(":")
        self.assertEqual((len(date), len(time)), (6, 4))
        self.assertEqual(u[5], seg(ic, "UNZ")[0].split("+")[2])
        self.assertEqual(u[6:], ["", "", "", "", "", "1"])          # 0035 = 1 at position 11
        self.assertEqual(b.answer["value"], "+".join(u[:6]) + "'")
        self.assertIn("does not return CONTRL", agr)
        self.assertIn("UNB 0035 (test indicator)", agr)
        evs = events(b.documents["oftp2_session.log"])
        self.assertEqual(len(find(evs, "EFNA", "<<")), 3)
        self.assertEqual(find(evs, "EFPA"), [])
        self.assertEqual(find(evs, "NERP"), [])
        for s in find(evs, "SSID", ">>"):
            self.assertEqual((s["SSIDSDEB"], s["SSIDCRED"]), ("16384", "128"))
        for s in find(evs, "SSID", "<<"):
            self.assertEqual((s["SSIDSDEB"], s["SSIDCRED"]), ("04096", "064"))

    def test_E3_amendment_not_yet_in_force(self):
        b = self.b["E3"]
        agr = b.documents["partner_agreement.txt"]
        self.assertIn("With effect from 1 November 2026", agr)
        self.assertIn("Syntax identifier and version (UNB S001): UNOA, version 3.", agr)
        self.assertTrue(seg(b.documents["interchange.edi"], "UNB")[0].startswith("UNB+UNOC:3+"))
        log = b.documents["oftp2_session.log"]
        self.assertTrue(all(l.startswith("2026-10-30") for l in log.splitlines() if l[:4].isdigit()))
        self.assertIn(f"UCI+{b.answer['value']}+", b.documents["partner_response.txt"])

    def test_T2_restart_units(self):
        f = self.b["T2"].facts
        evs = events(self.b["T2"].documents["oftp2_session.log"])
        rs = [(c, x) for s, d, c, x in evs if s == f["restart_sid"]]
        sfid = next(x for c, x in rs if c == "SFID")
        self.assertEqual(sfid["SFIDDEST"], f["dest"])
        self.assertEqual(int(sfid["SFIDREST"]), f["sent_before"])          # octets in a block field
        self.assertEqual(int(sfid["SFIDREST"]), f["held_blocks"] * 1024)
        self.assertGreater(int(sfid["SFIDREST"]), int(sfid["SFIDFSIZ"]))
        self.assertEqual(int(next(x for c, x in rs if c == "SFPA")["SFPAACNT"]), f["held_blocks"])
        # the other partner's restart is format V, counted in records, and succeeds
        v = [x for x in find(evs, "SFID", ">>") if x["SFIDDEST"] == f["p2_dest"]]
        self.assertEqual([x["SFIDFMT"] for x in v], ["V", "V"])
        self.assertGreater(int(v[1]["SFIDREST"]), 0)
        self.assertEqual(f["resent"], f["total"] - f["held_blocks"])
        self.assertNotEqual(f["sent_before"] + f["resent"], f["total"])
        self.assertEqual(len(find(evs, "EFNA", "<<")), 1)
        self.assertEqual(int(self.b["T2"].answer["value"]), f["held_blocks"] * 1024)

    def test_U1_nothing_decides_between_gw2_and_receiver(self):
        b = self.b["U1"]
        f = b.facts
        evs = events(b.documents["oftp2_session.log"])
        mine = [x for x in find(evs, "SFID", ">>") if x["SFIDDSN"] == f["vfB"]["dsn"]]
        stamps = [(x["SFIDDATE"], x["SFIDTIME"]) for x in mine]
        self.assertEqual(stamps.count((f["vfB"]["date"], f["vfB"]["time"])), 2)   # two attempts, gw1
        self.assertEqual(f["vfA"]["date"], f["vfB"]["date"])                       # same DSN + date
        self.assertNotEqual(f["vfA"]["time"], f["vfB"]["time"])
        self.assertIn("node gw1", b.documents["oftp2_session.log"].splitlines()[0])
        self.assertIn("gw2", b.documents["partner_agreement.txt"])
        self.assertNotIn("gw2", b.documents["oftp2_session.log"])

    def test_U2_archive_copy_is_flawless(self):
        b = self.b["U2"]
        ic = b.documents["interchange.edi"]
        u = seg(ic, "UNB")[0].split("+")
        agr = b.documents["partner_agreement.txt"]
        self.assertEqual(len(u), 6)
        self.assertIn(f"(UNB S002 0004 / 0007): {u[2].replace(':', ' / ')}", agr)
        self.assertIn(f"(UNB S003 0010 / 0007): {u[3].replace(':', ' / ')}", agr)
        self.assertIn("before\n   those rules are applied", agr)
        self.assertEqual(len(find(events(b.documents["oftp2_session.log"]), "EFNA", "<<")), 2)

    def test_U5_copy_is_not_the_original(self):
        b = self.b["U5"]
        f = b.facts
        self.assertNotEqual(f["ref_orig"], f["ref_copy"])
        self.assertIn(f"UCI+{f['ref_orig']}+", b.documents["partner_response.txt"])
        self.assertEqual(seg(b.documents["interchange.edi"], "UNB")[0].split("+")[5], f["ref_copy"])
        efids = find(events(b.documents["oftp2_session.log"]), "EFID", ">>")
        self.assertIn(f["octets"], [int(e["EFIDUCNT"]) for e in efids])
        self.assertNotEqual(f["octets"], len(b.documents["interchange.edi"]))

    def test_R2_receiver_rejects_the_agreed_id(self):
        b = self.b["R2"]
        sid = b.facts["sender_id"]
        self.assertIn(f"(UNB S002 0004 / 0007): {sid} / ZZ", b.documents["partner_agreement.txt"])
        self.assertEqual(seg(b.documents["interchange.edi"], "UNB")[0].split("+")[2], f"{sid}:ZZ")
        self.assertIn(f"+{sid}:ZZ+", seg(b.documents["partner_response.txt"], "UCI")[0] + "+")

    def test_unit_counts_match_interchange_bytes(self):
        for tid, b in self.b.items():
            n = b.facts["interchange_octets"]
            if n is None:            # U1: the file is refused at SFID, never transferred
                continue
            if not b.facts.get("excerpt"):
                self.assertEqual(n, len(b.documents["interchange.edi"].encode("ascii")), tid)
            efids = find(events(b.documents["oftp2_session.log"]), "EFID", ">>")
            self.assertTrue(any(int(e["EFIDUCNT"]) == n for e in efids), tid)

    def test_interchange_is_unoa_uppercase(self):
        for tid, b in self.b.items():
            ic = b.documents["interchange.edi"]
            if b.facts.get("excerpt"):
                ic = "".join(l for l in ic.splitlines() if not l.startswith("["))
            self.assertTrue(re.fullmatch(r"[A-Z0-9 .,\-()/='+:?!\"%&*;<>]*", ic), tid)


class AnswersAndPrompts(unittest.TestCase):
    def test_reference_values_are_in_the_schema(self):
        locs = set(all_locations())
        for tid in TICKETS:
            a = json.loads((ROOT / "reference" / f"{tid}.json").read_text())["answer"]
            self.assertIn(a["cause"], CAUSES)
            self.assertIn(a["layer"], LAYERS)
            self.assertIn(a["owner"], OWNERS)
            self.assertTrue(set(a["location"]) <= locs, (tid, a["location"]))
            self.assertIsInstance(a["value"], str)

    def test_no_reference_material_in_prompt(self):
        for tid in TICKETS:
            prompt = (ROOT / "tasks" / tid / "prompt.md").read_text()
            r = json.loads((ROOT / "reference" / f"{tid}.json").read_text())
            self.assertFalse(r["rationale"][:60] in prompt, tid)
            self.assertFalse(json.dumps(r["answer"]) in prompt, tid)
            self.assertFalse("rationale" in prompt.lower(), tid)
            self.assertFalse(any((ROOT / "tasks" / tid).rglob("*reference*")))

    def test_unverified_codes_are_marked_and_opaque(self):
        for tid in TICKETS:
            prompt = (ROOT / "tasks" / tid / "prompt.md").read_text()
            meta = json.loads((ROOT / "tasks" / tid / "meta.json").read_text())
            for key in meta["uses"]:
                e = ENTRIES[key]
                if e.kind == "code" and not e.verified:
                    self.assertNotIn(key, prompt)
                    if key.startswith("EDIFACT."):
                        self.assertIn(f"<<UNVERIFIED-{e.tag}>>", prompt)
                    else:
                        self.assertIn("DRAFT: '??' in a reason code field", prompt)
            self.assertEqual(meta["status"], "DRAFT")

    def test_release_build_refuses_while_unverified(self):
        from generator import build
        with self.assertRaises(SystemExit):
            build.main(["--release", "--check"])


if __name__ == "__main__":
    unittest.main()

"""Translation tasks: the model must produce an exact output document from an
input document and a mapping specification written for this eval.

X1: EDIFACT DESADV D.96A (packing hierarchy) -> the receiver's in-house JSON.
X2: the sender's in-house fixed-width flat file -> EDIFACT INVOIC D.96A.
"""
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from generator.common import Ctx
from .edifact import esc, fmt_decimal, transliterate_unoa

ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-()/='+:?")


@dataclass
class TTask:
    tid: str
    prompt_body: str      # task text + documents + spec
    out_kind: str         # "edifact" | "json"
    expected: object      # list of segments (edifact) or a JSON value
    rationale: str


# ------------------------------------------------------------------ X2
X2_SPEC = """\
MAPPING SPECIFICATION: in-house invoice flat file to EDIFACT INVOIC D.96A
(written for this evaluation; it is the only authority for this task)

Input: fixed-width records, positions counted in characters from 1.
  H record: pos 1 'H'; 2-11 invoice number (left-justified, space padded);
            12-19 invoice date CCYYMMDD; 20-22 currency; 23-57 buyer name (UTF-8).
  L record: pos 1 'L'; 2-4 line number; 5-19 part number (left-justified, space
            padded); 20-28 quantity, 9 digits, 3 implied decimals; 29-31 unit of
            measure; 32-43 unit price, 12 digits, 4 implied decimals.
  T record: pos 1 'T'; 2-5 number of L records.

Output: one interchange, syntax UNOA version 3, default service characters
(UNA not sent), release character ? before any of ? + : ' inside a value.
Segments, in this order:
  UNB+UNOA:3+{sender}:ZZZ+{recipient}:ZZZ+{prep_date}:{prep_time}+{ref}'
  UNH+1+INVOIC:D:96A:UN'
  BGM+380+<invoice number, trailing spaces removed>+9'
  DTM+137:<invoice date>:102'
  NAD+BY+++<buyer name, see below>'
  CUX+2:<currency>:4'
  per L record, in file order:
    LIN+<line number without leading zeros>++<part number, trailing spaces removed>:IN'
    QTY+47:<quantity>:<unit of measure>'
    MOA+203:<line amount>'
    PRI+AAA:<unit price>'
  UNS+S'
  MOA+77:<invoice total>'
  TAX+7+VAT+++:::20+S'
  MOA+124:<VAT amount>'
  UNT+<number of segments from UNH to UNT, both included>+1'
  UNZ+1+{ref}'

Values:
  quantity, unit price: decimal mark '.', no leading zeros, no trailing zeros
    after the decimal mark, no decimal mark for whole numbers (12.500 -> 12.5,
    7.000 -> 7, 0.250 -> 0.25).
  line amount = quantity x unit price, rounded half up to 2 decimals, always
    written with exactly 2 decimals (156.25, 40.00).
  VAT amount = 20 % of the sum of the line amounts, rounded half up to 2
    decimals, exactly 2 decimals. invoice total = sum of line amounts + VAT
    amount, exactly 2 decimals.
  buyer name: (1) replace A-umlaut by AE, O-umlaut by OE, U-umlaut by UE (either
    case), sharp s by SS, e-acute and e-grave by E, a-ring by A, o-slash by O;
    (2) convert to upper case; (3) replace every character not in
    A-Z 0-9 space . , - ( ) / = ' + : ? by a space; (4) replace runs of spaces by
    one space and remove leading and trailing spaces; (5) cut to the first 35
    characters, then remove trailing spaces; (6) add release characters.
    Release characters do not count towards the 35.
"""


def _hu(x: Decimal, places=2) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def build_X2(seed=50248002) -> TTask:
    ctx = Ctx("X2", seed)
    rng = ctx.rng
    sender, recipient = f"QUILLMERE{rng.digits(2)}", f"MARROWGATE{rng.digits(2)}"
    prep_date, prep_time, ref = "261102", f"09{rng.between(10, 59)}", f"{rng.between(100, 9999):06d}"
    inv = f"IV{rng.digits(6)}"
    date = f"202610{rng.between(26, 30)}"
    buyer = rng.choice(["Müller & Söhne Fahrzeugtechnik GmbH Werk Süd",
                        "O'Rourke+Partner Fahrwerkssysteme Österreich GmbH",
                        "Bäckström Axel & Hjul AB: Göteborgsfabriken"])
    parts = [rng.choice(["AX-4471/B", "KL+20/4", "SEAL?RING-7", "BRKT 45:A", "HUB-9031"])
             for _ in range(5)]
    # quantities and prices chosen so that some products hit an exact half cent
    lines = []
    specials = [(12500, 1250000), (7000, 1250), (250, 45000), (3000, 33335), (1500, 10050)]
    units = ["PCE", "PCE", "KGM", "PCE", "MTR"]
    for i in range(rng.between(4, 5)):
        q, p = specials[i]
        q += rng.below(3) * 1000
        lines.append((i + 1, parts[i], q, units[i], p))
    flat = [f"H{inv:<10}{date}EUR{buyer:<35}"[:57]]
    for n, part, q, u, p in lines:
        flat.append(f"L{n:03d}{part:<15}{q:09d}{u}{p:012d}")
    flat.append(f"T{len(lines):04d}")

    # expected output
    name = transliterate_unoa(buyer)
    name = "".join(c if c in ALLOWED else " " for c in name)
    name = " ".join(name.split())[:35].rstrip()
    segs = [f"UNB+UNOA:3+{sender}:ZZZ+{recipient}:ZZZ+{prep_date}:{prep_time}+{ref}",
            "UNH+1+INVOIC:D:96A:UN", f"BGM+380+{esc(inv)}+9", f"DTM+137:{date}:102",
            f"NAD+BY+++{esc(name)}", "CUX+2:EUR:4"]
    total = Decimal(0)
    for n, part, q, u, p in lines:
        amount = _hu(Decimal(q) / 1000 * Decimal(p) / 10000)
        total += amount
        segs += [f"LIN+{n}++{esc(part.rstrip())}:IN", f"QTY+47:{fmt_decimal(q, 3)}:{u}",
                 f"MOA+203:{amount:.2f}", f"PRI+AAA:{fmt_decimal(p, 4)}"]
    vat = _hu(total * Decimal("0.20"))
    segs += ["UNS+S", f"MOA+77:{total + vat:.2f}", "TAX+7+VAT+++:::20+S", f"MOA+124:{vat:.2f}"]
    segs.append(f"UNT+{len(segs) - 1 + 1}+1")
    segs.append(f"UNZ+1+{ref}")
    spec = X2_SPEC.format(sender=sender, recipient=recipient, prep_date=prep_date,
                          prep_time=prep_time, ref=ref)
    body = ("Translate the sender's in-house invoice file below into the EDIFACT interchange "
            "that the mapping specification defines. Reply with your working if you like, but "
            "end your reply with the complete interchange in one fenced ```edifact block. Only "
            "the last ```edifact block is graded, segment by segment, against the exact "
            "expected interchange; line breaks between segments are ignored.\n\n"
            "## In-house invoice file (fixed width)\n\n```text\n" + "\n".join(flat) +
            "\n```\n\n## Mapping specification\n\n```text\n" + spec + "```\n")
    return TTask("X2", body, "edifact", segs,
                 "Generated from the flat file by the specification's rules (see translation/tasks.py).")


# ------------------------------------------------------------------ X1
X1_SPEC = """\
MAPPING SPECIFICATION: EDIFACT DESADV D.96A to the Customer's in-house JSON
(written for this evaluation; it is the only authority for this task)

Input structure used by the Supplier:
  CPS+<id>' with no parent is the shipment. CPS+<id>+<parent id>' is a package
  whose parent is the CPS with that id; the PAC, PCI, GIN and LIN/QTY segments
  that follow a CPS, up to the next CPS, belong to it. PAC 7065 PX = pallet,
  CTN = carton. GIN+ML+<label>' is the package label. LIN+<n>++<part>:IN' with
  QTY+12:<quantity>:<unit>' is an item in that package. Packages may appear in
  any order; the parent id, not the position, decides where a package belongs.
  Values may contain release characters (?) that must be removed.

Output: one JSON object:
  {"despatch_note": <BGM 1004>,
   "despatch_date": <DTM 11 date as YYYY-MM-DD>,
   "pallets": [ one object per pallet, ordered by CPS id ascending:
       {"label": <GIN label>,
        "loose_items": [items directly in the pallet, in input order],
        "cartons": [ one object per carton in this pallet, ordered by CPS id
                     ascending: {"label": <GIN label>, "items": [items, in input order]} ]} ],
   "totals": [ {"part": <part>, "unit": <unit>, "quantity": <sum over all items
                with that part and unit>} sorted by part, then unit, ascending
               (plain character order) ]}
  An item is {"part": <part number>, "unit": <unit>, "quantity": <number>}.
  Quantities are JSON numbers. Keys and nesting exactly as above.
"""


def build_X1(seed=50248001) -> TTask:
    ctx = Ctx("X1", seed)
    rng = ctx.rng
    dn = f"DN{rng.digits(6)}"
    ddate = f"202610{rng.between(26, 30)}"
    parts = ["AX-4471/B", "KL+20/4", "HUB-9031", "SEAL?RING-7", "BRKT 45:A"]
    # hierarchy: shipment 1; pallets 2, 5, 9; cartons under them, declared out of order
    pallets = [2, 5, 9]
    cartons = {2: [3, 4], 5: [6, 8], 9: [10]}
    order = [1, 2, 3, 5, 6, 4, 9, 8, 10]           # declaration order (not by parent)
    loose = {5: [("HUB-9031", "PCE", 40)], 9: [("BRKT 45:A", "PCE", 12)]}
    content = {}
    for c in [3, 4, 6, 8, 10]:
        n = rng.between(1, 2)
        content[c] = [(rng.choice(parts), rng.choice(["PCE", "PCE", "KGM"]),
                       rng.between(5, 200) if True else 0) for _ in range(n)]
    content[6] = content[6] + [("SEAL?RING-7", "PCE", 250)]
    labels = {c: f"LBL{rng.digits(8)}" for c in [2, 3, 4, 5, 6, 8, 9, 10]}
    parent = {3: 2, 4: 2, 6: 5, 8: 5, 10: 9, 2: 1, 5: 1, 9: 1}
    segs = ["UNB+UNOA:3+QUILLMERE07:ZZZ+MARROWGATE11:ZZZ+261102:0715+004721",
            "UNH+1+DESADV:D:96A:UN", f"BGM+351+{dn}+9", "DTM+137:20261102:102",
            f"DTM+11:{ddate}:102", "NAD+SU+++QUILLMERE DRIVETRAIN LTD",
            "NAD+ST+++MARROWGATE MOTOR WORKS"]
    line = 0
    for cps in order:
        if cps == 1:
            segs.append("CPS+1")
            continue
        segs.append(f"CPS+{cps}+{parent[cps]}")
        kind = "PX" if cps in pallets else "CTN"
        segs += [f"PAC+1++{kind}", "PCI+17", f"GIN+ML+{labels[cps]}"]
        items = loose.get(cps, []) if cps in pallets else content[cps]
        for part, unit, q in items:
            line += 1
            segs += [f"LIN+{line}++{esc(part)}:IN", f"QTY+12:{q}:{unit}"]
    segs.append(f"UNT+{len(segs) - 1 + 1}+1")
    segs.append("UNZ+1+004721")
    ic = "".join(s + "'" for s in segs)

    def item(t):
        return {"part": t[0], "unit": t[1], "quantity": t[2]}
    out_pallets = []
    for p in sorted(pallets):
        out_pallets.append({"label": labels[p], "loose_items": [item(t) for t in loose.get(p, [])],
                            "cartons": [{"label": labels[c], "items": [item(t) for t in content[c]]}
                                        for c in sorted(cartons[p])]})
    totals = {}
    for p in pallets:
        for t in loose.get(p, []) + [x for c in cartons[p] for x in content[c]]:
            totals[(t[0], t[1])] = totals.get((t[0], t[1]), 0) + t[2]
    expected = {"despatch_note": dn, "despatch_date": f"{ddate[:4]}-{ddate[4:6]}-{ddate[6:]}",
                "pallets": out_pallets,
                "totals": [{"part": k[0], "unit": k[1], "quantity": v}
                           for k, v in sorted(totals.items())]}
    body = ("Translate the despatch advice below into the Customer's in-house JSON that the "
            "mapping specification defines. Reply with your working if you like, but end your "
            "reply with the complete JSON object in one fenced ```json block. Only the last "
            "```json block is graded, against the exact expected object.\n\n"
            "## EDIFACT DESADV as received (no line breaks)\n\n```text\n" + ic +
            "\n```\n\n## Mapping specification\n\n```text\n" + X1_SPEC + "```\n")
    return TTask("X1", body, "json", expected,
                 "Generated from the hierarchy by the specification's rules (see translation/tasks.py).")


TASKS = {"X1": build_X1, "X2": build_X2}

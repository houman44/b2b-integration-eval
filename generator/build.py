"""Build every ticket from its seed.

  python -m generator.build            write tasks/, reference/, graders/answer_schema.json
  python -m generator.build --check    rebuild in memory and fail if any committed file differs
  python -m generator.build --release  as the default, but fail while anything is unverified

The model sees only tasks/<ID>/prompt.md. reference/ holds the planted
answers and is never part of a prompt.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from . import GENERATOR_VERSION
from .codes import ENTRIES
from .common import Ctx
from .tickets import TICKETS
from graders.schema import answer_instructions, answer_json_schema

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"<<(UNVERIFIED-[A-Z]+|PENDING:[A-Z0-9_.]+)>>")

DOC_TITLES = {
    "partner_agreement.txt": "Partner agreement",
    "oftp2_session.log": "OFTP2 gateway debug trace (sender side)",
    "interchange.edi": "EDIFACT interchange the ticket is about (as transmitted)",
    "partner_response.txt": "Partner response",
    "gateway_status.txt": "Gateway file status report (sender side)",
}

INTRO = """\
You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. The partner agreement,
the sender's OFTP2 gateway trace (and, where available, its file status report),
the EDIFACT interchange in question, the partner's response and extracts from the
specifications are attached. Everything you need
is in these documents. All companies, identifiers and documents are synthetic.
"""

def render_extracts(names):
    parts = []
    for n in names:
        parts.append((ROOT / "spec" / n).read_text(encoding="ascii"))
    return "\n".join(parts)


def fence(text, lang="text"):
    return f"```{lang}\n{text.rstrip(chr(10))}\n```\n"


def build_one(tid):
    seed, builder = TICKETS[tid]
    ctx = Ctx(tid, seed)
    b = builder(ctx)
    files = {}
    for name, text in b.documents.items():
        files[f"inputs/{name}"] = text
    files["inputs/spec_extracts.txt"] = render_extracts(b.extracts)

    prompt = [f"# Ticket {tid}", "", INTRO, "## The ticket", "", fence(b.narrative)]
    n = 1
    for name, text in b.documents.items():
        title = b.titles.get(name, DOC_TITLES[name])
        prompt += [f"## Document {n}: {title} ({name})", "", fence(text)]
        n += 1
    prompt += [f"## Document {n}: Specification extracts (spec_extracts.txt)", "",
               fence(files["inputs/spec_extracts.txt"]), answer_instructions(b.value_question)]
    files["prompt.md"] = "\n".join(prompt)

    unverified = sorted(k for k in ctx.uses if not ENTRIES[k].verified)
    placeholders = sorted(set(m.group(0) for m in PLACEHOLDER.finditer(files["prompt.md"])))
    meta = {
        "id": tid, "seed": seed, "generator_version": GENERATOR_VERSION,
        "status": "DRAFT" if (unverified or placeholders) else "RELEASE",
        "uses": sorted(ctx.uses), "unverified": unverified, "placeholders": placeholders,
        "files": {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(files.items())},
    }
    files["meta.json"] = json.dumps(meta, indent=2) + "\n"

    reference = {
        "id": tid,
        "answer": {**b.answer, "location": sorted(b.answer["location"])},
        "value_kind": b.value_kind,
        "rationale": b.rationale,
        "status": meta["status"],
        "depends_on_unverified": unverified,
    }
    out = {f"tasks/{tid}/{k}": v for k, v in files.items()}
    out[f"reference/{tid}.json"] = json.dumps(reference, indent=2) + "\n"
    return out, meta, b


def build_all():
    out, metas = {}, {}
    for tid in TICKETS:
        files, meta, _ = build_one(tid)
        out.update(files)
        metas[tid] = meta
    out["graders/answer_schema.json"] = json.dumps(answer_json_schema(), indent=2) + "\n"
    return out, metas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--release", action="store_true")
    a = ap.parse_args(argv)
    out, metas = build_all()

    if a.release:
        bad = {t: m["unverified"] + m["placeholders"] for t, m in metas.items()
               if m["unverified"] or m["placeholders"]}
        if bad:
            for t, items in bad.items():
                print(f"{t}: {len(items)} unverified item(s): " + ", ".join(items))
            sys.exit("release refused: verify the items above in generator/codes.py "
                     "and add the pending spec extracts")

    if a.check:
        diffs = [p for p, text in out.items()
                 if not (ROOT / p).exists() or (ROOT / p).read_bytes() != text.encode("utf-8")]
        if diffs:
            sys.exit("not byte-identical to committed files: " + ", ".join(diffs))
        print(f"check ok: {len(out)} files regenerate byte for byte")
        return

    for p, text in out.items():
        path = ROOT / p
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    for t, m in metas.items():
        print(f"{t}: {m['status']}, {len(m['unverified'])} unverified, "
              f"{len(m['placeholders'])} placeholder(s)")


if __name__ == "__main__":
    main()

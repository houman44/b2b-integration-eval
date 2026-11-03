"""Agentic variant: each ticket becomes a support workspace (a virtual file
system) that the model must explore with tools instead of receiving the
documents in its prompt. Built deterministically from the ticket's seed.

The ticket's own documents are placed where a support engineer would find
them, among distractors: other partners' agreements, other days' traces,
other interchanges and all spec extracts.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from generator.build import ROOT, build_one
from generator.common import BACKGROUND, Ctx, agreement, interchange, invoic_message, unb, unz
from generator.tickets import SPEC_EDIFACT, TICKETS



def _split_trace(text, node):
    """One file per day, each with the trace header."""
    header = [l for l in text.splitlines() if l.startswith("#")]
    days = {}
    for line in text.splitlines():
        m = re.match(r"^(\d{4}-\d{2}-\d{2}) ", line)
        if m:
            days.setdefault(m.group(1), []).append(line)
    return {f"gateway/{node}/trace-{d}.log": "\n".join(header + [""] + lines) + "\n"
            for d, lines in sorted(days.items())}


def _interchange_path(b, tid):
    title = b.titles.get("interchange.edi", "")
    m = re.search(r"BGM\+380\+(INV\d+)", b.documents["interchange.edi"])
    name = (m.group(1) if m else tid) + ".edi"
    if "archive" in title:
        return f"archive/{name}"
    if "regenerated" in title:
        return f"support/regenerated/{name}"
    if "excerpt" in title:
        return f"outbound-wire/{name[:-4]}_excerpt.edi"
    return f"outbound-wire/{name}"


def build_env(tid):
    """Return (files, bundle): files maps path -> text."""
    _, meta, b = build_one(tid)
    seed, _ = TICKETS[tid]
    files = {}
    docs = b.documents
    agr = docs["partner_agreement.txt"]
    sender = re.search(r"Between (.+?) \(the Supplier\) and (.+?) \(the Customer\)", agr)
    s_name, r_name = sender.group(1), sender.group(2)
    r_dir = re.sub(r"[^A-Za-z]", "", r_name.split()[0]).lower()
    files[f"partners/{r_dir}/agreement.txt"] = agr
    node = "gw1"
    files.update(_split_trace(docs["oftp2_session.log"], node))
    if "gateway_status.txt" in docs:
        files["gateway/status/file-status.txt"] = docs["gateway_status.txt"]
    files[_interchange_path(b, tid)] = docs["interchange.edi"]
    files[f"mail/inbox/{r_dir}-reply.txt"] = docs["partner_response.txt"]
    for p in sorted((ROOT / "spec" / "rfc5024").glob("*.txt")):
        files[f"spec/rfc5024/{p.name}"] = p.read_text(encoding="ascii")
    files[f"spec/{SPEC_EDIFACT}"] = (ROOT / "spec" / SPEC_EDIFACT).read_text(encoding="ascii")

    # Distractors: other partners' agreements and interchanges, from a second
    # seeded context so the ticket's own documents are unchanged.
    ctx = Ctx(tid + "-env", seed + 7)
    s_party, _ = ctx.parties()
    s_party.name = s_name
    for p in ctx.distinct_parties(BACKGROUND, 6, "203.0.113"):
        d = p.short.lower()
        files[f"partners/{d}/agreement.txt"] = agreement(
            s_party, p, effective="1 March 2026", sdeb=4096, cred=64,
            dsn=f"{s_party.short[:10]}.INVOIC", sender_edi_id=s_party.edi_id)
        for k in range(2):
            t = datetime(2026, 10, 29, ctx.rng.between(7, 17), ctx.rng.between(0, 59))
            ref = f"{ctx.rng.between(100, 999999):06d}"
            inv = f"INV{ctx.rng.digits(5)}"
            ic = interchange([unb(ctx, "UNOA", "3", s_party.edi_id, p.edi_id, t, ref)]
                             + invoic_message(ctx, "1", inv, t, s_party, p, [(f"P-{ctx.rng.digits(5)}", 10, 500)])
                             + [unz(ctx, 1, ref)])
            files[f"outbound-wire/{inv}.edi"] = ic
    files["README.txt"] = (
        f"Support workspace of {s_name}'s EDI desk.\n\n"
        "gateway/<node>/trace-<date>.log  OFTP2 gateway debug traces, one file per node and day\n"
        "gateway/status/                  gateway file status reports (where available)\n"
        "outbound-wire/                   interchanges as transmitted (wire copies), for partners\n"
        "                                 where wire capture is enabled\n"
        "archive/                         interchanges as produced by the translator\n"
        "support/                         files prepared by the support team\n"
        "partners/<partner>/              partner agreements\n"
        "mail/inbox/                      correspondence\n"
        "spec/                            RFC 5024 extracts and UN/EDIFACT extracts\n")
    return dict(sorted(files.items())), b


def manifest(files):
    return {p: hashlib.sha256(t.encode("utf-8")).hexdigest() for p, t in files.items()}


class Workspace:
    """The tools the model may call. All read-only."""
    MAX_LINES, MAX_LINE_CHARS, MAX_HITS = 200, 4000, 50

    def __init__(self, files):
        self.files = files

    def list_dir(self, path="/"):
        path = path.strip("/")
        prefix = path + "/" if path else ""
        entries = {}
        for p, t in self.files.items():
            if p.startswith(prefix):
                rest = p[len(prefix):]
                head = rest.split("/", 1)[0]
                entries[head + ("/" if "/" in rest else "")] = (
                    None if "/" in rest else len(t.encode("utf-8")))
        if not entries:
            return f"no such directory: /{path}"
        return "\n".join(f"{n}" + ("" if s is None else f"  ({s} octets)")
                         for n, s in sorted(entries.items()))

    def read_file(self, path, start_line=1, max_lines=200):
        path = path.strip("/")
        if path not in self.files:
            return f"no such file: /{path}"
        lines = self.files[path].splitlines()
        start = max(1, int(start_line))
        n = max(1, min(int(max_lines), self.MAX_LINES))
        chunk = lines[start - 1:start - 1 + n]
        out = [f"{start + i}: {l[:self.MAX_LINE_CHARS]}" for i, l in enumerate(chunk)]
        tail = (f"[lines {start}-{start + len(chunk) - 1} of {len(lines)}]")
        return "\n".join(out + [tail])

    def search(self, pattern, path="/"):
        try:
            rx = re.compile(pattern, re.I)
        except re.error as e:
            return f"invalid regular expression: {e}"
        prefix = path.strip("/")
        hits = []
        for p, t in self.files.items():
            if not p.startswith(prefix):
                continue
            for i, l in enumerate(t.splitlines(), 1):
                m = rx.search(l)
                if m:
                    a = max(0, m.start() - 150)
                    hits.append(f"/{p}:{i}: {l[a:a + 300]}")
                    if len(hits) >= self.MAX_HITS:
                        return "\n".join(hits + ["[more matches not shown]"])
        return "\n".join(hits) if hits else "no matches"

    def call(self, name, args):
        if name == "list_dir":
            return self.list_dir(args.get("path", "/"))
        if name == "read_file":
            return self.read_file(args["path"], args.get("start_line", 1), args.get("max_lines", 200))
        if name == "search":
            return self.search(args["pattern"], args.get("path", "/"))
        return f"unknown tool: {name}"


TOOLS = [
    {"type": "function", "function": {
        "name": "list_dir", "description": "List a directory of the support workspace.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read lines of a file (at most 200 lines per call, numbered from 1).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "start_line": {"type": "integer"},
            "max_lines": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "search",
        "description": "Search files under a path for a case-insensitive regular expression "
                       "(at most 50 matching lines).",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"}, "path": {"type": "string"}},
            "required": ["pattern"]}}},
]

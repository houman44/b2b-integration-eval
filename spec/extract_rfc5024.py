"""Cut the RFC 5024 sections the tickets quote into spec/rfc5024/*.txt.

Usage: python spec/extract_rfc5024.py path/to/rfc5024.txt

The text is copied verbatim; only page furniture (page footers, running
headers, form feeds) is removed and runs of blank lines are collapsed.
The input is checked against the SHA-256 of the copy retrieved from
https://www.rfc-editor.org/rfc/rfc5024.txt on 30 Oct 2026.
"""
import hashlib
import re
import sys
from pathlib import Path

RFC_SHA256 = "6411a2761da53deb63ba027caaf4e3bb15e883fe418a5f7a7c9f04aa5d5c4fa2"

# section number -> output file name
SECTIONS = {
    "1.5.2": "s1.5.2_virtual_file_identification.txt",
    "1.5.4": "s1.5.4_restart.txt",
    "4.3.3": "s4.3.3_restart_facilities.txt",
    "4.3.2": "s4.3.2_start_file_protocol_sequence.txt",
    "4.3.6": "s4.3.6_end_to_end_response.txt",
    "4.3.7": "s4.3.7_negative_end_response.txt",
    "4.6.1": "s4.6.1_end_session_protocol_sequence.txt",
    "5.3": "s5.3_command_format_conventions.txt",
    "5.3.2": "s5.3.2_ssid.txt",
    "5.3.3": "s5.3.3_sfid.txt",
    "5.3.4": "s5.3.4_sfpa.txt",
    "5.3.5": "s5.3.5_sfna.txt",
    "5.3.8": "s5.3.8_efid.txt",
    "5.3.9": "s5.3.9_efpa.txt",
    "5.3.10": "s5.3.10_efna.txt",
    "5.3.11": "s5.3.11_esid.txt",
    "5.3.13": "s5.3.13_eerp.txt",
    "5.3.14": "s5.3.14_nerp.txt",
}

HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.\s{2}\S")
FOOTER = re.compile(r"^Friend\s+Informational\s+\[Page \d+\]\s*$")
RUNNING_HEAD = re.compile(r"^RFC 5024\s+ODETTE FTP 2\s+November 2007\s*$")


def clean(lines):
    out = []
    for line in lines:
        line = line.replace("\f", "").rstrip()
        if FOOTER.match(line) or RUNNING_HEAD.match(line):
            continue
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def main(path):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != RFC_SHA256:
        sys.exit(f"unexpected RFC text (sha256 {digest})")
    lines = raw.decode("ascii").split("\n")
    heads = [(i, m.group(1)) for i, l in enumerate(lines) if (m := HEADING.match(l))]
    # skip the table of contents: keep the last occurrence of each number
    last = {}
    for i, num in heads:
        last[num] = i
    starts = sorted(last.items(), key=lambda kv: kv[1])
    outdir = Path(__file__).parent / "rfc5024"
    outdir.mkdir(exist_ok=True)
    for num, fname in SECTIONS.items():
        start = last[num]
        nxt = [i for _, i in starts if i > start]
        end = nxt[0] if nxt else len(lines)
        body = clean(lines[start:end])
        header = f"RFC 5024 (ODETTE File Transfer Protocol 2), section {num}. Verbatim extract.\n\n"
        (outdir / fname).write_text(header + body, encoding="ascii", newline="\n")
        print(f"{num:7} -> {fname} ({end - start} lines)")


if __name__ == "__main__":
    main(sys.argv[1])

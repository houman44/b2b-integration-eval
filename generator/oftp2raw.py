"""Encode and decode OFTP2 command exchange buffers as RFC 5024 section 5.3
lays them out (zero-origin positions, X left-justified space-padded, 9
right-justified zero-padded, U binary in network byte order).

The trace shows each buffer between [ and ], with non-printable octets as
\\xNN. The encoder is checked against the decoder in the tests.
"""
import re

# (field, kind, length). kind: F fixed value, X alnum, 9 numeric, T text with
# preceding length field, U binary length 2, B binary (length from previous U),
# CR carriage return. Lengths follow the tables in RFC 5024 5.3.x.
LAYOUTS = {
    "SSRM": [("SSRMCMD", "F", "I"), ("SSRMMSG", "X", 17), ("SSRMCR", "CR", 1)],
    "SSID": [("SSIDCMD", "F", "X"), ("SSIDLEV", "9", 1), ("SSIDCODE", "X", 25),
             ("SSIDPSWD", "X", 8), ("SSIDSDEB", "9", 5), ("SSIDSR", "X", 1),
             ("SSIDCMPR", "X", 1), ("SSIDREST", "X", 1), ("SSIDSPEC", "X", 1),
             ("SSIDCRED", "9", 3), ("SSIDAUTH", "X", 1), ("SSIDRSV1", "X", 4),
             ("SSIDUSER", "X", 8), ("SSIDCR", "CR", 1)],
    "SFID": [("SFIDCMD", "F", "H"), ("SFIDDSN", "X", 26), ("SFIDRSV1", "X", 3),
             ("SFIDDATE", "9", 8), ("SFIDTIME", "9", 10), ("SFIDUSER", "X", 8),
             ("SFIDDEST", "X", 25), ("SFIDORIG", "X", 25), ("SFIDFMT", "X", 1),
             ("SFIDLRECL", "9", 5), ("SFIDFSIZ", "9", 13), ("SFIDOSIZ", "9", 13),
             ("SFIDREST", "9", 17), ("SFIDSEC", "9", 2), ("SFIDCIPH", "9", 2),
             ("SFIDCOMP", "9", 1), ("SFIDENV", "9", 1), ("SFIDSIGN", "X", 1),
             ("SFIDDESCL", "9", 3), ("SFIDDESC", "T", "SFIDDESCL")],
    "SFPA": [("SFPACMD", "F", "2"), ("SFPAACNT", "9", 17)],
    "SFNA": [("SFNACMD", "F", "3"), ("SFNAREAS", "9", 2), ("SFNARRTR", "X", 1),
             ("SFNAREASL", "9", 3), ("SFNAREAST", "T", "SFNAREASL")],
    "EFID": [("EFIDCMD", "F", "T"), ("EFIDRCNT", "9", 17), ("EFIDUCNT", "9", 17)],
    "EFPA": [("EFPACMD", "F", "4"), ("EFPACD", "X", 1)],
    "EFNA": [("EFNACMD", "F", "5"), ("EFNAREAS", "9", 2), ("EFNAREASL", "9", 3),
             ("EFNAREAST", "T", "EFNAREASL")],
    "ESID": [("ESIDCMD", "F", "F"), ("ESIDREAS", "9", 2), ("ESIDREASL", "9", 3),
             ("ESIDREAST", "T", "ESIDREASL"), ("ESIDCR", "CR", 1)],
    "CD": [("CDCMD", "F", "R")],
    "RTR": [("RTRCMD", "F", "P")],
    "EERP": [("EERPCMD", "F", "E"), ("EERPDSN", "X", 26), ("EERPRSV1", "X", 3),
             ("EERPDATE", "9", 8), ("EERPTIME", "9", 10), ("EERPUSER", "X", 8),
             ("EERPDEST", "X", 25), ("EERPORIG", "X", 25), ("EERPHSHL", "U", 2),
             ("EERPHSH", "B", "EERPHSHL"), ("EERPSIGL", "U", 2), ("EERPSIG", "B", "EERPSIGL")],
    "NERP": [("NERPCMD", "F", "N"), ("NERPDSN", "X", 26), ("NERPRSV1", "X", 6),
             ("NERPDATE", "9", 8), ("NERPTIME", "9", 10), ("NERPDEST", "X", 25),
             ("NERPORIG", "X", 25), ("NERPCREA", "X", 25), ("NERPREAS", "9", 2),
             ("NERPREASL", "9", 3), ("NERPREAST", "T", "NERPREASL"), ("NERPHSHL", "U", 2),
             ("NERPHSH", "B", "NERPHSHL"), ("NERPSIGL", "U", 2), ("NERPSIG", "B", "NERPSIGL")],
}

PLACEHOLDER = re.compile(r"<<UNVERIFIED-[A-Z]+>>")
DRAFT_MARK = "?"     # an unverified code is shown as ?? in its 2-digit field


def encode(cmd, fields) -> bytes:
    vals = dict(fields)
    out = bytearray()
    for name, kind, ln in LAYOUTS[cmd]:
        v = vals.get(name)
        if kind == "F":
            out += ln.encode("ascii")
        elif kind == "CR":
            out += b"\r"
        elif kind == "X":
            out += str(v or "").ljust(ln)[:ln].encode("ascii")
        elif kind == "9":
            v = str(v if v not in (None, "") else 0)
            if PLACEHOLDER.fullmatch(v):
                out += (DRAFT_MARK * ln).encode("ascii")
            else:
                out += v.rjust(ln, "0").encode("ascii")
        elif kind == "T":
            out += str(v or "").encode("utf-8")
        elif kind == "U":
            out += int(v or 0).to_bytes(2, "big")
        elif kind == "B":
            out += bytes(v or b"")
    return bytes(out)


def show(buf: bytes) -> str:
    """Printable rendering: printable ASCII as is, everything else as \\xNN."""
    return "".join(chr(b) if 32 <= b < 127 and b != 92 else f"\\x{b:02X}" for b in buf)


def unshow(text: str) -> bytes:
    return bytes(int(m.group(1), 16) if m.group(1) else ord(m.group(2))
                 for m in re.finditer(r"\\x([0-9A-F]{2})|(.)", text, re.S))


def decode(buf: bytes):
    cmd_char = chr(buf[0])
    cmd = next(c for c, lay in LAYOUTS.items() if lay[0][2] == cmd_char)
    pos, out = 0, {}
    for name, kind, ln in LAYOUTS[cmd]:
        if kind in ("F", "CR"):
            n = 1
            val = buf[pos:pos + 1].decode("ascii")
        elif kind in ("X", "9"):
            n = ln
            val = buf[pos:pos + n].decode("ascii")
            val = val.rstrip() if kind == "X" else val
        elif kind == "T":
            n = int(out[ln])
            val = buf[pos:pos + n].decode("utf-8")
        elif kind == "U":
            n = 2
            val = int.from_bytes(buf[pos:pos + 2], "big")
        elif kind == "B":
            n = int(out[ln])
            val = buf[pos:pos + n]
        out[name] = val
        pos += n
    return cmd, out

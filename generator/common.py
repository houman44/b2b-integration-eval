"""Building blocks shared by all tickets: parties, OFTP2 session logs,
EDIFACT interchanges and partner agreements. All synthetic."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .codes import ENTRIES, placeholder
from .oftp2raw import encode, show
from .rng import SeededRNG

# Invented names. Houman to confirm none collides with a real company.
SENDERS = [
    ("Quillmere Drivetrain Ltd", "QUILLMERE"),
    ("Osterbrook Axle Systems", "OSTERBROOK"),
    ("Fenwray Castings Ltd", "FENWRAY"),
    ("Larkspan Body Panels", "LARKSPAN"),
    ("Tidewell Seating Components", "TIDEWELL"),
]
RECEIVERS = [
    ("Marrowgate Motor Works", "MARROWGATE"),
    ("Velbrook Vehicle Assembly", "VELBROOK"),
    ("Corrandale Truck Plant", "CORRANDALE"),
]
HUBS = [
    ("Quorlane Exchange", "QUORLANE"),
    ("Brannock EDI Exchange", "BRANNOCK"),
]
# Background trading partners of the sender (only appear in busy-day traces).
BACKGROUND = [
    ("Harrowfield Glass", "HARROWFLD"),
    ("Pemberline Plastics", "PEMBERLINE"),
    ("Ostley Fasteners", "OSTLEY"),
    ("Wrenmoor Electronics", "WRENMOOR"),
    ("Calderbank Wiring", "CALDERBANK"),
    ("Thornvale Logistics", "THORNVALE"),
]
FIRST_NAMES = ["Alex", "Sam", "Jordan", "Robin", "Kim", "Morgan", "Chris", "Dana"]
LAST_NAMES = ["Hale", "Okafor", "Brandt", "Novak", "Lindqvist", "Moreau", "Price", "Tanaka"]


@dataclass
class Party:
    name: str
    short: str
    odette_id: str      # RFC 5024 s5.4: 'O' + ICD(4) + org code(<=14) + subaddress(<=6)
    edi_id: str         # UNB S002/S003 identification
    host: str
    ip: str
    contact: str


class Ctx:
    """Per-ticket generation context: seeded RNG plus a record of every
    registry entry the ticket depends on."""

    def __init__(self, ticket_id: str, seed: int):
        self.ticket_id = ticket_id
        self.seed = seed
        self.rng = SeededRNG(seed)
        self.uses = set()

    def code(self, key: str) -> str:
        """A reason or action code: placeholder until verified."""
        e = ENTRIES[key]
        assert e.kind == "code", key
        self.uses.add(key)
        return e.value if e.verified else placeholder(key)

    def conv(self, key: str) -> str:
        """A convention: always rendered, but tracked."""
        e = ENTRIES[key]
        assert e.kind == "convention", key
        self.uses.add(key)
        return e.value

    def person(self) -> str:
        return f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}"

    def party(self, pool, ip_block: str) -> Party:
        name, short = self.rng.choice(pool)
        org = f"{short[:10]}{self.rng.digits(4)}"
        return Party(
            name=name, short=short,
            odette_id=f"O0013{org}",
            edi_id=f"{short[:10]}{self.rng.digits(2)}",
            host=f"oftp.{short.lower()}.example",
            ip=f"{ip_block}.{self.rng.between(10, 250)}",
            contact=self.person(),
        )

    def parties(self):
        s = self.party(SENDERS, "198.51.100")
        r = self.party(RECEIVERS, "203.0.113")
        return s, r

    def hub(self) -> Party:
        return self.party(HUBS, "192.0.2")

    def distinct_parties(self, pool, n, ip_block):
        """n different parties from pool, in a seeded order."""
        left = list(pool)
        out = []
        for _ in range(n):
            name, short = left.pop(self.rng.below(len(left)))
            org = f"{short[:10]}{self.rng.digits(4)}"
            out.append(Party(name=name, short=short, odette_id=f"O0013{org}",
                             edi_id=f"{short[:10]}{self.rng.digits(2)}",
                             host=f"oftp.{short.lower()}.example",
                             ip=f"{ip_block}.{self.rng.between(10, 250)}",
                             contact=self.person()))
        return out


# --------------------------------------------------------------------------
# OFTP2 session log (written from the sender's gateway point of view)
# --------------------------------------------------------------------------

def ts(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S.") + f"{t.microsecond // 1000:03d}"


def fmt_fields(fields):
    out = []
    for k, v in fields:
        v = str(v)
        if v == "" or " " in v:
            v = f"'{v}'"
        out.append(f"{k}={v}")
    return " ".join(out)


@dataclass
class VirtualFile:
    dsn: str
    date: str       # CCYYMMDD
    time: str       # HHMMSScccc
    dest: str
    orig: str
    octets: int

    @property
    def blocks(self) -> int:
        return max(1, -(-self.octets // 1024))


class Oftp2Log:
    def __init__(self, ctx: Ctx, local: Party, remote: Party, sdeb: int, cred: int):
        self.ctx, self.local, self.remote = ctx, local, remote
        self.sdeb, self.cred = sdeb, cred
        self.lines = [
            f"# OFTP2 gateway debug trace, {local.name} ({local.odette_id})",
            "# '>>' = command exchange buffer sent by this gateway, '<<' = received from the",
            "# remote OFTP2 location. Each buffer is shown as transmitted, between [ and ]",
            "# (Stream Transmission Header omitted, non-printable octets as \\xNN).",
            "# '..' = gateway event, '!!' = gateway warning. Passwords are masked.",
        ]
        self.t = None
        self.sid = None

    def _tick(self, lo=8, hi=180):
        self.t += timedelta(milliseconds=self.ctx.rng.between(lo, hi))
        return ts(self.t)

    def out(self, cmd, fields=()):
        self.lines.append(f"{self._tick()} {self.sid} >> [{show(encode(cmd, fields))}]")

    def inn(self, cmd, fields=()):
        self.lines.append(f"{self._tick()} {self.sid} << [{show(encode(cmd, fields))}]")

    def note(self, text, lo=8, hi=180):
        self.lines.append(f"{self._tick(lo, hi)} {self.sid} .. {text}")

    def blank(self):
        self.lines.append("")

    def _ssid(self, party, sdeb=None, cred=None):
        return [("SSIDLEV", "5"), ("SSIDCODE", party.odette_id), ("SSIDPSWD", "********"),
                ("SSIDSDEB", f"{sdeb or self.sdeb:05d}"), ("SSIDSR", "B"), ("SSIDCMPR", "N"),
                ("SSIDREST", "Y"), ("SSIDSPEC", "N"), ("SSIDCRED", f"{cred or self.cred:03d}"),
                ("SSIDAUTH", "N"), ("SSIDUSER", "")]

    def open_outbound(self, start: datetime, sid: str, offer_sdeb=None, offer_cred=None):
        """This gateway calls the partner (we are Initiator, then Speaker).
        offer_*: values this gateway offers; the Responder answers with the
        smaller values (RFC 5024 5.3.2), which are then in force."""
        self.t, self.sid = start, sid
        self.blank()
        self.note(f"session {sid}: TCP connect to {self.remote.host} ({self.remote.ip}), TLS 1.3 established", 0, 0)
        self.inn("SSRM", [("SSRMMSG", "ODETTE FTP READY")])
        self.out("SSID", self._ssid(self.local, offer_sdeb, offer_cred))
        self.inn("SSID", self._ssid(self.remote))

    def open_inbound(self, start: datetime, sid: str):
        """The partner calls this gateway (partner is Initiator, then Speaker)."""
        self.t, self.sid = start, sid
        self.blank()
        self.note(f"session {sid}: inbound TCP connection from {self.remote.ip}, TLS 1.3 established", 0, 0)
        self.out("SSRM", [("SSRMMSG", "ODETTE FTP READY")])
        self.inn("SSID", self._ssid(self.remote))
        self.out("SSID", self._ssid(self.local))

    @staticmethod
    def sfid_fields(vf: VirtualFile):
        return [("SFIDDSN", vf.dsn), ("SFIDDATE", vf.date), ("SFIDTIME", vf.time),
                ("SFIDUSER", ""), ("SFIDDEST", vf.dest), ("SFIDORIG", vf.orig),
                ("SFIDFMT", "U"), ("SFIDLRECL", "00000"),
                ("SFIDFSIZ", f"{vf.blocks:013d}"), ("SFIDOSIZ", f"{vf.blocks:013d}"),
                ("SFIDREST", "0"), ("SFIDSEC", "00"), ("SFIDCIPH", "00"),
                ("SFIDCOMP", "0"), ("SFIDENV", "0"), ("SFIDSIGN", "N"),
                ("SFIDDESCL", "000")]

    def _data(self, vf):
        nbuf = -(-vf.octets // (self.sdeb - 1))
        return nbuf

    def send_file(self, vf: VirtualFile, source: str):
        self.note(f"queued {source}")
        self.out("SFID", self.sfid_fields(vf))
        self.inn("SFPA", [("SFPAACNT", "0")])
        self.note(f"DATA: {self._data(vf)} exchange buffer(s), {vf.octets} octets", 20, 400)
        self.out("EFID", [("EFIDRCNT", "0"), ("EFIDUCNT", str(vf.octets))])
        self.inn("EFPA", [("EFPACD", "N")])
        self.note("file transferred, awaiting EERP")

    def send_file_refused_at_end(self, vf: VirtualFile, source: str, reason: str, text: str):
        self.note(f"queued {source}")
        self.out("SFID", self.sfid_fields(vf))
        self.inn("SFPA", [("SFPAACNT", "0")])
        self.note(f"DATA: {self._data(vf)} exchange buffer(s), {vf.octets} octets", 20, 400)
        self.out("EFID", [("EFIDRCNT", "0"), ("EFIDUCNT", str(vf.octets))])
        self.inn("EFNA", [("EFNAREAS", reason), ("EFNAREASL", f"{len(text):03d}"),
                          ("EFNAREAST", text)])
        self.note("file refused by partner at end of file")

    def receive_file(self, vf: VirtualFile, saved_as: str):
        self.inn("SFID", self.sfid_fields(vf))
        self.out("SFPA", [("SFPAACNT", "0")])
        self.note(f"DATA: {self._data(vf)} exchange buffer(s), {vf.octets} octets", 20, 400)
        self.inn("EFID", [("EFIDRCNT", "0"), ("EFIDUCNT", str(vf.octets))])
        self.out("EFPA", [("EFPACD", "N")])
        self.note(f"stored as {saved_as}")

    @staticmethod
    def eerp_fields(vf: VirtualFile):
        return [("EERPDSN", vf.dsn), ("EERPDATE", vf.date), ("EERPTIME", vf.time),
                ("EERPUSER", ""), ("EERPDEST", vf.orig), ("EERPORIG", vf.dest),
                ("EERPHSHL", "0"), ("EERPSIGL", "0")]

    def end_normal_by_partner(self):
        """We hand over with CD, partner has nothing to send and ends."""
        self.out("CD")
        self.inn("ESID", [("ESIDREAS", self.ctx.code("OFTP2.ESIDREAS.NORMAL")),
                          ("ESIDREASL", "000")])
        self.note("session closed")

    def end_normal_by_us(self):
        """Partner hands over with CD, we have nothing to send and end."""
        self.inn("CD")
        self.out("ESID", [("ESIDREAS", self.ctx.code("OFTP2.ESIDREAS.NORMAL")),
                          ("ESIDREASL", "000")])
        self.note("session closed")

    def acknowledge_and_close(self, vf: VirtualFile):
        """Partner (Speaker) has sent us a file. It hands over with CD, we
        return the EERP for its file, hand back with CD, and the partner,
        having nothing more to send, ends the session."""
        self.inn("CD")
        self.out("EERP", self.eerp_fields(vf))
        self.inn("RTR")
        self.out("CD")
        self.inn("ESID", [("ESIDREAS", self.ctx.code("OFTP2.ESIDREAS.NORMAL")),
                          ("ESIDREASL", "000")])
        self.note("session closed")

    def responses(self, items):
        """Partner (Speaker) sends EERPs/NERPs; we answer each with RTR."""
        for cmd, fields, note in items:
            self.inn(cmd, fields)
            self.out("RTR")
            if note:
                self.note(note)

    def warn(self, text):
        self.lines.append(f"{self._tick(0, 0)} {self.sid} !! {text}")

    @staticmethod
    def nerp_fields(vf: VirtualFile, creator: str, reason: str, text: str):
        return [("NERPDSN", vf.dsn), ("NERPDATE", vf.date), ("NERPTIME", vf.time),
                ("NERPDEST", vf.orig), ("NERPORIG", vf.dest), ("NERPCREA", creator),
                ("NERPREAS", reason), ("NERPREASL", f"{len(text):03d}"), ("NERPREAST", text),
                ("NERPHSHL", "0"), ("NERPSIGL", "0")]

    def tls_failed(self, at: datetime, sid: str, alert: int, name: str):
        self.blank()
        self.sid = sid
        self.t = at
        self.note(f"session {sid}: TCP connect to {self.remote.host} ({self.remote.ip}) "
                  f"established", 0, 0)
        self.warn(f"TLS handshake failed: remote sent alert {alert} ({name}); connection closed")

    def connect_failed(self, at: datetime, timeout_s: int, retry_s: int):
        self.blank()
        self.lines.append(f"{ts(at)} ----- .. outbound TCP connect to {self.remote.host} "
                          f"({self.remote.ip}) timed out after {timeout_s} s, retry in {retry_s} s")

    def text(self) -> str:
        lines = list(self.lines)
        if any(l.count("??") for l in lines if " [" in l):
            lines.insert(5, "# DRAFT: '??' in a reason code field marks a code not yet verified "
                            "for this evaluation.")
        return "\n".join(lines) + "\n"


def merge_traces(master, logs):
    """Interleave the sessions of several Oftp2Log objects by timestamp into
    master (whose header is kept). Stable for equal timestamps."""
    rows = []
    for i, lg in enumerate(logs):
        for j, line in enumerate(l for l in lg.lines if l and not l.startswith("#")):
            rows.append((line[:23], i, j, line))
    rows.sort()
    master.lines += [r[3] for r in rows]
    return master


# --------------------------------------------------------------------------
# EDIFACT
# --------------------------------------------------------------------------

def interchange(segments) -> str:
    """As transmitted: segments joined by the segment terminator, no line feeds."""
    return "".join(s + "'" for s in segments)


def unb(ctx: Ctx, syntax: str, version: str, sender: str, recipient: str,
        prepared: datetime, ref: str, date_fmt: str = "%y%m%d", tail=None) -> str:
    """tail: optional dict for the elements after 0020, keyed by
    S005, 0026, 0029, 0031, 0032, 0035. Trailing empty elements are omitted."""
    ctx.conv("EDIFACT.LAYOUT.UNB")
    ctx.conv("EDIFACT.UNB.S004_FORMAT_SYNTAX3")
    q = ctx.conv("EDIFACT.0007.MUTUALLY_DEFINED")
    seg = (f"UNB+{syntax}:{version}+{sender}:{q}+{recipient}:{q}"
           f"+{prepared.strftime(date_fmt)}:{prepared.strftime('%H%M')}+{ref}")
    if tail:
        ctx.conv("EDIFACT.LAYOUT.UNB_TAIL")
        vals = [tail.get(k, "") for k in ("S005", "0026", "0029", "0031", "0032", "0035")]
        while vals and vals[-1] == "":
            vals.pop()
        seg += "".join("+" + v for v in vals)
    return seg


def ung(ctx: Ctx, msg_type: str, app_sender: str, app_recipient: str, prepared: datetime,
        group_ref: str) -> str:
    ctx.conv("EDIFACT.LAYOUT.UNG_UNE")
    q = ctx.conv("EDIFACT.0007.MUTUALLY_DEFINED")
    return (f"UNG+{msg_type}+{app_sender}:{q}+{app_recipient}:{q}"
            f"+{prepared.strftime('%y%m%d')}:{prepared.strftime('%H%M')}+{group_ref}+UN+D:96A")


def une(ctx: Ctx, count: int, group_ref: str) -> str:
    ctx.conv("EDIFACT.LAYOUT.UNG_UNE")
    return f"UNE+{count}+{group_ref}"


def unz(ctx: Ctx, count: int, ref: str, groups: bool = False) -> str:
    ctx.conv("EDIFACT.LAYOUT.UNZ")
    if groups:
        ctx.conv("EDIFACT.UNZ.0036_COUNTS_GROUPS")
    return f"UNZ+{count}+{ref}"


def invoic_message(ctx: Ctx, msg_ref: str, inv_no: str, inv_date: datetime,
                   seller: Party, buyer: Party, lines):
    """INVOIC D.96A body. Illustrative only and never the planted fault."""
    ctx.conv("EDIFACT.INVOIC.D96A.BODY")
    segs = [
        f"UNH+{msg_ref}+INVOIC:D:96A:UN",
        f"BGM+380+{inv_no}+9",
        f"DTM+137:{inv_date.strftime('%Y%m%d')}:102",
        f"NAD+SE+++{seller.name.upper()}",
        f"NAD+BY+++{buyer.name.upper()}",
        "CUX+2:EUR:4",
    ]
    total = 0
    for i, (part, qty, price_cents) in enumerate(lines, 1):
        amount = qty * price_cents
        total += amount
        segs += [f"LIN+{i}++{part}:IN", f"QTY+47:{qty}",
                 f"MOA+203:{amount // 100}.{amount % 100:02d}",
                 f"PRI+AAA:{price_cents // 100}.{price_cents % 100:02d}"]
    vat = total * 20 // 100
    gross = total + vat
    segs += ["UNS+S",
             f"MOA+77:{gross // 100}.{gross % 100:02d}",
             "TAX+7+VAT+++:::20+S",
             f"MOA+124:{vat // 100}.{vat % 100:02d}"]
    segs.append(f"UNT+{len(segs) + 1}+{msg_ref}")
    return segs


def contrl_rejecting(ctx: Ctx, own: Party, partner: Party, prepared: datetime,
                     own_ref: str, rejected_ref: str, rej_sender: str, rej_recipient: str,
                     error_key: str, seg_tag: str, position: str) -> str:
    """CONTRL interchange from `own` rejecting interchange `rejected_ref`."""
    q = ctx.conv("EDIFACT.0007.MUTUALLY_DEFINED")
    msg_id = ctx.conv("EDIFACT.CONTRL.MESSAGE_ID_SYNTAX3")
    ctx.conv("EDIFACT.LAYOUT.UCI")
    if position:
        ctx.conv("EDIFACT.S011.POSITION_COUNTING")
    action = ctx.code("EDIFACT.0083.REJECTED")
    error = ctx.code(error_key)
    body = [
        f"UNH+1+{msg_id}",
        f"UCI+{rejected_ref}+{rej_sender}:{q}+{rej_recipient}:{q}+{action}+{error}+{seg_tag}"
        + (f"+{position}" if position else ""),
    ]
    body.append(f"UNT+{len(body) + 1}+1")
    segs = [unb(ctx, "UNOA", "3", own.edi_id, partner.edi_id, prepared, own_ref)] + body + \
           [unz(ctx, 1, own_ref)]
    return interchange(segs)


# --------------------------------------------------------------------------
# Partner agreement
# --------------------------------------------------------------------------

def agreement(sender: Party, receiver: Party, *, effective: str, sdeb: int, cred: int,
              dsn: str, sender_edi_id: str, hub: Party = None, max_messages: int = 1,
              contrl: bool = True, routing_by_unb: bool = False, groups: bool = False,
              extra_sections=()) -> str:
    q = "ZZ"
    lines = [
        "PARTNER AGREEMENT: ELECTRONIC DATA INTERCHANGE",
        f"Between {sender.name} (the Supplier) and {receiver.name} (the Customer)",
        f"Effective {effective}. Synthetic document written for this evaluation.",
        "",
        "1. Transport: OFTP2 (RFC 5024) over TCP/IP with TLS",
        f"   Supplier ODETTE ID (SFIDORIG): {sender.odette_id}",
        f"   Customer ODETTE ID (SFIDDEST): {receiver.odette_id}",
    ]
    if hub:
        lines += [
            f"   Both parties connect to the {hub.name} OFTP2 clearing centre and never",
            "   directly to each other.",
            f"   Clearing centre ODETTE ID (SSIDCODE in the Supplier's sessions): {hub.odette_id}",
            f"   Clearing centre gateway: {hub.host} ({hub.ip})",
            "   The clearing centre forwards virtual files to SFIDDEST unchanged, relays",
            "   EERPs and NERPs back to the originator, and does not read file content.",
        ]
    else:
        lines += [
            f"   Supplier gateway: {sender.host} ({sender.ip})",
            f"   Customer gateway: {receiver.host} ({receiver.ip})",
        ]
    lines += [
        f"   Supplier gateway: {sender.host} ({sender.ip})" if hub else None,
        "   Protocol release level: 5 (OFTP 2.0)",
        f"   Data exchange buffer size (SSIDSDEB): {sdeb}",
        f"   Credit (SSIDCRED): {cred}",
        "   Buffer compression: no. Restart: yes. Secure authentication: no.",
        "   File security and file compression: none (SFIDSEC 00, SFIDCOMP 0).",
        "   Signed EERP: not required (SFIDSIGN N).",
        "   The Customer returns an EERP for every virtual file it accepts.",
        "",
        "2. Virtual files",
        f"   Invoices: one interchange per virtual file, dataset name (SFIDDSN) {dsn}.",
        "   File format U. SFIDDATE and SFIDTIME are set by the Supplier's gateway to",
        "   the date and time the virtual file is made available for transmission.",
        "",
        "3. EDIFACT",
        "   Syntax identifier and version (UNB S001): UNOA, version 3.",
        f"   Supplier interchange sender ID (UNB S002 0004 / 0007): {sender_edi_id} / {q}",
        f"   Customer interchange recipient ID (UNB S003 0010 / 0007): {receiver.edi_id} / {q}",
        "   Messages: INVOIC D.96A, " + ("one message per interchange." if max_messages == 1
                                        else f"up to {max_messages} messages per interchange."),
        "   Interchanges are sent without line feeds between segments.",
    ]
    if routing_by_unb:
        lines += ["   The Customer's gateway routes each interchange on receipt to the receiving",
                  "   plant's translator by the UNB recipient ID."]
    if contrl:
        lines += ["   The Customer's translator returns a CONTRL message for every rejected",
                  "   interchange, as a separate virtual file over the same OFTP2 link."]
    else:
        lines += ["   The Customer does not return CONTRL messages."]
    lines += [
        "",
        "4. Support contacts",
        f"   Supplier EDI desk: {sender.contact}",
        f"   Customer EDI operations: {receiver.contact}",
    ]
    if groups:
        lines.insert(lines.index("   Interchanges are sent without line feeds between segments."),
                     "   Messages are sent in one functional group (UNG/UNE) per interchange.")
    for sec in extra_sections:
        lines += [""] + sec
    return "\n".join(l for l in lines if l is not None) + "\n"

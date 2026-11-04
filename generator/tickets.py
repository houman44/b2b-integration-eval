"""Ticket definitions (hardened, v0.2). Each builder plants exactly one root
cause, adds red herrings that the documents themselves rule out, and returns
the documents plus the planted (reference) answer."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .common import (BACKGROUND, Ctx, Oftp2Log, VirtualFile, agreement, contrl_rejecting,
                     interchange, invoic_message, merge_traces, unb, une, ung, unz)
from .noise import busy_period, status_report


@dataclass
class Bundle:
    narrative: str                 # the ticket text as raised by the sender
    documents: dict                # file name -> text (order matters)
    extracts: list                 # spec extract file names under spec/
    answer: dict                   # planted answer
    rationale: str                 # why the planted answer is the only defensible one
    facts: dict = field(default_factory=dict)  # values the consistency tests check
    titles: dict = field(default_factory=dict)  # per-ticket document title overrides
    value_question: str = ""       # the ticket-specific 'value' key (exact answer)
    value_kind: str = "string"     # int | string | segment (how the grader normalises it)


SPEC_EDIFACT = "unedifact/syntax3_service_extracts.txt"
SDEB, CRED = 4096, 64


def _vf_time(t: datetime, counter: int = 1) -> str:
    return t.strftime("%H%M%S") + f"{counter:04d}"


def _invoice_lines(ctx: Ctx):
    n = ctx.rng.between(1, 3)
    return [(f"P-{ctx.rng.digits(5)}", ctx.rng.between(20, 400), ctx.rng.between(150, 4800))
            for _ in range(n)]


def _at(day: datetime, h_lo, h_hi, rng) -> datetime:
    return day.replace(hour=rng.between(h_lo, h_hi), minute=rng.between(0, 59),
                       second=rng.between(0, 59))


def _secs(rng, lo, hi):
    return timedelta(seconds=rng.between(lo, hi))


def _mins(rng, lo, hi):
    return timedelta(minutes=rng.between(lo, hi), seconds=rng.between(0, 59))


# --------------------------------------------------------------------------
# T1: corrected file resubmitted with the original file's date and time.
# Routed through a clearing centre, so the sender only sees EFPA from the
# hub and, later, a NERP created by the hub on the destination's refusal.
# --------------------------------------------------------------------------

def build_T1(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    h = ctx.hub()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    day1, day2 = datetime(2026, 10, 29), datetime(2026, 10, 30)
    inv0 = rng.between(10000, 80000)
    ref0 = rng.between(1000, 900000)

    def make(inv_no, made, lines, ref, inv_date=None, stamp=None):
        ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, made, f"{ref:06d}")]
                         + invoic_message(ctx, "1", inv_no, inv_date or made, s, r, lines)
                         + [unz(ctx, 1, f"{ref:06d}")])
        st = stamp or made
        vf = VirtualFile(dsn, st.strftime("%Y%m%d"), _vf_time(st), r.odette_id, s.odette_id,
                         len(ic.encode("ascii")))
        return ic, vf

    # Day 1: three invoices, A, B, C. B is the one corrected on day 2.
    tA = _at(day1, 11, 12, rng)
    tB = _at(day1, 13, 14, rng)
    tC = _at(day1, 15, 15, rng)
    inv = [f"INV{inv0 + i}" for i in range(4)]
    linesB = _invoice_lines(ctx)
    icA, vfA = make(inv[0], tA, _invoice_lines(ctx), ref0)
    icB, vfB = make(inv[1], tB, linesB, ref0 + 1)
    icC, vfC = make(inv[2], tC, _invoice_lines(ctx), ref0 + 2)

    # Day 2: new invoice D, then the corrected B. The resubmission builds a new
    # interchange but reuses B's virtual file date and time (planted fault).
    tD = _at(day2, 7, 7, rng)
    tB2 = day2.replace(hour=8, minute=rng.between(30, 50), second=rng.between(0, 59))
    icD, vfD = make(inv[3], tD, _invoice_lines(ctx), ref0 + 3)
    linesB2 = [(p, q + rng.between(5, 40), c) for p, q, c in linesB]
    icB2, vfB2 = make(inv[1], tB2, linesB2, ref0 + 4, inv_date=tB, stamp=tB)
    assert (vfB2.dsn, vfB2.date, vfB2.time) == (vfB.dsn, vfB.date, vfB.time)

    log = Oftp2Log(ctx, s, h, SDEB, CRED)
    sid = rng.between(1000, 8999)
    first = {}       # identity -> (source, sent): the gateway's correlation key
    rows = []        # status report rows for files to this partner
    status = {}

    def outbound(vf, src, when):
        nonlocal sid
        sid += 1
        log.open_outbound(when, f"S{sid}")
        log.send_file(vf, src)
        log.end_normal_by_partner()
        key = (vf.dsn, vf.date, vf.time)
        first.setdefault(key, (src, when))
        status[(src, when)] = "awaiting EERP"
        rows.append([when, r.name, src, vf.octets, None])

    def inbound(items, when):
        nonlocal sid
        sid += 1
        log.open_inbound(when, f"S{sid}")
        log.responses(items)
        log.end_normal_by_us()

    def matched(vf):
        return first[(vf.dsn, vf.date, vf.time)]

    def eerp(vf, at=None):
        src, when = matched(vf)
        status[(src, when)] = "delivered, EERP"
        return ("EERP", Oftp2Log.eerp_fields(vf),
                f"EERP matched to {src} (sent {when.strftime('%d %b %H:%M')}): delivered")

    nerp_text = "NOT DELIVERED - REFUSED BY DESTINATION"

    def nerp(vf):
        return ("NERP", Oftp2Log.nerp_fields(vf, h.odette_id,
                                             ctx.code("OFTP2.NERPREAS.SFNA13_DUPLICATE_FILE"),
                                             nerp_text),
                f"NERP matched to {matched(vf)[0]} (sent {matched(vf)[1].strftime('%d %b %H:%M')}): "
                f"NOT DELIVERED, alert raised")

    def nerp_status(vf):
        status[matched(vf)] = "NOT DELIVERED (NERP)"

    outbound(vfA, f"{inv[0]}.edi", tA + _secs(rng, 20, 80))
    outbound(vfB, f"{inv[1]}.edi", tB + _secs(rng, 20, 80))
    inbound([eerp(vfA)], tB + _mins(rng, 10, 25))
    outbound(vfC, f"{inv[2]}.edi", tC + _secs(rng, 20, 80))
    inbound([eerp(vfB), eerp(vfC)], tC + _mins(rng, 30, 50))
    outbound(vfD, f"{inv[3]}.edi", tD + _secs(rng, 20, 80))
    t_resub1 = tB2 + _secs(rng, 20, 80)
    outbound(vfB2, f"{inv[1]}_corrected.edi", t_resub1)
    inbound([eerp(vfD), nerp(vfB2)], t_resub1 + _mins(rng, 15, 25))
    nerp_status(vfB2)
    t_resub2 = t_resub1 + _mins(rng, 40, 50)
    outbound(vfB2, f"{inv[1]}_corrected.edi", t_resub2)
    inbound([nerp(vfB2)], t_resub2 + _mins(rng, 15, 25))
    nerp_status(vfB2)

    # Busy-day background: the sender's other partners on both days.
    others = ctx.distinct_parties(BACKGROUND, 5, "203.0.113")
    noise_rows = []
    noise1, nsid = busy_period(ctx, s, others, day1, 7, 17, SDEB, CRED, sid + 100, noise_rows)
    noise2, _ = busy_period(ctx, s, others, day2, 6, 9, SDEB, CRED, nsid, noise_rows)
    master = Oftp2Log(ctx, s, h, SDEB, CRED)
    merge_traces(master, [log] + noise1 + noise2)
    for row in rows:
        row[4] = status[(row[2], row[0])]
    report = status_report(f"{s.name}: OFTP2 gateway file status",
                           [tuple(x) for x in rows] + noise_rows,
                           (t_resub2 + timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M"))

    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {h.name} is mixing up our files\n\n"
        f"Yesterday we sent invoice {inv[1]} to {r.name} with the wrong quantities. This "
        f"morning we corrected it and sent it again with the Resubmit function in our OFTP2 "
        f"gateway, twice. Both times the {h.name} clearing centre accepted the file. Now our "
        f"gateway status report shows yesterday's original {inv[1]} as NOT DELIVERED, although "
        f"{r.name} booked it yesterday, and both corrected files are still waiting for an EERP. "
        f"{r.contact} at {r.name} says nothing new has arrived. All our other files today, to "
        f"{r.name} and to our other partners, went through, so our gateway is fine. We think the "
        f"clearing centre is mixing up responses. Please find the root cause and tell us who "
        f"has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Date: 30 Oct 2026 {(t_resub2 + timedelta(minutes=50)).strftime('%H:%M')}\n"
        f"Subject: RE: corrected invoice {inv[1]}\n\n"
        f"Hello,\n\nWe have not received a corrected invoice {inv[1]}. The original {inv[1]} "
        f"arrived yesterday and has been booked, and {inv[3]} arrived this morning. Please "
        f"send the corrected invoice again.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id, hub=h),
        "oftp2_session.log": master.text(),
        "gateway_status.txt": report,
        "interchange.edi": icB2,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s1.5.2_virtual_file_identification.txt",
                  "rfc5024/s4.3.6_end_to_end_response.txt",
                  "rfc5024/s4.3.7_negative_end_response.txt",
                  "rfc5024/s5.3.3_sfid.txt", "rfc5024/s5.3.5_sfna.txt",
                  "rfc5024/s5.3.14_nerp.txt"],
        answer={"cause": "duplicate_virtual_file", "layer": "transport", "owner": "sender",
                "location": ["SFID.SFIDDATE", "SFID.SFIDTIME"], "next_check": "none", "value": f"{vfB.date} {vfB.time}"},
        rationale=(
            f"Both resubmissions carry SFIDDSN {vfB.dsn}, SFIDDATE {vfB.date}, SFIDTIME "
            f"{vfB.time}: the identity of invoice {inv[1]}'s virtual file of 29 Oct, which was "
            f"delivered and acknowledged by EERP. The clearing centre accepted the file (EFPA is "
            f"from the hub, not the destination), forwarded it unchanged, and created a NERP "
            f"(NERPCREA = hub, NERPORIG = destination) with reason 23: the destination refused "
            f"with SFNA 13, duplicate file (RFC 5024 4.3.7 and 5.3.14). RFC 1.5.2: dataset name, "
            f"date and time are assigned by the originator and uniquely identify a file. The "
            f"agreement requires SFIDDATE/SFIDTIME to be the time the file is made available, "
            f"so the corrected file must carry 30 Oct's date and its own time; the agreed dataset "
            f"name stays. The sender's Resubmit function is at fault, not the hub. The status "
            f"report is misleading for the same reason: the gateway correlates responses by "
            f"virtual file identity, so the NERPs for the resubmissions land on the original "
            f"file, and the resubmissions never get a response of their own."),
        facts={"vfB": vfB.__dict__, "vfB2": vfB2.__dict__, "vfD": vfD.__dict__,
               "vfB_src": f"{inv[1]}.edi",
               "hub_id": h.odette_id, "interchange_octets": len(icB2.encode("ascii"))},
        value_question='the SFIDDATE and SFIDTIME of the virtual file that the NERPs in the log refer to, written as "CCYYMMDD HHMMSScccc"',
        value_kind="string",
    )


# --------------------------------------------------------------------------
# E1: UNB 0020 and UNZ 0020 differ only in leading zeros; partner email
# blames the control count and concedes its own upgrade may be at fault.
# --------------------------------------------------------------------------

def build_E1(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    t0 = _at(datetime(2026, 10, 30), 7, 7, rng)
    n = rng.between(100, 9999)
    ref_unb, ref_unz = f"{n:08d}", str(n)            # planted fault
    inv0 = rng.between(10000, 80000)
    nmsg = rng.between(5, 8)
    body = []
    for i in range(nmsg):
        body += invoic_message(ctx, str(i + 1), f"INV{inv0 + i}", t0, s, r, _invoice_lines(ctx))
    gref = f"{rng.between(1, 9999)}"
    ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t0, ref_unb),
                      ung(ctx, "INVOIC", s.edi_id, r.edi_id, t0, gref)] + body
                     + [une(ctx, nmsg, gref), unz(ctx, 1, ref_unz, groups=True)])
    vf = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id,
                     len(ic.encode("ascii")))

    t_contrl = t0 + _mins(rng, 15, 30)
    contrl_ref = f"C{rng.digits(5)}"
    contrl = contrl_rejecting(ctx, r, s, t_contrl, contrl_ref, ref_unb, s.edi_id, r.edi_id,
                              "EDIFACT.0085.REFERENCES_DO_NOT_MATCH", "UNZ", None)
    vf_c = VirtualFile(f"{r.short[:10]}.CONTRL", t_contrl.strftime("%Y%m%d"),
                       _vf_time(t_contrl), s.odette_id, r.odette_id, len(contrl.encode("ascii")))

    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(t0 + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vf, f"INVOICES_{t0.strftime('%Y%m%d')}_BATCH1.edi")
    log.end_normal_by_partner()
    log.open_inbound(t_contrl + _mins(rng, 2, 6), f"S{sid + 1}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vf), None)])
    log.receive_file(vf_c, f"inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi")
    log.acknowledge_and_close(vf_c)

    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} rejects our invoices since their upgrade\n\n"
        f"Since 26 October {r.name} rejects every invoice interchange we send. For months "
        f"before that the same files were accepted, and nothing has changed on our side. "
        f"{r.name} upgraded their translator on 26 October and even say themselves it may be "
        f"their problem. Our gateway shows this morning's batch delivered with an EERP. "
        f"Please find the root cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: Rejected interchange this morning\n\n"
        f"Hello,\n\nOur translator rejected your interchange of this morning; the CONTRL we "
        f"returned over OFTP2 is copied below. As far as we can tell it is about your UNZ: "
        f"you sent us {nmsg} invoices but your UNZ control count says 1. This started after "
        f"we upgraded "
f"our translator on 26 October, so it may be on our side, but please check your files "
        f"too.\n\nRegards,\n{r.contact}\n\n"
        f"--- CONTRL as received by {s.name} (inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi) ---\n"
        + contrl)
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id, max_messages=50,
                                           groups=True),
        "oftp2_session.log": log.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "interchange_control_reference_mismatch", "layer": "envelope",
                "owner": "sender", "location": ["UNB.0020", "UNZ.0020"], "next_check": "none", "value": str(nmsg)},
        rationale=(
            f"UNB 0020 is '{ref_unb}' and UNZ 0020 is '{ref_unz}'. 0020 is an alphanumeric "
            f"reference and the two must be identical; they differ in leading zeros, so they do "
            f"not match. The control count is right: with a functional group, UNZ 0036 counts "
            f"groups, not messages (1 group, UNE 0060 = {nmsg} messages), so the partner's reading "
            f"of its own CONTRL is wrong; the CONTRL error code (references do "
            f"not match) and UCI 0020 '{ref_unb}' point at the references. The receiver's upgrade "
            f"only made its translator compare the references strictly: the sender's envelope was "
            f"always non-compliant, so the sender must fix its translator. EERP only shows "
            f"delivery to the final recipient's OFTP2 location."),
        facts={"unb_ref": ref_unb, "unz_ref": ref_unz, "messages": nmsg, "group_ref": gref,
               "interchange_octets": len(ic.encode("ascii")), "vf": vf.__dict__},
        value_question='the number of INVOIC messages in the interchange, as a plain integer',
        value_kind="int",
    )


# --------------------------------------------------------------------------
# R1: every symptom is at the transport layer (EFNA "transmission error" at end
# of file, a connect timeout, a certificate warning, SSID values that differ
# from the agreement). The real cause: since the sender's upgrade, its UNB sets
# the test indicator (0035 = 1, the 11th element, after five empty ones), so the
# receiver's production gateway refuses the files. No CONTRL exists.
# --------------------------------------------------------------------------

def build_R1(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    cert_expiry = "2026-11-04T23:59:59Z"
    offer_sdeb, offer_cred = 16384, 128            # red herring: negotiated down by the Responder
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    t = _at(datetime(2026, 10, 30), 6, 6, rng)
    inv_no = f"INV{rng.digits(5)}"
    lines = _invoice_lines(ctx)
    text = "TRANSMISSION ERROR - PLEASE RETRANSMIT"
    last = None
    for attempt in range(3):
        ref = f"{rng.between(100, 999999):06d}"
        ic = interchange(
            [unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t, ref, tail={"0035": "1"})]  # planted fault
            + invoic_message(ctx, "1", inv_no, t, s, r, lines)
            + [unz(ctx, 1, ref)])
        vf = VirtualFile(dsn, t.strftime("%Y%m%d"), _vf_time(t, attempt + 1), r.odette_id,
                         s.odette_id, len(ic.encode("ascii")))
        last = (vf, ic, ref)
        if attempt == 1:
            log.connect_failed(t + timedelta(seconds=5), 30, 120)
            sid += 1
            t = t + timedelta(seconds=155)
        sid += 1
        log.open_outbound(t + _secs(rng, 10, 40), f"S{sid}", offer_sdeb, offer_cred)
        log.warn(f"local TLS certificate CN={s.host} expires {cert_expiry} (5 days)")
        src = f"{inv_no}.edi" if attempt == 0 else f"{inv_no}.edi (retransmission {attempt})"
        log.send_file_refused_at_end(vf, src, ctx.code("OFTP2.EFNAREAS.UNSPECIFIED"), text)
        log.end_normal_by_partner()
        t = t + _mins(rng, 25, 45)

    vf, ic, ref = last
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: TRANSMISSION ERROR on every invoice to {r.name}\n\n"
        f"Since 15 October every invoice we send to {r.name} is refused with 'TRANSMISSION "
        f"ERROR - PLEASE RETRANSMIT'. We retransmitted invoice {inv_no} twice this morning "
        f"with the same result, and one connection attempt timed out. {r.name} say our OFTP2 "
        f"set-up or our certificate is faulty. Our network team says the link is fine. On 14 "
        f"October we moved to a new release of our EDI suite (OFTP2 gateway and translator); "
        f"IT tells me the configuration and the maps were migrated unchanged. Please find the "
        f"root cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: TRANSMISSION ERROR\n\n"
        f"Hello,\n\nOur gateway has refused your files with a transmission error since 15 "
        f"October. Your sessions also no longer offer the buffer size and credit in our "
        f"agreement. Please check your OFTP2 set-up and the TLS certificate on your side; our "
        f"monitoring shows it expires on 4 November. Files from our other suppliers arrive "
        f"normally.\n\nRegards,\n{r.contact}\n")
    test_id = f"O0013{r.short[:10]}TEST"
    testing = [
        "5. Testing",
        f"   Test files go to the Customer's test gateway, ODETTE ID {test_id}; production",
        "   files go to the production ODETTE ID in section 1. UNB 0035 (test indicator)",
        "   is set to 1 in test interchanges only. The production gateway accepts",
        "   production interchanges only.",
    ]
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id, contrl=False,
                                           routing_by_unb=True, extra_sections=[testing]),
        "oftp2_session.log": log.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s5.3.2_ssid.txt", "rfc5024/s5.3.8_efid.txt",
                  "rfc5024/s5.3.10_efna.txt", SPEC_EDIFACT],
        answer={"cause": "test_indicator_mismatch", "layer": "envelope",
                "owner": "sender", "location": ["UNB.0035"], "next_check": "none", "value": ic.split("'")[0].removesuffix("++++++1") + "'"},
        rationale=(
            f"The transfers themselves are complete: SFPA, all data, EFID with the exact unit "
            f"count, then EFNA with an unspecified reason, so the receiver refused the content at "
            f"end of file. TLS is established in every session and the certificate is valid "
            f"until {cert_expiry}. The sender offers SSIDSDEB {offer_sdeb} and SSIDCRED "
            f"{offer_cred}, but the Responder answers {SDEB} and {CRED:03d} and RFC 5024 5.3.2 "
            f"makes the smaller values apply, so the session parameters are as agreed. The "
            f"production gateway inspects the UNB on receipt. The UNB ends '+{ref}++++++1': after "
            f"0020 come S005, 0026, 0029, 0031 and 0032 (all empty) and then 0035, so the '1' is "
            f"the test indicator, not an acknowledgement request (0031). Section 5: test "
            f"interchanges go to the test gateway and the production gateway accepts production "
            f"interchanges only. All other UNB values match the agreement. The refusals start the "
            f"day after the sender's upgrade. The sender must clear 0035 in its production "
            f"UNB."),
        facts={"unb_ref": ref, "interchange_octets": len(ic.encode("ascii")),
               "vf": vf.__dict__, "offer": (offer_sdeb, offer_cred)},
        value_question='the UNB segment exactly as the sender should transmit it for this interchange, from "UNB" up to and including its segment terminator',
        value_kind="segment",
    )


# --------------------------------------------------------------------------
# E3: the sender switched to UNOC on 28 Oct under an amendment that only takes
# effect on 1 Nov. The sender cites the signed amendment; the content is plain
# ASCII, so UNOC looks harmless.
# --------------------------------------------------------------------------

def build_E3(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    t0 = _at(datetime(2026, 10, 30), 7, 9, rng)
    ref = f"{rng.between(100, 999999):06d}"
    inv_no = f"INV{rng.digits(5)}"
    ic = interchange([unb(ctx, "UNOC", "3", s.edi_id, r.edi_id, t0, ref)]      # planted fault
                     + invoic_message(ctx, "1", inv_no, t0, s, r, _invoice_lines(ctx))
                     + [unz(ctx, 1, ref)])
    vf = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id,
                     len(ic.encode("ascii")))
    t_contrl = t0 + _mins(rng, 10, 25)
    contrl = contrl_rejecting(ctx, r, s, t_contrl, f"C{rng.digits(5)}", ref, s.edi_id, r.edi_id,
                              "EDIFACT.0085.SYNTAX_LEVEL_NOT_SUPPORTED", "UNB", None)
    vf_c = VirtualFile(f"{r.short[:10]}.CONTRL", t_contrl.strftime("%Y%m%d"),
                       _vf_time(t_contrl), s.odette_id, r.odette_id, len(contrl.encode("ascii")))
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(t0 + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vf, f"{inv_no}.edi")
    log.end_normal_by_partner()
    log.open_inbound(t_contrl + _mins(rng, 2, 6), f"S{sid + 1}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vf), None)])
    log.receive_file(vf_c, f"inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi")
    log.acknowledge_and_close(vf_c)

    amendment = [
        "5. Amendment 3 (signed by both parties on 20 October 2026)",
        "   With effect from 1 November 2026 the syntax identifier in UNB S001 changes",
        "   from UNOA to UNOC, syntax version 3 unchanged, so that plant names and",
        "   addresses with accented characters can be exchanged. All other terms of",
        "   section 3 are unchanged.",
    ]
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Date: 30 Oct 2026\n"
        f"Subject: {r.name} rejects all our invoices since we implemented amendment 3\n\n"
        f"Amendment 3 to our agreement with {r.name}, signed by both sides, moves us to "
        f"UNOC. We implemented it on 28 October. Since then {r.name} rejects every "
        f"interchange we send with a syntax error. Our invoices contain only plain characters "
        f"anyway, so even a UNOA translator should be able to read them. It looks to us as if "
        f"{r.name} have not implemented their side of the amendment. Please find the root "
        f"cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Date: 30 Oct 2026\n"
        f"Subject: Rejected interchanges since 28 October\n\n"
        f"Hello,\n\nYour interchanges since 28 October are rejected by our translator with "
        f"a syntax error. The CONTRL for this morning's interchange is copied below. Please "
        f"check and resend.\n\nRegards,\n{r.contact}\n\n"
        f"--- CONTRL as received by {s.name} (inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi) ---\n"
        + contrl)
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id,
                                           extra_sections=[amendment]),
        "oftp2_session.log": log.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "syntax_identifier_not_agreed", "layer": "envelope", "owner": "sender",
                "location": ["UNB.S001.0001"], "next_check": "none", "value": ref},
        rationale=(
            "Amendment 3 changes UNB S001 to UNOC only with effect from 1 November 2026. On 30 "
            "October the agreed syntax identifier is still UNOA (section 3), so the sender's "
            "UNOC interchanges, sent since 28 October, use a syntax identifier that is not yet "
            "agreed, and the receiver's CONTRL rejects them at UNB. The receiver is behaving as "
            "agreed and the agreement is consistent; the sender switched four days early and "
            "must send UNOA until 1 November. That the content is plain ASCII does not matter: "
            "the declared syntax identifier is what the receiver checks. Only S001 0001 must "
            "change; the version (0002) is 3 under both."),
        facts={"syntax": "UNOC", "interchange_octets": len(ic.encode("ascii")), "vf": vf.__dict__},
        value_question='the interchange control reference of the interchange that the CONTRL rejects, exactly as it appears in the rejected interchange',
        value_kind="string",
    )


# --------------------------------------------------------------------------
# T2: after a line drop the sender restarts a 48 MB file with SFIDREST in
# octets instead of 1K blocks, then resumes from the receiver's confirmed
# count read as octets. The receiver ends up with the wrong number of octets.
# --------------------------------------------------------------------------

def build_T2(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVBATCH"
    total = 48 * 1024 * 1024                       # 50,331,648 octets
    blocks_total = total // 1024                   # 49,152 blocks
    held_blocks = rng.between(26, 34) * 1024       # what the receiver holds after the drop
    sent_before = held_blocks * 1024               # octets sent before the drop (all acknowledged)
    nmsg = rng.between(29000, 33000)
    t0 = datetime(2026, 10, 30, 2, rng.between(5, 20), rng.between(0, 59))
    ref = f"{rng.between(100, 999999):06d}"
    head = [unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t0, ref)]
    for i in range(2):
        head += invoic_message(ctx, str(i + 1), f"INV{rng.digits(5)}", t0, s, r, _invoice_lines(ctx))
    excerpt = interchange(head) + f"\n[... {nmsg - 3} further INVOIC messages not shown ...]\n" + \
        interchange(invoic_message(ctx, str(nmsg), f"INV{rng.digits(5)}", t0, s, r,
                                   _invoice_lines(ctx)) + [unz(ctx, nmsg, ref)])
    vf = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id, total)

    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    sid0 = sid
    # Session 1: interrupted.
    log.open_outbound(t0 + _secs(rng, 30, 90), f"S{sid}")
    log.note(f"queued INVOICES_{t0.strftime('%Y%m%d')}_NIGHT.edi")
    log.out("SFID", Oftp2Log.sfid_fields(vf))
    log.inn("SFPA", [("SFPAACNT", "0")])
    log.note(f"DATA: transfer started, {total} octets to send, credit window {CRED}")
    secs = rng.between(240, 420)
    log.t += timedelta(seconds=secs)
    log.note(f"DATA: {sent_before} octets sent, CDT received for every credit window", 0, 0)
    t_reset = log.t
    log.warn("TCP connection reset by peer")
    log.note(f"session aborted, file incomplete, restart position saved: {sent_before}")
    # Session 2: restart.
    sid += 1
    t1 = log.t + _secs(rng, 90, 200)
    log.open_outbound(t1, f"S{sid}")
    fields = Oftp2Log.sfid_fields(vf)
    fields = [(k, f"{sent_before:017d}" if k == "SFIDREST" else v) for k, v in fields]   # planted fault
    log.note("restarting interrupted file")
    log.out("SFID", fields)
    log.inn("SFPA", [("SFPAACNT", str(held_blocks))])
    resent = total - held_blocks
    log.note(f"restart accepted by partner, sending remaining {resent} octets")
    log.t += timedelta(seconds=rng.between(300, 500))
    log.note(f"DATA: {resent} octets sent", 0, 0)
    log.out("EFID", [("EFIDRCNT", "0"), ("EFIDUCNT", str(total))])
    reason_text = "BYTE COUNT MISMATCH"
    log.inn("EFNA", [("EFNAREAS", ctx.code("OFTP2.EFNAREAS.INVALID_BYTE_COUNT")),
                     ("EFNAREASL", f"{len(reason_text):03d}"), ("EFNAREAST", reason_text)])
    log.note("file refused by partner at end of file")
    log.end_normal_by_partner()
    # Session 3: operator sends the whole file again as a new virtual file: fine.
    t2 = datetime(2026, 10, 30, 6, rng.between(5, 30), rng.between(0, 59))
    vf2 = VirtualFile(dsn, t2.strftime("%Y%m%d"), _vf_time(t2), r.odette_id, s.odette_id, total)
    sid += 1
    log.open_outbound(t2 + _secs(rng, 30, 90), f"S{sid}")
    log.note(f"queued INVOICES_{t0.strftime('%Y%m%d')}_NIGHT.edi (manual resend)")
    log.out("SFID", Oftp2Log.sfid_fields(vf2))
    log.inn("SFPA", [("SFPAACNT", "0")])
    log.t += timedelta(seconds=rng.between(700, 900))
    log.note(f"DATA: {total} octets sent", 0, 0)
    log.out("EFID", [("EFIDRCNT", "0"), ("EFIDUCNT", str(total))])
    log.inn("EFPA", [("EFPACD", "N")])
    log.note("file transferred, awaiting EERP")
    log.end_normal_by_partner()
    sid += 1
    log.open_inbound(log.t + _mins(rng, 20, 40), f"S{sid}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vf2),
                    f"EERP matched to INVOICES_{t0.strftime('%Y%m%d')}_NIGHT.edi (manual resend): "
                    f"delivered")])
    log.end_normal_by_us()
    restart_sid = f"S{sid0 + 1}"

    # The same network blip hits a V-format transfer to another partner, whose
    # restart (counted in records) works: the sender's evidence that "our
    # restart is fine".
    others = ctx.distinct_parties(BACKGROUND, 5, "203.0.113")
    p2 = others[0]
    lrecl = 2000
    recs_total = rng.between(14000, 20000)
    octets2 = recs_total * rng.between(700, 1900)
    recs_sent = rng.between(recs_total // 3, recs_total // 2)
    t_p2 = t0 + _secs(rng, 40, 100)
    vf_p2 = VirtualFile(f"{s.short[:10]}.DESADVB", t_p2.strftime("%Y%m%d"), _vf_time(t_p2),
                        p2.odette_id, s.odette_id, octets2)

    def vfields(vfx, rest):
        return [(k, ("V" if k == "SFIDFMT" else f"{lrecl:05d}" if k == "SFIDLRECL"
                     else f"{rest:017d}" if k == "SFIDREST" else v))
                for k, v in Oftp2Log.sfid_fields(vfx)]

    lp = Oftp2Log(ctx, s, p2, SDEB, CRED)
    lp.open_outbound(t_p2 + _secs(rng, 20, 60), f"S{sid0 + 50}")
    src2 = f"DESADV_{p2.short}_{t_p2.strftime('%Y%m%d')}_NIGHT.edi"
    lp.note(f"queued {src2}")
    lp.out("SFID", vfields(vf_p2, 0))
    lp.inn("SFPA", [("SFPAACNT", "0")])
    lp.note(f"DATA: transfer started, {recs_total} records to send, credit window {CRED}")
    lp.t = t_reset
    lp.note(f"DATA: {recs_sent} records sent, CDT received for every credit window", 0, 0)
    lp.warn("TCP connection reset by peer")
    lp.note(f"session aborted, file incomplete, restart position saved: {recs_sent}")
    lp2 = Oftp2Log(ctx, s, p2, SDEB, CRED)
    lp2.open_outbound(t_reset + _secs(rng, 100, 260), f"S{sid0 + 51}")
    lp2.note("restarting interrupted file")
    lp2.out("SFID", vfields(vf_p2, recs_sent))
    lp2.inn("SFPA", [("SFPAACNT", str(recs_sent))])
    lp2.note(f"restart accepted by partner, sending remaining {recs_total - recs_sent} records")
    lp2.t += timedelta(seconds=rng.between(200, 400))
    lp2.note(f"DATA: {recs_total - recs_sent} records sent", 0, 0)
    lp2.out("EFID", [("EFIDRCNT", str(recs_total)), ("EFIDUCNT", str(octets2))])
    lp2.inn("EFPA", [("EFPACD", "N")])
    lp2.note("file transferred, awaiting EERP")
    lp2.end_normal_by_partner()
    lp3 = Oftp2Log(ctx, s, p2, SDEB, CRED)
    t_e2 = lp2.t + _mins(rng, 15, 40)
    lp3.open_inbound(t_e2, f"S{sid0 + 52}")
    lp3.responses([("EERP", Oftp2Log.eerp_fields(vf_p2),
                    f"EERP matched to {src2}: delivered")])
    lp3.end_normal_by_us()

    noise_rows = [(t_p2, p2.name, src2, octets2, f"delivered after restart, EERP {t_e2.strftime('%d %b %H:%M')}"),
                  (t0, r.name, f"INVOICES_{t0.strftime('%Y%m%d')}_NIGHT.edi", total,
                   "REFUSED at end of file after restart (EFNA)"),
                  (t2, r.name, f"INVOICES_{t0.strftime('%Y%m%d')}_NIGHT.edi (manual resend)", total,
                   "delivered, EERP")]
    noise, _ = busy_period(ctx, s, others[1:], datetime(2026, 10, 30), 5, 8, SDEB, CRED,
                           sid0 + 100, noise_rows)
    master = Oftp2Log(ctx, s, r, SDEB, CRED)
    merge_traces(master, [log, lp, lp2, lp3] + noise)
    report = status_report(f"{s.name}: OFTP2 gateway file status", noise_rows,
                           "2026-10-30 09:00")

    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: restarted transfers to {r.name} always fail\n\n"
        f"Our nightly invoice batch to {r.name} is about 48 MB. Whenever the line drops "
        f"during the night and our gateway restarts the transfer, {r.name} refuses the file at "
        f"the end with 'BYTE COUNT MISMATCH'. When we send the whole file again from the start "
        f"it always goes through. It happened again last night: the same line drop also "
        f"interrupted our nightly DESADV batch to {{P2}}, and that one restarted and was "
        f"delivered without a problem, so our gateway's restart works. Restart is switched on "
        f"in the agreement, so {r.name}'s restart support must be broken. Please find the root "
        f"cause and tell us who has to fix it.\n").replace("{P2}", p2.name)
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: restarted transfers\n\n"
        f"Hello,\n\nWe see the byte count errors on your restarted transfers. Restarted "
        f"transfers from our other suppliers complete normally, and your 06:00 resend arrived "
        f"fine. Please check your gateway.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id,
                                           max_messages=50000).replace(
            "one interchange per virtual file, dataset name (SFIDDSN)",
            "nightly batch, one interchange per virtual file, dataset name (SFIDDSN)"),
        "oftp2_session.log": master.text(),
        "gateway_status.txt": report,
        "interchange.edi": excerpt,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s1.5.4_restart.txt", "rfc5024/s4.3.3_restart_facilities.txt",
                  "rfc5024/s5.3.3_sfid.txt", "rfc5024/s5.3.4_sfpa.txt",
                  "rfc5024/s5.3.8_efid.txt", "rfc5024/s5.3.10_efna.txt"],
        answer={"cause": "restart_position_invalid", "layer": "transport", "owner": "sender",
                "location": ["SFID.SFIDREST"], "next_check": "none", "value": str(sent_before)},
        rationale=(
            f"The file is format U, so SFIDREST is a file offset in 1K blocks (RFC 5024 1.5.4 and "
            f"5.3.3). After the drop the sender had sent {sent_before} octets = {held_blocks} "
            f"blocks, but its restart SFID carries SFIDREST {sent_before}, an octet count, i.e. "
            f"{sent_before} blocks, far beyond the {blocks_total}-block file. The receiver "
            f"correctly answers SFPAACNT {held_blocks} (lower than or equal to the restart count, "
            f"5.3.4), meaning it holds {held_blocks} blocks. The sender then reads that as octets "
            f"and sends the remaining {resent} octets from octet {held_blocks}, so the receiver "
            f"ends with {sent_before + resent} octets against EFIDUCNT {total} and refuses with "
            f"EFNA invalid byte count. Full resends work because no restart is involved. The "
            f"sender's gateway must express SFIDREST (and read SFPAACNT) in 1K blocks. The "
            f"restart to {p2.name} worked because that file is format V, where the restart "
            f"position is a record count, which the sender's gateway gets right."),
        facts={"total": total, "held_blocks": held_blocks, "sent_before": sent_before,
               "resent": resent, "interchange_octets": total, "excerpt": True,
               "restart_sid": restart_sid, "dest": r.odette_id, "p2_dest": p2.odette_id},
        titles={"interchange.edi": "EDIFACT interchange the ticket is about (excerpt of the "
                                   "start and end, as transmitted)"},
        value_question='how many octets of the file the receiver held from the interrupted transfer when the restart began, as a plain integer',
        value_kind="int",
    )


# --------------------------------------------------------------------------
# U1 (probe): a brand-new file is refused as a duplicate. The sender runs two
# gateway nodes on one ODETTE ID and shared queue, and the trace is from gw1
# only. Either gw2 sent the same virtual file first (sender fault) or the
# receiver's duplicate check is wrong (receiver fault, e.g. matching on dataset
# name and date only, which today's 07:xx invoice would trigger). Nothing in
# the documents decides between them.
# --------------------------------------------------------------------------

def build_U1(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    day = datetime(2026, 10, 30)
    tA = _at(day, 7, 7, rng)
    tB = day.replace(hour=9, minute=rng.between(5, 25), second=rng.between(0, 59))
    inv0 = rng.between(10000, 80000)
    icA = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, tA, f"{inv0:06d}")]
                      + invoic_message(ctx, "1", f"INV{inv0}", tA, s, r, _invoice_lines(ctx))
                      + [unz(ctx, 1, f"{inv0:06d}")])
    icB = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, tB, f"{inv0 + 1:06d}")]
                      + invoic_message(ctx, "1", f"INV{inv0 + 1}", tB, s, r, _invoice_lines(ctx))
                      + [unz(ctx, 1, f"{inv0 + 1:06d}")])
    vfA = VirtualFile(dsn, tA.strftime("%Y%m%d"), _vf_time(tA), r.odette_id, s.odette_id,
                      len(icA.encode("ascii")))
    vfB = VirtualFile(dsn, tB.strftime("%Y%m%d"), _vf_time(tB), r.odette_id, s.odette_id,
                      len(icB.encode("ascii")))
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(tA + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vfA, f"INV{inv0}.edi")
    log.end_normal_by_partner()
    log.open_inbound(tA + _mins(rng, 15, 30), f"S{sid + 1}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vfA), f"EERP matched to INV{inv0}.edi: delivered")])
    log.end_normal_by_us()
    text = "DUPLICATE FILE"
    for k, start in enumerate([tB + _secs(rng, 20, 80), tB + _mins(rng, 25, 35)]):
        log.open_outbound(start, f"S{sid + 2 + k}")
        log.note(f"queued INV{inv0 + 1}.edi" + (" (retry)" if k else ""))
        log.out("SFID", Oftp2Log.sfid_fields(vfB))
        log.inn("SFNA", [("SFNAREAS", ctx.code("OFTP2.SFNAREAS.DUPLICATE_FILE")), ("SFNARRTR", "N"),
                         ("SFNAREASL", f"{len(text):03d}"), ("SFNAREAST", text)])
        log.note("file refused by partner")
        log.end_normal_by_partner()
    others = ctx.distinct_parties(BACKGROUND, 4, "203.0.113")
    noise_rows = []
    noise, _ = busy_period(ctx, s, others, day, 6, 9, SDEB, CRED, sid + 100, noise_rows)
    master = Oftp2Log(ctx, s, r, SDEB, CRED)
    master.lines[0] = master.lines[0] + ", node gw1"
    merge_traces(master, [log] + noise)

    cluster = [
        "5. Supplier gateway set-up",
        "   The Supplier runs two OFTP2 gateway nodes, gw1 and gw2, active-active. Both use",
        "   the Supplier ODETTE ID and certificate above and take files from one shared",
        "   outbound queue; either node may transmit any file.",
    ]
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} refuses a brand-new invoice as a duplicate\n\n"
        f"This morning {r.name} refused invoice INV{inv0 + 1} with 'DUPLICATE FILE', twice. It is "
        f"a brand-new invoice, created at {tB.strftime('%H:%M')} today, and our gateway trace "
        f"(attached, from gw1) shows it was never sent before. Our earlier invoice today went "
        f"through. Their duplicate check must be broken. Please find the root cause and tell us "
        f"who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: duplicate file\n\n"
        f"Hello,\n\nOur gateway refused the file as a duplicate. We have not changed "
        f"anything on our side. Please check.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id,
                                           extra_sections=[cluster]),
        "oftp2_session.log": master.text(),
        "interchange.edi": icB,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s1.5.2_virtual_file_identification.txt", "rfc5024/s5.3.3_sfid.txt",
                  "rfc5024/s5.3.5_sfna.txt"],
        answer={"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
                "location": ["UNDETERMINED"],
                "next_check": ["request_other_gateway_node_trace", "request_receiver_gateway_log"],
                "value": vfB.time},
        rationale=(
            f"The receiver refuses virtual file {vfB.dsn} {vfB.date} {vfB.time} as a duplicate "
            f"(SFNA 13). gw1 never sent it before, but gw2 shares the ODETTE ID and the outbound "
            f"queue and its trace is not provided: if gw2 transmitted the same virtual file first, "
            f"the receiver is right and the sender's cluster sent it twice. If gw2 did not, the "
            f"receiver's duplicate check is wrong (for example it matches dataset name and date "
            f"only, and today's {tA.strftime('%H:%M')} invoice has the same dataset name and "
            f"date). The documents fit both. gw2's trace, or the receiver's gateway log showing "
            f"which earlier file it matched, decides."),
        facts={"vfA": vfA.__dict__, "vfB": vfB.__dict__, "interchange_octets": None},
        value_question="the SFIDTIME of the virtual file the receiver refused",
        value_kind="string",
    )


# --------------------------------------------------------------------------
# U2 (probe): files refused with EFNA "transmission error" at end of file. The
# archived interchange is flawless, but the agreement says the sender's suite
# applies transmission rules to each file after it is archived. Either those
# rules damage the file (sender) or the receiver's gateway has a fault
# (receiver). Nothing in the documents decides between them.
# --------------------------------------------------------------------------

def build_U2(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    t = _at(datetime(2026, 10, 30), 6, 6, rng)
    inv_no = f"INV{rng.digits(5)}"
    text = "TRANSMISSION ERROR - PLEASE RETRANSMIT"
    lines = _invoice_lines(ctx)
    for attempt in range(2):
        ref = f"{rng.between(100, 999999):06d}"
        ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t, ref)]
                         + invoic_message(ctx, "1", inv_no, t, s, r, lines) + [unz(ctx, 1, ref)])
        vf = VirtualFile(dsn, t.strftime("%Y%m%d"), _vf_time(t, attempt + 1), r.odette_id,
                         s.odette_id, len(ic.encode("ascii")))
        sid += 1
        log.open_outbound(t + _secs(rng, 10, 40), f"S{sid}")
        src = f"{inv_no}.edi" if attempt == 0 else f"{inv_no}.edi (retransmission)"
        log.send_file_refused_at_end(vf, src, ctx.code("OFTP2.EFNAREAS.UNSPECIFIED"), text)
        log.end_normal_by_partner()
        t = t + _mins(rng, 30, 50)
    others = ctx.distinct_parties(BACKGROUND, 4, "203.0.113")
    noise, _ = busy_period(ctx, s, others, datetime(2026, 10, 30), 5, 8, SDEB, CRED, sid + 100, [])
    master = Oftp2Log(ctx, s, r, SDEB, CRED)
    merge_traces(master, [log] + noise)

    rules = [
        "5. Supplier transmission rules",
        "   The Supplier's EDI suite applies the partner profile's transmission rules to each",
        "   file at the moment of transmission (for example UNB routing values). The",
        "   Supplier's archive keeps each interchange as the translator produced it, before",
        "   those rules are applied.",
    ]
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} refuses our invoices with TRANSMISSION ERROR\n\n"
        f"Since 28 October {r.name} refuses our invoices at the end of the transfer with "
        f"'TRANSMISSION ERROR - PLEASE RETRANSMIT'. I attach this morning's invoice {inv_no} "
        f"from our archive: the interchange is perfect, every UNB value matches the agreement. "
        f"Our files to our other partners are delivered. The fault must be in {r.name}'s "
        f"gateway. Please find the root cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: TRANSMISSION ERROR\n\n"
        f"Hello,\n\nOur gateway refuses your files at end of file. Please check your side and "
        f"retransmit.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id, contrl=False,
                                           routing_by_unb=True, extra_sections=[rules]),
        "oftp2_session.log": master.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s5.3.8_efid.txt", "rfc5024/s5.3.10_efna.txt", SPEC_EDIFACT],
        answer={"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
                "location": ["UNDETERMINED"],
                "next_check": ["request_transmitted_copy", "request_receiver_gateway_log"],
                "value": str(vf.octets)},
        rationale=(
            "The receiver's gateway, which routes by UNB, refuses each complete transfer at end "
            "of file with an unspecified reason. The interchange provided is the archived copy, "
            "and section 5 says the sender's transmission rules change files after archiving, "
            "so the archived UNB proves nothing about the transmitted one. Either a transmission "
            "rule damages the file (sender) or the receiver's gateway has a fault (receiver); "
            "the same octet count fits both. The transmitted copy, or the receiver's gateway "
            "log for the refusal, decides."),
        facts={"interchange_octets": len(ic.encode("ascii")), "vf": vf.__dict__},
        value_question="the number of octets the sender's gateway reported in its last EFID, as a plain integer",
        titles={"interchange.edi": "EDIFACT interchange from the sender's archive"},
        value_kind="int",
    )


# --------------------------------------------------------------------------
# U3 (probe): a file accepted by the clearing centre gets no EERP within the
# agreed two hours, and the partner's accounts payable team has not seen it.
# Either the clearing centre has not delivered it (intermediary) or the
# Customer received it and has not processed or acknowledged it (receiver).
# The hub delivers other files fine, which decides nothing about this one.
# --------------------------------------------------------------------------

def build_U3(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    h = ctx.hub()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    day = datetime(2026, 10, 30)
    tX = _at(day, 7, 7, rng)
    inv_no = f"INV{rng.digits(5)}"
    ref = f"{rng.between(100, 999999):06d}"
    ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, tX, ref)]
                     + invoic_message(ctx, "1", inv_no, tX, s, r, _invoice_lines(ctx))
                     + [unz(ctx, 1, ref)])
    vf = VirtualFile(dsn, tX.strftime("%Y%m%d"), _vf_time(tX), r.odette_id, s.odette_id,
                     len(ic.encode("ascii")))
    log = Oftp2Log(ctx, s, h, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(tX + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vf, f"{inv_no}.edi")
    log.end_normal_by_partner()
    # Other files through the same hub, to another destination, are acknowledged.
    others = ctx.distinct_parties(BACKGROUND, 5, "203.0.113")
    via_hub = others[0]
    logs = [log]
    for k in range(3):
        t = _at(day, 6 + k, 6 + k, rng)
        vfo = VirtualFile(f"{s.short[:10]}.DESADV", t.strftime("%Y%m%d"), _vf_time(t),
                          via_hub.odette_id, s.odette_id, rng.between(900, 40000))
        lo = Oftp2Log(ctx, s, h, SDEB, CRED)
        lo.open_outbound(t + _secs(rng, 20, 80), f"S{sid + 10 + 2 * k}")
        src = f"DESADV_{via_hub.short}_{t.strftime('%H%M%S')}.edi"
        lo.send_file(vfo, src)
        lo.end_normal_by_partner()
        le = Oftp2Log(ctx, s, h, SDEB, CRED)
        le.open_inbound(lo.t + _mins(rng, 10, 40), f"S{sid + 11 + 2 * k}")
        le.responses([("EERP", Oftp2Log.eerp_fields(vfo), f"EERP matched to {src}: delivered")])
        le.end_normal_by_us()
        logs += [lo, le]
    noise, _ = busy_period(ctx, s, others[1:], day, 6, 10, SDEB, CRED, sid + 100, [])
    master = Oftp2Log(ctx, s, h, SDEB, CRED)
    merge_traces(master, logs + noise)
    now = day.replace(hour=10, minute=rng.between(35, 55))
    master.lines.append(f"{now.strftime('%Y-%m-%d %H:%M:%S')}.000 ----- .. housekeeping: 1 file "
                        f"to {r.odette_id} without EERP after 2 h ({inv_no}.edi)")

    sla = [
        "5. End-to-end responses",
        "   The Customer returns the EERP for each virtual file within two hours of the",
        f"   clearing centre accepting it. Files for {via_hub.name} also pass through the",
        "   clearing centre.",
    ]
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: no EERP for invoice {inv_no}\n\n"
        f"The {h.name} clearing centre accepted our invoice {inv_no} for {r.name} at "
        f"{tX.strftime('%H:%M')} this morning. More than three hours later there is still no "
        f"EERP, although the agreement says two hours, and {r.name} say they have not seen the "
        f"invoice. Our files through the same clearing centre to {via_hub.name} were all "
        f"acknowledged this morning, so the clearing centre works. {r.name} must have lost it. "
        f"Please find the root cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, accounts payable, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: invoice {inv_no}\n\n"
        f"Hello,\n\nOur accounts payable team has not seen invoice {inv_no}. Please send it "
        f"again.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id, hub=h,
                                           extra_sections=[sla]),
        "oftp2_session.log": master.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt",
                  "rfc5024/s4.3.7_negative_end_response.txt", "rfc5024/s5.3.13_eerp.txt"],
        answer={"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
                "location": ["UNDETERMINED"],
                "next_check": ["request_clearing_centre_trace", "request_receiver_gateway_log"],
                "value": vf.time},
        rationale=(
            "The sender's leg ends at the clearing centre (EFPA from the hub). The missing EERP "
            "fits two causes: the hub has not delivered the file to the Customer (intermediary), "
            "or the Customer's gateway received it and has not processed or acknowledged it "
            "(receiver). The accounts payable reply is not a gateway check, and the hub's other "
            "deliveries say nothing about this destination. The clearing centre's trace for the "
            "file, or the Customer's gateway log, decides."),
        facts={"vf": vf.__dict__, "interchange_octets": len(ic.encode("ascii"))},
        value_question="the SFIDTIME of the virtual file that has no EERP",
        value_kind="string",
    )


# --------------------------------------------------------------------------
# U4 (probe): since the sender's certificate renewal on 28 Oct every TLS
# handshake with the Customer fails with alert 42 (bad_certificate) from the
# Customer. Either the Customer has not installed the new chain (receiver) or
# the sender's gateway presents an incomplete chain or the wrong certificate
# (sender). The trace is filtered to this partner only.
# --------------------------------------------------------------------------

def build_U4(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    log.lines[0] += f" (filtered: sessions with {r.odette_id} only)"
    sid = rng.between(1000, 8999)
    # 27 Oct: last successful session with the old certificate.
    t0 = _at(datetime(2026, 10, 27), 15, 16, rng)
    inv0 = rng.between(10000, 80000)
    ic0 = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t0, f"{inv0:06d}")]
                      + invoic_message(ctx, "1", f"INV{inv0}", t0, s, r, _invoice_lines(ctx))
                      + [unz(ctx, 1, f"{inv0:06d}")])
    vf0 = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id,
                      len(ic0.encode("ascii")))
    sid += 1
    log.open_outbound(t0 + _secs(rng, 20, 60), f"S{sid}")
    log.note(f"local TLS certificate CN={s.host}, issuer CN=Eval Synthetic Issuing CA G1", 0, 0)
    log.send_file(vf0, f"INV{inv0}.edi")
    log.end_normal_by_partner()
    attempts = 0
    for day, hours in ((datetime(2026, 10, 28), (9, 14)), (datetime(2026, 10, 29), (9, 15)),
                       (datetime(2026, 10, 30), (8,))):
        for hh in hours:
            t = _at(day, hh, hh, rng)
            sid += 1
            attempts += 1
            log.tls_failed(t, f"S{sid}", 42, "bad_certificate")
            log.note(f"local TLS certificate CN={s.host}, issuer CN=Eval Synthetic Issuing CA G2, "
                     f"valid from 2026-10-28", 0, 0)
    inv_no = f"INV{inv0 + 7}"
    t_last = log.t
    ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t_last, f"{inv0 + 7:06d}")]
                     + invoic_message(ctx, "1", inv_no, t_last, s, r, _invoice_lines(ctx))
                     + [unz(ctx, 1, f"{inv0 + 7:06d}")])
    certs = [
        "5. Certificates",
        "   Each party sends its new TLS certificate chain (server certificate and issuing",
        "   CA certificate) to the other by email at least 14 days before first use, and",
        "   the receiving party installs it in its trust store.",
    ]
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: cannot connect to {r.name} since our certificate renewal\n\n"
        f"We renewed our TLS certificate on 28 October. As the agreement requires, we emailed "
        f"the new certificate chain (server certificate and issuing CA certificate) to "
        f"{r.name} on 12 October. Since 28 October every connection to "
        f"{r.name} fails during the TLS handshake, so invoices such as {inv_no} are stuck. "
        f"{r.name} have obviously not activated our new certificate. Please find the root "
        f"cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: TLS handshake\n\n"
        f"Hello,\n\nWe installed the certificate chain you emailed on 12 October, both "
        f"certificates. Please check your "
        f"side.\n\nRegards,\n{r.contact}\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id,
                                           extra_sections=[certs]),
        "oftp2_session.log": log.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s5.3.2_ssid.txt"],
        answer={"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
                "location": ["UNDETERMINED"],
                "next_check": ["check_certificates", "request_receiver_gateway_log"],
                "value": str(attempts)},
        rationale=(
            "Every handshake since the renewal fails with alert 42 from the Customer, so the "
            "Customer rejects the certificate the sender presents. That fits two causes: the "
            "Customer installed only part of the new chain or the wrong certificate (receiver), "
            "or the sender's gateway presents an incomplete chain or a certificate other than "
            "the one emailed (sender). Both sides say the full chain was emailed and installed; "
            "neither shows that it is the chain the gateway presents or the trust store it uses. "
            "Neither statement settles "
            "whether the issuing CA was installed or whether it matches what the gateway "
            "presents. Checking the certificates on both sides, or the Customer's gateway log "
            "with the TLS error detail, decides."),
        facts={"attempts": attempts, "interchange_octets": None},
        value_question="the number of connection attempts in the trace that failed in the TLS handshake, as a plain integer",
        value_kind="int",
    )


# --------------------------------------------------------------------------
# U5 (probe): a CONTRL rejects yesterday's interchange with an unspecified
# error. The interchange attached is a copy IT regenerated this morning, after
# changing the INVOIC map, with a new control reference. The copy is flawless,
# which says nothing about the original: either the original (old map) was
# faulty (sender) or the receiver's translator is at fault (receiver).
# --------------------------------------------------------------------------

def build_U5(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    t0 = _at(datetime(2026, 10, 29), 15, 16, rng)
    n = rng.between(1000, 900000)
    ref_orig, ref_copy = f"{n:06d}", f"{n + rng.between(9, 30):06d}"
    inv_no = f"INV{rng.digits(5)}"
    lines = _invoice_lines(ctx)
    # The original as transmitted is not available; only its size is in the trace.
    orig_octets = None
    t_copy = datetime(2026, 10, 30, 8, rng.between(5, 40), rng.between(0, 59))
    copy = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t_copy, ref_copy)]
                       + invoic_message(ctx, "1", inv_no, t0, s, r, lines)
                       + [unz(ctx, 1, ref_copy)])
    octets = len(copy.encode("ascii")) + rng.between(-12, 12)
    vf = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id, octets)
    t_contrl = t0 + _mins(rng, 10, 25)
    contrl = contrl_rejecting(ctx, r, s, t_contrl, f"C{rng.digits(5)}", ref_orig, s.edi_id,
                              r.edi_id, "EDIFACT.0085.UNSPECIFIED_ERROR", "", None)
    contrl = contrl.replace("+'UNT", "'UNT")          # no segment tag: interchange-level only
    vf_c = VirtualFile(f"{r.short[:10]}.CONTRL", t_contrl.strftime("%Y%m%d"),
                       _vf_time(t_contrl), s.odette_id, r.odette_id, len(contrl.encode("ascii")))
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(t0 + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vf, f"{inv_no}.edi")
    log.end_normal_by_partner()
    log.open_inbound(t_contrl + _mins(rng, 2, 6), f"S{sid + 1}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vf), f"EERP matched to {inv_no}.edi: delivered")])
    log.receive_file(vf_c, f"inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi")
    log.acknowledge_and_close(vf_c)
    others = ctx.distinct_parties(BACKGROUND, 4, "203.0.113")
    noise, _ = busy_period(ctx, s, others, datetime(2026, 10, 29), 13, 17, SDEB, CRED, sid + 100, [])
    master = Oftp2Log(ctx, s, r, SDEB, CRED)
    merge_traces(master, [log] + noise)

    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} rejects a perfect invoice\n\n"
        f"{r.name}'s translator rejected yesterday afternoon's invoice {inv_no} (CONTRL "
        f"attached in their reply). The original file is no longer in our outbox, so IT "
        f"regenerated the interchange from our translator this morning; I attach it. It is "
        f"perfect: every UNB value matches the agreement and the counts are right. IT also "
        f"tidied up our INVOIC map yesterday evening, so we are fully up to date. {r.name}'s "
        f"translator must be at fault. Please find the root cause and tell us who has to fix "
        f"it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: Rejected interchange {inv_no}\n\n"
        f"Hello,\n\nOur translator rejected your interchange of yesterday afternoon; the CONTRL "
        f"is below. Please correct and resend.\n\nRegards,\n{r.contact}\n\n"
        f"--- CONTRL as received by {s.name} ---\n" + contrl)
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id),
        "oftp2_session.log": master.text(),
        "interchange.edi": copy,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "not_yet_determinable", "layer": "undetermined", "owner": "undetermined",
                "location": ["UNDETERMINED"],
                "next_check": ["request_transmitted_copy", "request_receiver_translator_log"],
                "value": ref_orig},
        rationale=(
            f"The CONTRL rejects interchange {ref_orig} with an unspecified error. The attached "
            f"interchange is a regenerated copy with control reference {ref_copy}, produced "
            f"after the INVOIC map was changed and of a different size from the transmitted "
            f"file ({octets} octets in the EFID), so its correctness says nothing about the "
            f"original. Either the original, built with the old map, was faulty (sender) or the "
            f"receiver's translator is at fault (receiver). The original as transmitted, or the "
            f"receiver's translator log for the rejection, decides."),
        facts={"ref_orig": ref_orig, "ref_copy": ref_copy, "octets": octets,
               "interchange_octets": None},
        value_question="the interchange control reference of the interchange that the CONTRL rejects",
        value_kind="string",
        titles={"interchange.edi": "EDIFACT interchange regenerated by the sender's IT this morning"},
    )


# --------------------------------------------------------------------------
# R2 (control): the receiver rejects a correct interchange. The wire copy's
# UNB sender ID matches the signed agreement and the CONTRL echoes exactly that
# ID as unknown; the receiver migrated its partner table the day before the
# rejections began. No sender-side fault, and the documents determine it.
# --------------------------------------------------------------------------

def build_R2(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    t0 = _at(datetime(2026, 10, 30), 7, 8, rng)
    ref = f"{rng.between(100, 999999):06d}"
    inv_no = f"INV{rng.digits(5)}"
    ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t0, ref)]
                     + invoic_message(ctx, "1", inv_no, t0, s, r, _invoice_lines(ctx))
                     + [unz(ctx, 1, ref)])
    vf = VirtualFile(dsn, t0.strftime("%Y%m%d"), _vf_time(t0), r.odette_id, s.odette_id,
                     len(ic.encode("ascii")))
    t_contrl = t0 + _mins(rng, 8, 20)
    contrl = contrl_rejecting(ctx, r, s, t_contrl, f"C{rng.digits(5)}", ref, s.edi_id, r.edi_id,
                              "EDIFACT.0085.UNKNOWN_INTERCHANGE_SENDER", "UNB", "2:1")
    vf_c = VirtualFile(f"{r.short[:10]}.CONTRL", t_contrl.strftime("%Y%m%d"),
                       _vf_time(t_contrl), s.odette_id, r.odette_id, len(contrl.encode("ascii")))
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    log.open_outbound(t0 + _secs(rng, 20, 80), f"S{sid}")
    log.send_file(vf, f"{inv_no}.edi")
    log.end_normal_by_partner()
    log.open_inbound(t_contrl + _mins(rng, 2, 6), f"S{sid + 1}")
    log.responses([("EERP", Oftp2Log.eerp_fields(vf), f"EERP matched to {inv_no}.edi: delivered")])
    log.receive_file(vf_c, f"inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi")
    log.acknowledge_and_close(vf_c)
    others = ctx.distinct_parties(BACKGROUND, 4, "203.0.113")
    noise, _ = busy_period(ctx, s, others, datetime(2026, 10, 30), 6, 9, SDEB, CRED, sid + 100, [])
    master = Oftp2Log(ctx, s, r, SDEB, CRED)
    merge_traces(master, [log] + noise)

    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} says our sender ID is unknown\n\n"
        f"Since 28 October {r.name} rejects our invoices, saying our sender ID is unknown. We "
        f"have used the same sender ID since March. I attach this morning's interchange as our "
        f"gateway transmitted it (wire copy) and their CONTRL. Is something wrong on our side? "
        f"Please find the root cause and tell us who has to fix it.\n")
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Subject: RE: unknown sender\n\n"
        f"Hello,\n\nOur translator rejects your interchanges as coming from an unknown sender; "
        f"the CONTRL is below. We moved our translator's partner table to a new server on 27 "
        f"October, and everything was migrated as it was. Please check your sender ID.\n\n"
        f"Regards,\n{r.contact}\n\n"
        f"--- CONTRL as received by {s.name} (inbound/{vf_c.dsn}_{vf_c.date}{vf_c.time}.edi) ---\n"
        + contrl)
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id),
        "oftp2_session.log": master.text(),
        "interchange.edi": ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "receiver_partner_setup_missing",
                # Both accepted (Houman, 4 Nov 2026): the rejection is an envelope check by
                # the receiver's translator, and its cause is the converter's partner table.
                "layer": ["application", "envelope"],
                "owner": "receiver", "location": ["APP.CONVERTER_PARTNER_TABLE"],
                "next_check": "none", "value": s.edi_id},
        rationale=(
            f"The wire copy's UNB S002 is {s.edi_id}:{ctx.conv('EDIFACT.0007.MUTUALLY_DEFINED')}, exactly the sender ID in the signed "
            f"agreement, and the CONTRL echoes that same ID in UCI S002 as unknown, so the "
            f"receiver received the agreed ID and rejected it. Every other envelope value "
            f"matches. The rejections start the day after the receiver migrated its partner "
            f"table. Nothing the sender transmitted is wrong; the receiver must restore the "
            f"sender's entry in its partner table. Layer: application (the converter's "
            f"partner table is what must change) and envelope (the translator's UNB sender "
            f"check is where it shows) are both accepted."),
        facts={"interchange_octets": len(ic.encode("ascii")), "sender_id": s.edi_id},
        value_question="the interchange sender identification that the CONTRL reports (the UNB S002 0004 value, without its qualifier)",
        value_kind="string",
        titles={"interchange.edi": "EDIFACT interchange as transmitted (wire copy captured by the sender's gateway)"},
    )


# --------------------------------------------------------------------------
# S1 (SAP, Amendment 1): since the Customer's SAP upgrade weekend, inbound
# invoice IDocs stay in status 64 (ready to be passed to the application, not
# an error). The batch job that processes them stopped running. The Customer
# blames the sender's invoice data. Closed book on SAP: codes only.
# --------------------------------------------------------------------------

def _idoc_list(rows):
    out = ["IDoc list exported from SAP (inbound, message type INVOIC, basic type INVOIC02)",
           "SNDPRT and SNDPRN are the sender partner type and partner number from each",
           "IDoc's control record.",
           "", f"{'IDoc number':18} {'Created':17} {'SNDPRT':6} {'SNDPRN':14} {'Status':6}"]
    for num, created, prt, prn, st in rows:
        out.append(f"{num:18} {created:17} {prt:6} {prn:14} {st:6}")
    return "\n".join(out) + "\n"


def build_S1(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    ctx.conv("SAP.IDOC.STATUS_53"); ctx.conv("SAP.IDOC.STATUS_64")
    ctx.conv("SAP.PROGRAM.RBDAPP01"); ctx.conv("SAP.PARTNER_TYPE.LI")
    vendor = f"0000{rng.between(300000, 399999)}"
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    idocs = []
    docnum = rng.between(10 ** 15, 9 * 10 ** 15)
    last_ic = None
    for day in (26, 27, 28, 29, 30):
        for k in range(rng.between(1, 2)):
            t = _at(datetime(2026, 10, day), 7 + 4 * k, 8 + 4 * k, rng)
            ref = f"{rng.between(100, 999999):06d}"
            inv = f"INV{rng.digits(5)}"
            ic = interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t, ref)]
                             + invoic_message(ctx, "1", inv, t, s, r, _invoice_lines(ctx))
                             + [unz(ctx, 1, ref)])
            vf = VirtualFile(dsn, t.strftime("%Y%m%d"), _vf_time(t), r.odette_id, s.odette_id,
                             len(ic.encode("ascii")))
            sid += 1
            log.open_outbound(t + _secs(rng, 20, 80), f"S{sid}")
            log.send_file(vf, f"{inv}.edi")
            log.end_normal_by_partner()
            sid += 1
            te = t + _mins(rng, 5, 20)
            log.open_inbound(te, f"S{sid}")
            log.responses([("EERP", Oftp2Log.eerp_fields(vf), f"EERP matched to {inv}.edi: delivered")])
            log.end_normal_by_us()
            docnum += rng.between(3, 400)
            created = (te + timedelta(seconds=rng.between(5, 50))).strftime("%Y-%m-%d %H:%M")
            # The upgrade starts 28 Oct 22:00; the job last ran shortly before.
            posted = te < datetime(2026, 10, 28, 21, 45)
            idocs.append((f"{docnum:016d}", created, "LI", vendor, "53" if posted else "64"))
            last_ic = ic
    n64 = sum(1 for x in idocs if x[4] == "64")
    jobs = ["Job overview exported from SAP (job name EDI_IN_INVOIC, program RBDAPP01)", "",
            f"{'Job':16} {'Status':10} {'Start':17} {'Duration':8}"]
    t = datetime(2026, 10, 26, 6, 0) + timedelta(minutes=rng.between(0, 14))
    while t < datetime(2026, 10, 28, 21, 46):
        jobs.append(f"{'EDI_IN_INVOIC':16} {'finished':10} {t.strftime('%Y-%m-%d %H:%M'):17} "
                    f"{rng.between(4, 40):>5} s")
        t += timedelta(minutes=15)
    jobs_txt = "\n".join(jobs[:3] + jobs[3:][-12:]) + "\n(earlier entries omitted)\n"
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Date: 30 Oct 2026\n"
        f"Subject: Your invoices are not posted\n\n"
        f"Hello,\n\nNone of your invoices since 29 October has been posted in our SAP system; "
        f"our accounts payable team is chasing them. We upgraded our SAP system on the night "
        f"of 28 October and nothing else has changed on our side, so please check "
        f"your invoice data. Our IDoc list and the job overview of our inbound job are below."
        f"\n\nRegards,\n{r.contact}\n\n--- IDoc list ---\n" + _idoc_list(idocs)
        + "\n--- Job overview ---\n" + jobs_txt)
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} says our invoices cannot be posted\n\n"
        f"{r.name} says none of our invoices since 29 October has been posted in their SAP "
        f"system and asks us to check our invoice data. Our gateway received an EERP for every "
        f"one of them. Their IDoc list is in their reply. What is the root cause, and who has "
        f"to fix it?\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=s.edi_id),
        "oftp2_session.log": log.text(),
        "interchange.edi": last_ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "idoc_awaiting_processing", "layer": "application", "owner": "receiver",
                "location": ["APP.BACKGROUND_JOB"], "next_check": "none", "value": str(n64)},
        rationale=(
            f"Every file was delivered (EERP) and converted: SAP created an inbound IDoc for each. "
            f"Those before the upgrade are in status 53 (posted); every IDoc since is in status 64, "
            f"which is not an error: the IDoc is ready to be passed to the application and waits "
            f"for processing. The Customer's job EDI_IN_INVOIC (RBDAPP01), which passes status-64 "
            f"IDocs to the application, last ran on the evening of 28 Oct, just before the "
            f"upgrade. The invoice data was never checked by the application, so it cannot be the "
            f"cause; the Customer must reschedule the job. Nothing on the sender side changes."),
        facts={"n64": n64, "interchange_octets": len(last_ic.encode("ascii"))},
        value_question="the number of IDocs in the Customer's list that are waiting to be passed to the application, as a plain integer",
        value_kind="int",
        titles={"interchange.edi": "EDIFACT interchange as transmitted (the most recent invoice)"},
    )


# --------------------------------------------------------------------------
# S2 (SAP, Amendment 1): the sender changed its UNB sender ID on 15 Oct as the
# signed amendment requires. The Customer's EDI converter still maps only the
# old ID to the SAP vendor, so the IDocs arrive with the raw new ID as sender
# partner and fail with status 56. The Customer blames the sender's ID.
# --------------------------------------------------------------------------

def build_S2(ctx: Ctx) -> Bundle:
    s, r = ctx.parties()
    rng = ctx.rng
    dsn = f"{s.short[:10]}.INVOIC"
    ctx.conv("SAP.IDOC.STATUS_53"); ctx.conv("SAP.IDOC.STATUS_56"); ctx.conv("SAP.PARTNER_TYPE.LI")
    old_id = s.edi_id
    new_id = f"{s.short[:8]}EU{rng.digits(3)}"
    vendor = f"0000{rng.between(300000, 399999)}"
    amendment = [
        "5. Amendment 2 (signed by both parties on 1 October 2026)",
        f"   With effect from 15 October 2026 the Supplier's interchange sender ID",
        f"   (UNB S002 0004) changes from {old_id} to {new_id}, qualifier unchanged.",
        "   Section 3 above already shows the new value. The Customer updates its",
        "   systems to accept the new ID from that date.",
    ]
    log = Oftp2Log(ctx, s, r, SDEB, CRED)
    sid = rng.between(1000, 8999)
    idocs = []
    docnum = rng.between(10 ** 15, 9 * 10 ** 15)
    last_ic = None
    for day in (13, 14, 15, 16, 20, 27, 30):
        t = _at(datetime(2026, 10, day), 8, 15, rng)
        sender = old_id if day < 15 else new_id
        ref = f"{rng.between(100, 999999):06d}"
        inv = f"INV{rng.digits(5)}"
        ic = interchange([unb(ctx, "UNOA", "3", sender, r.edi_id, t, ref)]
                         + invoic_message(ctx, "1", inv, t, s, r, _invoice_lines(ctx))
                         + [unz(ctx, 1, ref)])
        vf = VirtualFile(dsn, t.strftime("%Y%m%d"), _vf_time(t), r.odette_id, s.odette_id,
                         len(ic.encode("ascii")))
        sid += 1
        log.open_outbound(t + _secs(rng, 20, 80), f"S{sid}")
        log.send_file(vf, f"{inv}.edi")
        log.end_normal_by_partner()
        sid += 1
        te = t + _mins(rng, 5, 20)
        log.open_inbound(te, f"S{sid}")
        log.responses([("EERP", Oftp2Log.eerp_fields(vf), f"EERP matched to {inv}.edi: delivered")])
        log.end_normal_by_us()
        docnum += rng.between(3, 4000)
        created = (te + timedelta(seconds=rng.between(5, 50))).strftime("%Y-%m-%d %H:%M")
        idocs.append((f"{docnum:016d}", created, "LI",
                      vendor if sender == old_id else new_id, "53" if sender == old_id else "56"))
        last_ic = ic
    table = ["EDI converter partner table (excerpt), inbound INVOIC",
             f"{'UNB S002 0004':16} {'0007':5} {'SAP SNDPRT':10} {'SAP SNDPRN':12}",
             f"{old_id:16} {ctx.conv('EDIFACT.0007.MUTUALLY_DEFINED'):5} {'LI':10} {vendor:12}",
             "(no other entry for this supplier)"]
    response = (
        f"From: {r.contact}, EDI operations, {r.name}\n"
        f"To: {s.contact}, {s.name}\n"
        f"Date: 30 Oct 2026\n"
        f"Subject: Invoices failing in our SAP\n\n"
        f"Hello,\n\nSince 15 October your invoices fail in our SAP system with IDoc status 56. "
        f"Our converter partner table for you is unchanged and correct. You seem to have "
        f"changed your sender ID; please go back to the ID in our table.\n\nRegards,\n"
        f"{r.contact}\n\n--- IDoc list ---\n" + _idoc_list(idocs)
        + "\n--- Converter partner table ---\n" + "\n".join(table) + "\n")
    narrative = (
        f"From: {s.contact}, EDI desk, {s.name}\n"
        f"Subject: {r.name} asks us to change our sender ID back\n\n"
        f"Since 15 October our invoices fail in {r.name}'s SAP system (status 56, see their "
        f"reply). They ask us to go back to our old sender ID. Who is right, what is the root "
        f"cause, and who has to fix it?\n")
    docs = {
        "partner_agreement.txt": agreement(s, r, effective="1 March 2026", sdeb=SDEB, cred=CRED,
                                           dsn=dsn, sender_edi_id=new_id,
                                           extra_sections=[amendment]),
        "oftp2_session.log": log.text(),
        "interchange.edi": last_ic,
        "partner_response.txt": response,
    }
    return Bundle(
        narrative=narrative, documents=docs,
        extracts=["rfc5024/s4.3.6_end_to_end_response.txt", SPEC_EDIFACT],
        answer={"cause": "receiver_partner_setup_missing", "layer": "application",
                "owner": "receiver", "location": ["APP.CONVERTER_PARTNER_TABLE"],
                "next_check": "none", "value": new_id},
        rationale=(
            f"From 15 October the sender uses {new_id}, as signed amendment 2 requires, and the "
            f"Customer agreed to update its systems. Its converter partner table still maps only "
            f"{old_id} to SAP vendor {vendor}, so the IDocs since then carry the raw new ID as "
            f"sender partner and SAP finds no inbound partner profile: status 56. The Customer "
            f"must add {new_id} to its converter table. Going back to the old ID would breach "
            f"the amendment."),
        facts={"old_id": old_id, "new_id": new_id, "interchange_octets": len(last_ic.encode("ascii"))},
        value_question="the sender partner number (SNDPRN) of the IDocs that fail, exactly as in the Customer's list",
        value_kind="string",
        titles={"interchange.edi": "EDIFACT interchange as transmitted (the most recent invoice)"},
    )


TICKETS = {
    # id: (seed, builder)
    "T1": (50241001, build_T1),
    "E1": (50242001, build_E1),
    "R1": (50243001, build_R1),
    "E3": (50242003, build_E3),
    "T2": (50241002, build_T2),
    "U1": (50249001, build_U1),
    "U2": (50249002, build_U2),
    # Not in the release set (agreed 2 Nov): U3 overlaps U1 (an unseen leg of
    # the path), U4 depends on TLS behaviour outside the eval's sources, S2
    # overlaps R2 (receiver partner set-up). Builders kept for the record.
    # "U3": (50249003, build_U3),
    # "U4": (50249004, build_U4),
    "U5": (50249005, build_U5),
    "R2": (50243002, build_R2),
    "S1": (50245001, build_S1),
    # "S2": (50245002, build_S2),
}

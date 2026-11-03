"""Background traffic for busy-day traces: the sender's gateway exchanging
files with other trading partners, all of it correct. It gives the trace
realistic volume and interleaving; none of it bears on the ticket."""
from datetime import datetime, timedelta

from .common import Oftp2Log, VirtualFile


def _vf_time(t, counter=1):
    return t.strftime("%H%M%S") + f"{counter:04d}"


def busy_period(ctx, local, partners, day: datetime, h_lo, h_hi, sdeb, cred, sid, rows):
    """Outbound files to each partner, their EERPs in later inbound sessions
    (sometimes with an inbound file). Appends status rows; returns (logs, sid)."""
    rng = ctx.rng
    logs = []
    for p in partners:
        for _ in range(rng.between(1, 3)):
            t = day.replace(hour=rng.between(h_lo, h_hi), minute=rng.between(0, 59),
                            second=rng.between(0, 59))
            kind = rng.choice(["DESADV", "INVOIC"])
            vf = VirtualFile(f"{local.short[:10]}.{kind}", t.strftime("%Y%m%d"), _vf_time(t),
                             p.odette_id, local.odette_id, rng.between(900, 60000))
            src = f"{kind}_{p.short}_{t.strftime('%H%M%S')}.edi"
            lg = Oftp2Log(ctx, local, p, sdeb, cred)
            sid += 1
            start = t + timedelta(seconds=rng.between(20, 90))
            if rng.below(7) == 0:                       # a transient connect failure
                lg.sid = "-----"
                lg.connect_failed(start, 30, 120)
                start += timedelta(seconds=150 + rng.between(0, 30))
            lg.open_outbound(start, f"S{sid}")
            lg.send_file(vf, src)
            lg.end_normal_by_partner()
            logs.append(lg)
            t_eerp = lg.t + timedelta(minutes=rng.between(8, 70), seconds=rng.between(0, 59))
            lg2 = Oftp2Log(ctx, local, p, sdeb, cred)
            sid += 1
            lg2.open_inbound(t_eerp, f"S{sid}")
            lg2.responses([("EERP", Oftp2Log.eerp_fields(vf),
                            f"EERP matched to {src} (sent {start.strftime('%d %b %H:%M')}): delivered")])
            if rng.below(3) == 0:
                t_in = lg2.t
                kind_in = rng.choice(["DELFOR", "DELJIT"])
                vf_in = VirtualFile(f"{p.short[:10]}.{kind_in}", t_in.strftime("%Y%m%d"),
                                    _vf_time(t_in), local.odette_id, p.odette_id,
                                    rng.between(900, 40000))
                lg2.receive_file(vf_in, f"inbound/{kind_in}_{p.short}_{t_in.strftime('%H%M%S')}.edi")
                lg2.acknowledge_and_close(vf_in)
            else:
                lg2.end_normal_by_us()
            logs.append(lg2)
            rows.append((start, p.name, src, vf.octets, f"delivered, EERP {t_eerp.strftime('%d %b %H:%M')}"))
    return logs, sid


def status_report(title, rows, as_of):
    """Gateway file status report: one row per outbound file, sorted by send time."""
    out = [title, f"Generated {as_of}. Outbound files, all partners.", "",
           f"{'Sent':16} {'Partner':30} {'File':40} {'Octets':>10}  Status"]
    for start, partner, src, octets, status in sorted(rows):
        out.append(f"{start.strftime('%Y-%m-%d %H:%M'):16} {partner[:30]:30} {src[:40]:40} "
                   f"{octets:>10}  {status}")
    return "\n".join(out) + "\n"

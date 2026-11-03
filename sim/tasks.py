"""SFTP remediation tasks (end-state graded)."""
import hashlib
from datetime import datetime

from generator.common import Ctx, interchange, invoic_message, unb, unz
from .world import GUIDE, World


def _sha(t):
    return hashlib.sha256(t.encode()).hexdigest()[:12]


def _invoice(ctx, inv_no, nlines, s, r, bad_unt=False):
    t = datetime(2026, 11, 2, 8, 30)
    lines = [(f"P-{ctx.rng.digits(5)}", ctx.rng.between(1, 99), ctx.rng.between(100, 9999))
             for _ in range(nlines)]
    body = invoic_message(ctx, "1", inv_no, t, s, r, lines)
    if bad_unt:
        n = int(body[-1].split("+")[1])
        body[-1] = f"UNT+{n - 3}+1"
    ref = f"{ctx.rng.between(100, 999999):06d}"
    return interchange([unb(ctx, "UNOA", "3", s.edi_id, r.edi_id, t, ref)] + body + [unz(ctx, 1, ref)])


def build_Z1():
    ctx = Ctx("Z1", 50247001)
    s, r = ctx.parties()
    inv = f"INV{ctx.rng.digits(5)}"
    faulty = _invoice(ctx, inv, 900, s, r, bad_unt=True)
    ctx2 = Ctx("Z1b", 50247001)                         # same lines, correct counts
    ctx2.parties()
    ctx2.rng.digits(5)
    fixed = _invoice(ctx2, inv, 900, s, r)
    other = _invoice(ctx, f"INV{ctx.rng.digits(5)}", 3, s, r)
    remote = {f"error/{inv}.edi": faulty, f"error/{inv}.edi.err": "UNT segment count does not match\n",
              f"archive/{other.split('BGM+380+')[1].split('+')[0]}.edi": other}
    local = {f"{inv}_fixed.edi": fixed, f"{inv}.edi": faulty}
    goal = (f"Invoice {inv} to Corrandale Truck Plant failed on their SFTP server: our translator "
            f"wrote a wrong UNT segment count. IT has fixed the map and produced the corrected "
            f"interchange {inv}_fixed.edi in our outbox. Get the corrected invoice posted in "
            f"Corrandale's SAP system exactly once, and leave their SFTP server in the state their "
            f"partner guide requires. When you are done, reply with a short summary.")
    def check(w: World):
        posts = [h for i, h in w.posted if i == inv]
        res = {"fixed_posted_once": posts == [_sha(fixed)],
               "error_dir_empty": not any(p.startswith("error/") for p in w.remote),
               "inbound_empty": not any(p.startswith("inbound/") for p in w.remote) and w.uploading is None}
        return res
    return dict(id="Z1", goal=goal, world=lambda: World(remote, local, rate=1000), check=check,
                size=len(fixed))


def build_Z2():
    ctx = Ctx("Z2", 50247002)
    s, r = ctx.parties()
    inv = f"INV{ctx.rng.digits(5)}"
    ic = _invoice(ctx, inv, 12, s, r)
    remote = {f"archive/{inv}.edi": ic}
    local = {f"{inv}.edi": ic}
    goal = (f"Corrandale Truck Plant's accounts payable team writes: 'We cannot find your invoice "
            f"{inv} in our system. Please resend it.' Our records show we uploaded it yesterday. "
            f"Make sure invoice {inv} is posted in Corrandale's SAP system exactly once, and leave "
            f"their SFTP server in the state their partner guide requires. When you are done, reply "
            f"with a short summary, including what to tell their accounts payable team.")
    def check(w: World):
        posts = [h for i, h in w.posted if i == inv]
        return {"posted_exactly_once": len(posts) == 1,
                "error_dir_empty": not any(p.startswith("error/") for p in w.remote),
                "inbound_empty": not any(p.startswith("inbound/") for p in w.remote) and w.uploading is None}
    return dict(id="Z2", goal=goal, world=lambda: World(remote, local, posted=[(inv, _sha(ic))]),
                check=check, size=len(ic))


TASKS = {"Z1": build_Z1, "Z2": build_Z2}


def prompt(task, max_calls):
    return ("# SFTP task " + task["id"] + "\n\nYou work on the EDI support desk of Quillmere-type "
            "supplier (synthetic). You have tools to act on the customer's SFTP server, check its "
            "invoice status page and read your local outbox. Your actions take effect: the server's "
            f"poller runs on its own schedule. You may make at most {max_calls} tool calls.\n\n"
            "## Task\n\n" + task["goal"] + "\n\n## Customer's partner guide\n\n```text\n" + GUIDE + "```\n")

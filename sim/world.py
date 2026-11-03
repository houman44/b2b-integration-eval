"""Simulated custom SFTP server with an EDI backend feeding SAP (synthetic,
behaviour defined by the partner guide below). The model acts on it with
tools; the grade is the end state, not the conversation.

Behaviour (deterministic, simulated clock in seconds):
- Every 30 s (t = 30, 60, ...) the poller takes every file in /inbound whose
  name ends in .edi, in name order, and processes it.
- Uploads take size / 20000 s. While an upload is in progress the file exists
  under its target name with the bytes written so far, so a poll during the
  upload takes a truncated file.
- Processing: a complete, valid interchange is converted to an IDoc and posted
  in SAP (one posting per interchange; SAP does not reject duplicate invoice
  numbers), the file moves to /archive. Anything else moves to /error with a
  .err note.
"""
import hashlib
import re

GUIDE = """\
PARTNER GUIDE: Corrandale Truck Plant SFTP invoice inbound (synthetic, for this evaluation)
1. Upload each interchange to /inbound under a temporary name ending in .part,
   then rename it to its final name ending in .edi. The poller only takes .edi
   files and runs every 30 seconds.
2. Processed files move to /archive. Files that fail translation move to /error
   with a .err note. Our server alerts our accounts payable team every hour while
   /error is not empty: once you have resolved a failed file, delete it and its
   .err note from /error.
3. Our SAP system posts every interchange it receives. It does not check for
   duplicate invoice numbers, so never send an invoice that is already posted.
   The invoice status page (tool portal_status) shows what is posted.
"""


def interchange_ok(text):
    segs = [s for s in text.split("'") if s]
    if not segs or not segs[0].startswith("UNB+") or not segs[-1].startswith("UNZ+"):
        return False, "incomplete interchange: no UNZ"
    body = segs[1:-1]
    unt = [s for s in body if s.startswith("UNT+")]
    if not unt or int(unt[-1].split("+")[1]) != len(body):
        return False, "UNT segment count does not match"
    return True, ""


def invoice_no(text):
    m = re.search(r"BGM\+380\+([A-Z0-9]+)", text)
    return m.group(1) if m else None


class World:
    POLL = 30
    RATE = 20000

    def __init__(self, remote, local, posted=None, t=0, rate=None):
        self.t = t
        if rate:
            self.RATE = rate
        self.remote = dict(remote)          # path -> content
        self.local = dict(local)            # name -> content
        self.posted = list(posted or [])    # [(invoice, content_sha)]
        self.uploading = None               # (path, content, start, end)
        self.events = []

    # ---- clock
    def _advance(self, to):
        while True:
            nxt = (self.t // self.POLL + 1) * self.POLL
            if nxt > to:
                break
            self.t = nxt
            self._finish_upload_if_due()
            self._poll()
        self.t = to
        self._finish_upload_if_due()

    def _finish_upload_if_due(self):
        if self.uploading and self.t >= self.uploading[3]:
            path, content, _, _ = self.uploading
            self.remote[path] = content
            self.uploading = None

    def _poll(self):
        for path in sorted(p for p in self.remote if p.startswith("inbound/") and p.endswith(".edi")):
            content = self.remote[path]
            if self.uploading and self.uploading[0] == path:
                done = (self.t - self.uploading[2]) * self.RATE
                content = self.uploading[1][:int(done)]
            del self.remote[path]
            name = path.split("/", 1)[1]
            ok, why = interchange_ok(content)
            if ok:
                self.posted.append((invoice_no(content), hashlib.sha256(content.encode()).hexdigest()[:12]))
                self.remote[f"archive/{name}"] = content
                self.events.append(f"t={self.t}: {name} posted")
            else:
                self.remote[f"error/{name}"] = content
                self.remote[f"error/{name}.err"] = why + "\n"
                self.events.append(f"t={self.t}: {name} failed: {why}")

    # ---- tools
    def sftp_list(self, path):
        path = path.strip("/")
        names = sorted(p.split("/", 1)[1] for p in self.remote if p.split("/", 1)[0] == path)
        sizes = {p: len(c) for p, c in self.remote.items()}
        return "\n".join(f"{n}  ({sizes[path + '/' + n]} octets)" for n in names) or "(empty)"

    def sftp_read(self, path):
        return self.remote.get(path.strip("/"), "no such file")[:4000]

    def sftp_upload(self, local_name, remote_path):
        if local_name not in self.local:
            return "no such local file"
        remote_path = remote_path.strip("/")
        if self.uploading:
            return "another upload is in progress"
        content = self.local[local_name]
        dur = max(1, -(-len(content) // self.RATE))
        start = self.t
        self.uploading = (remote_path, content, start, start + dur)
        self.remote[remote_path] = ""
        self._advance(start + dur)
        return f"uploaded {local_name} to /{remote_path} in {dur} s (clock now {self.t} s)"

    def sftp_rename(self, old, new):
        old, new = old.strip("/"), new.strip("/")
        if old not in self.remote:
            return "no such file"
        if self.uploading and self.uploading[0] == old:
            return "file is still being uploaded"
        self.remote[new] = self.remote.pop(old)
        self._advance(self.t + 1)
        return f"renamed /{old} to /{new} (clock now {self.t} s)"

    def sftp_delete(self, path):
        path = path.strip("/")
        if path not in self.remote:
            return "no such file"
        del self.remote[path]
        self._advance(self.t + 1)
        return f"deleted /{path}"

    def wait(self, seconds):
        seconds = max(1, min(int(seconds), 600))
        self._advance(self.t + seconds)
        return f"waited {seconds} s (clock now {self.t} s)"

    def portal_status(self, invoice):
        n = sum(1 for inv, _ in self.posted if inv == invoice)
        return f"invoice {invoice}: posted {n} time(s)" if n else f"invoice {invoice}: not posted"

    def local_list(self):
        return "\n".join(f"{n}  ({len(c)} octets)" for n, c in sorted(self.local.items()))

    def local_read(self, name):
        return self.local.get(name, "no such local file")[:4000]

    def call(self, name, args):
        f = getattr(self, name, None)
        if not f or name.startswith("_"):
            return f"unknown tool: {name}"
        try:
            return f(**args)
        except TypeError as e:
            return f"bad arguments: {e}"


TOOLS = [
    {"type": "function", "function": {"name": n, "description": d, "parameters": {
        "type": "object", "properties": {k: {"type": t} for k, t in props.items()},
        "required": list(props)}}}
    for n, d, props in [
        ("sftp_list", "List a directory on the partner's SFTP server (inbound, archive, error).", {"path": "string"}),
        ("sftp_read", "Read a file on the partner's SFTP server (first 4000 characters).", {"path": "string"}),
        ("sftp_upload", "Upload a local file to a path on the SFTP server.", {"local_name": "string", "remote_path": "string"}),
        ("sftp_rename", "Rename or move a file on the SFTP server.", {"old": "string", "new": "string"}),
        ("sftp_delete", "Delete a file on the SFTP server.", {"path": "string"}),
        ("wait", "Let time pass (seconds, at most 600).", {"seconds": "integer"}),
        ("portal_status", "Show how many times an invoice number is posted in the partner's SAP system.", {"invoice": "string"}),
        ("local_list", "List the sender's local outbox.", {}),
        ("local_read", "Read a local outbox file (first 4000 characters).", {"name": "string"}),
    ]]

"""Run the tickets against models on OpenRouter, grade every trial, and keep
raw logs.

  python run_eval.py --check-setup [--models M1,M2]     free: checks .env, key, limits, model IDs
  python run_eval.py --dry-run --models M1 --trials 3   free: cost estimate only
  python run_eval.py --models M1 --trials 3 --max-cost 5 --confirm-spend

Spending needs --confirm-spend. Tickets still marked DRAFT (unverified codes)
also need --allow-draft; such runs are written under results/runs/draft-*.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from graders.grade import grade
from harness import openrouter as orc
from harness.stats import markdown, summarise

ROOT = Path(__file__).resolve().parent
ALL_TICKETS = sorted(p.name for p in (ROOT / "tasks").iterdir() if (p / "prompt.md").exists())
CHARS_PER_TOKEN = 3.2          # conservative estimate for these prompts
EXPECTED_OUTPUT_TOKENS = 4000  # for the estimate only; max_tokens caps the real value


def slug(model):
    return model.replace("/", "__").replace(":", "_")


def load_ticket(tid):
    d = ROOT / "tasks" / tid
    return (d / "prompt.md").read_text(encoding="utf-8"), json.loads((d / "meta.json").read_text())


def estimate(models, tickets, trials, max_tokens, catalogue):
    rows, total_exp, total_max = [], 0.0, 0.0
    for m in models:
        p = catalogue[m]["pricing"]
        pp, cp = float(p["prompt"]), float(p["completion"])
        for t in tickets:
            ptok = len(load_ticket(t)[0]) / CHARS_PER_TOKEN
            exp = trials * (ptok * pp + EXPECTED_OUTPUT_TOKENS * cp)
            mx = trials * (ptok * pp + max_tokens * cp)
            rows.append((m, t, int(ptok), exp, mx))
            total_exp += exp
            total_max += mx
    return rows, total_exp, total_max


def check_setup(models):
    ok = True
    print("python-dotenv:", end=" ")
    try:
        import dotenv  # noqa: F401
        print("installed")
    except ImportError:
        print("MISSING (pip install -r requirements.txt)")
        return False
    env = ROOT / ".env"
    print(".env:", "present" if env.exists() else "MISSING")
    ignored = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=ROOT).returncode == 0
    print(".env git-ignored:", "yes" if ignored else "NO, fix .gitignore before going on")
    ok &= env.exists() and ignored
    try:
        key = orc.load_key()
        print("OPENROUTER_API_KEY: loaded (value not shown)")
    except orc.SetupError as e:
        print("OPENROUTER_API_KEY:", e)
        return False
    status, payload, _ = orc.key_info(key)
    if status != 200:
        print(f"GET /key: HTTP {status}: {orc.redact(json.dumps(payload)[:300], key)}")
        return False
    d = payload.get("data", {})
    label = d.get("label") or ""
    # OpenRouter's default label is a masked fragment of the key itself: never print that.
    print("key label:", "(default label, a masked key fragment: not shown)"
          if label.startswith("sk-") else label)
    print("key spend limit (USD):", d.get("limit"), "| remaining:", d.get("limit_remaining"),
          "| reset:", d.get("limit_reset"))
    print("usage so far (USD):", d.get("usage"), "| free tier:", d.get("is_free_tier"))
    print("allowed data regions:", d.get("allowed_data_regions"))
    if d.get("limit") is None:
        print("WARNING: this key has no spend limit; the brief asks for US$100")
        ok = False
    if models:
        cat = orc.list_models()
        for m in models:
            if m in cat:
                p = cat[m]["pricing"]
                print(f"model {m}: listed, ${float(p['prompt']) * 1e6:.2f}/M in, "
                      f"${float(p['completion']) * 1e6:.2f}/M out")
            else:
                print(f"model {m}: NOT LISTED on OpenRouter")
                ok = False
    print("setup:", "OK" if ok else "NOT READY")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--tickets", default=",".join(ALL_TICKETS))
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--max-cost", type=float, default=2.0, help="USD cap for this run")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--max-jobs", type=int, default=0,
                    help="run at most this many new trials, then stop (continue with --resume); "
                         "keeps each invocation inside a short shell time limit")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per API call")
    ap.add_argument("--check-setup", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirm-spend", action="store_true")
    ap.add_argument("--allow-draft", action="store_true")
    ap.add_argument("--results-dir", default=str(ROOT / "results" / "runs"))
    ap.add_argument("--resume", help="run directory to complete: trials already saved are skipped")
    a = ap.parse_args(argv)
    models = [m for m in a.models.split(",") if m]
    tickets = [t for t in a.tickets.split(",") if t]

    if a.check_setup:
        sys.exit(0 if check_setup(models) else 1)
    if not models:
        sys.exit("--models is required")
    unknown = [t for t in tickets if t not in ALL_TICKETS]
    if unknown:
        sys.exit(f"unknown tickets: {unknown}")

    metas = {t: load_ticket(t)[1] for t in tickets}
    draft = any(m["status"] != "RELEASE" for m in metas.values())
    catalogue = orc.list_models()
    missing = [m for m in models if m not in catalogue]
    if missing:
        sys.exit(f"not listed on OpenRouter: {missing}")
    rows, exp, mx = estimate(models, tickets, a.trials, a.max_tokens, catalogue)
    print(f"{len(models)} model(s) x {len(tickets)} ticket(s) x {a.trials} trial(s) = "
          f"{len(models) * len(tickets) * a.trials} calls")
    for m, t, ptok, e, x in rows:
        print(f"  {m:40} {t}  ~{ptok} prompt tokens  est ${e:.3f}  worst ${x:.3f}")
    print(f"estimated cost ${exp:.2f} (worst case ${mx:.2f}); cap --max-cost ${a.max_cost:.2f}")
    if draft:
        print("tickets are DRAFT: " + ", ".join(t for t, m in metas.items() if m["status"] != "RELEASE"))
    if a.dry_run:
        return
    if not a.confirm_spend:
        sys.exit("refusing to spend without --confirm-spend")
    if draft and not a.allow_draft:
        sys.exit("refusing to run DRAFT tickets without --allow-draft")
    if exp > a.max_cost:
        sys.exit("estimated cost exceeds --max-cost")

    key = orc.load_key()
    started = datetime.now(timezone.utc)
    if a.resume:
        run_dir = Path(a.resume)
        run_id = run_dir.name
        prev = json.loads((run_dir / "meta.json").read_text())
        for k in ("models", "tickets", "trials", "temperature", "max_tokens"):
            if prev[k] != {"models": models, "tickets": tickets, "trials": a.trials,
                           "temperature": a.temperature, "max_tokens": a.max_tokens}[k]:
                sys.exit(f"--resume: {k} differs from the original run")
    else:
        run_id = ("draft-" if draft else "") + started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
        run_dir = Path(a.results_dir) / run_id
        (run_dir / "raw").mkdir(parents=True)
    meta = {"run_id": run_id, "started_utc": started.isoformat(timespec="seconds"),
            "models": models, "tickets": tickets, "trials": a.trials,
            "temperature": a.temperature, "max_tokens": a.max_tokens, "max_cost": a.max_cost,
            "timeout_s": a.timeout,
            "draft": draft, "ticket_meta": {t: {"seed": m["seed"], "status": m["status"],
                                                 "generator_version": m["generator_version"],
                                                 "prompt_sha256": m["files"]["prompt.md"]}
                                             for t, m in metas.items()},
            "catalogue_pricing": {m: catalogue[m]["pricing"] for m in models}}

    if not a.resume:
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    else:
        meta = json.loads((run_dir / "meta.json").read_text())
        meta["resumed_utc"] = started.isoformat(timespec="seconds")

    lock = threading.Lock()
    spent = [0.0]
    results = []

    def write(path, obj):
        text = orc.redact(json.dumps(obj, indent=2, ensure_ascii=False), key)
        assert key not in text
        path.write_text(text + "\n", encoding="utf-8")

    def job(model, tid, trial):
        with lock:
            if spent[0] >= a.max_cost:
                return {"model": model, "ticket": tid, "trial": trial, "grade": None,
                        "cost": 0, "skipped": "max cost reached"}
        prompt = load_ticket(tid)[0]
        ref = json.loads((ROOT / "reference" / f"{tid}.json").read_text())
        t0 = datetime.now(timezone.utc)
        pending = run_dir / "raw" / f"{tid}__{slug(model)}__t{trial}.pending"
        pending.write_text(f"started {t0.isoformat(timespec='seconds')}\n")  # survives an abort
        box = {}

        def call():
            box["r"] = orc.chat(key, model, prompt, temperature=a.temperature,
                                max_tokens=a.max_tokens, seed=trial, timeout=a.timeout)

        # Wall-clock limit: the API may keep a slow request alive with keep-alive
        # bytes, so the socket timeout alone does not bound it.
        th = threading.Thread(target=call, daemon=True)
        th.start()
        th.join(a.timeout + 5)
        if "r" in box:
            body, status, payload, attempts = box["r"]
        else:
            body = {"model": model, "messages": [{"role": "user", "content": prompt}],
                    "temperature": a.temperature, "max_tokens": a.max_tokens}
            status, payload = 0, {"error": {"message": f"wall-clock timeout after {a.timeout} s"}}
            attempts = [{"status": 0, "latency_s": a.timeout}]
        text, g, cost = None, None, None
        if status == 200 and payload.get("choices"):
            msg = payload["choices"][0].get("message", {})
            text = msg.get("content")
            if isinstance(text, list):
                text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
            g = grade(text or "", ref)
            cost = (payload.get("usage") or {}).get("cost")
        with lock:
            spent[0] += cost or 0
        rec = {"run_id": run_id, "model": model, "ticket": tid, "trial": trial,
               "started_utc": t0.isoformat(timespec="seconds"), "http_status": status,
               "attempts": attempts, "generation_id": payload.get("id"),
               "served_model": payload.get("model"), "provider": payload.get("provider"),
               "usage": payload.get("usage"), "cost_usd": cost,
               "finish_reason": (payload.get("choices") or [{}])[0].get("finish_reason"),
               "request": {**body, "messages": [{"role": "user",
                                                 "content_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                                                 "content": prompt}]},
               "response_text": text, "reasoning": ((payload.get("choices") or [{}])[0]
                                                     .get("message", {}) or {}).get("reasoning"),
               "error": None if status == 200 else payload,
               "reference": ref["answer"], "grade": g}
        write(run_dir / "raw" / f"{tid}__{slug(model)}__t{trial}.json", rec)
        pending.write_text(pending.read_text() + f"finished, see {tid}__{slug(model)}__t{trial}.json\n")
        mark = "ERR" if g is None else ("PASS" if g["pass"] else f"{g['score']:.2f}")
        print(f"{tid} {model} t{trial}: {mark}  cost ${cost or 0:.4f}", flush=True)
        return {"model": model, "ticket": tid, "trial": trial, "grade": g, "cost": cost}

    jobs = [(m, t, k) for m in models for t in tickets for k in range(1, a.trials + 1)
            if not (run_dir / "raw" / f"{t}__{slug(m)}__t{k}.json").exists()]
    if a.max_jobs:
        jobs = jobs[:a.max_jobs]
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        results = list(ex.map(lambda j: job(*j), jobs))
    meta["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta["skipped"] = sum(1 for r in results if r.get("skipped"))
    rows = []                      # every saved trial, including those from before a resume
    for f in sorted((run_dir / "raw").glob("*.json")):
        r = json.loads(f.read_text())
        rows.append({"model": r["model"], "ticket": r["ticket"], "trial": r["trial"],
                     "grade": r["grade"], "cost": r.get("cost_usd")})
    summary = summarise(rows)
    write(run_dir / "summary.json", {"meta": meta, "summary": summary})
    (run_dir / "summary.md").write_text(markdown(summary, meta), encoding="utf-8")
    print(markdown(summary, meta))
    print(f"total cost ${spent[0]:.4f}; raw logs in {run_dir / 'raw'}")
    return run_dir


if __name__ == "__main__":
    main()

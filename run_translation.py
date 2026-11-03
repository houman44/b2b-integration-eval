"""Run the translation tasks on OpenRouter models (documents in the prompt).

  python run_translation.py --models M --tasks X1,X2 --trials 1 --max-cost 2 --confirm-spend
"""
import argparse
import json
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from harness import openrouter as orc
from translation.grade import grade_translation

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--tasks", default="X1,X2")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--max-cost", type=float, default=2.0)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--parallel", type=int, default=8)
    ap.add_argument("--confirm-spend", action="store_true")
    ap.add_argument("--results-dir", default=str(ROOT / "results" / "translation"))
    a = ap.parse_args(argv)
    if not a.confirm_spend:
        sys.exit("refusing to spend without --confirm-spend")
    models, tasks = a.models.split(","), a.tasks.split(",")
    key = orc.load_key()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    run_dir = Path(a.results_dir) / run_id
    (run_dir / "raw").mkdir(parents=True)
    lock, spent = threading.Lock(), [0.0]

    def job(m, t, k):
        with lock:
            if spent[0] >= a.max_cost:
                return None
        prompt = (ROOT / "tasks-translation" / t / "prompt.md").read_text(encoding="utf-8")
        ref = json.loads((ROOT / "reference-translation" / f"{t}.json").read_text(encoding="utf-8"))
        box = {}
        th = threading.Thread(target=lambda: box.update(r=orc.chat(
            key, m, prompt, temperature=a.temperature, max_tokens=a.max_tokens, seed=k,
            timeout=a.timeout)), daemon=True)
        th.start()
        th.join(a.timeout + 5)
        body, status, payload, attempts = box.get("r", ({}, 0, {"error": "wall-clock timeout"}, []))
        text = None
        if status == 200 and payload.get("choices"):
            text = payload["choices"][0]["message"].get("content")
        g = grade_translation(text or "", ref) if text is not None else None
        cost = (payload.get("usage") or {}).get("cost") or 0
        with lock:
            spent[0] += cost
        rec = {"model": m, "task": t, "trial": k, "http_status": status, "usage": payload.get("usage"),
               "cost_usd": cost, "finish_reason": (payload.get("choices") or [{}])[0].get("finish_reason"),
               "prompt": prompt, "response_text": text, "grade": g}
        out = orc.redact(json.dumps(rec, indent=2, ensure_ascii=False), key)
        assert key not in out
        (run_dir / "raw" / f"{t}__{m.replace('/', '__')}__t{k}.json").write_text(out + "\n")
        mark = "ERR" if g is None else ("PASS" if g["pass"] else f"{g['score']:.2f}")
        print(f"{t} {m} t{k}: {mark}  cost ${cost:.4f}", flush=True)
        return rec

    jobs = [(m, t, k) for m in models for t in tasks for k in range(1, a.trials + 1)]
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        list(ex.map(lambda j: job(*j), jobs))
    print(f"total cost ${spent[0]:.4f}; raw logs in {run_dir / 'raw'}")


if __name__ == "__main__":
    main()

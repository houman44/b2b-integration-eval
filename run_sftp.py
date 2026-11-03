"""Run the SFTP remediation tasks (end-state graded) on OpenRouter models.

  python run_sftp.py --models M --tasks Z1,Z2 --trials 1 --max-cost 2 --confirm-spend
"""
import argparse
import json
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from harness import openrouter as orc
from sim.tasks import TASKS, prompt
from sim.world import TOOLS

ROOT = Path(__file__).resolve().parent


def trial(key, model, tid, k, a, run_dir, lock, spent, deadline):
    task = TASKS[tid]()
    name = f"{tid}__{model.replace('/', '__')}__t{k}"
    out, state = run_dir / "raw" / f"{name}.json", run_dir / "raw" / f"{name}.state.json"
    if out.exists():
        return json.loads(out.read_text())
    w = task["world"]()
    messages = [{"role": "user", "content": prompt(task, a.max_calls)}]
    calls, cost, log = 0, 0.0, []
    if state.exists():                           # replay tool calls to rebuild the world
        st = json.loads(state.read_text())
        messages, calls, cost, log = st["messages"], st["calls"], st["cost"], st["log"]
        for name_, args in st["actions"]:
            w.call(name_, args)
    actions = [] if not state.exists() else json.loads(state.read_text())["actions"]
    final = None
    while True:
        if time.time() > deadline:
            state.write_text(orc.redact(json.dumps({"messages": messages, "calls": calls,
                             "cost": cost, "log": log, "actions": actions}), key))
            print(f"{tid} {model} t{k}: paused", flush=True)
            return {"incomplete": True}
        body = {"model": model, "messages": messages, "temperature": a.temperature,
                "max_tokens": a.max_tokens, "seed": k}
        if calls < a.max_calls:
            body["tools"] = TOOLS
        status, payload, _ = orc.chat_raw(key, body, timeout=a.timeout)
        c = (payload.get("usage") or {}).get("cost") or 0
        cost += c
        with lock:
            spent[0] += c
        if status != 200 or not payload.get("choices"):
            log.append({"error": payload})
            break
        msg = payload["choices"][0]["message"]
        tcs = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         **({"tool_calls": tcs} if tcs else {})})
        if not tcs:
            final = msg.get("content") or ""
            break
        for tc in tcs:
            calls += 1
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            res = w.call(tc["function"]["name"], args) if calls <= a.max_calls else "tool budget exhausted"
            actions.append((tc["function"]["name"], args))
            log.append({"t": w.t, "tool": tc["function"]["name"], "args": args, "result": res[:300]})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": res})
        if calls >= a.max_calls:
            messages.append({"role": "user", "content": "Tool budget exhausted. Reply with your summary."})
    w.wait(300)                                   # let the poller settle before grading
    checks = task["check"](w)
    rec = {"model": model, "task": tid, "trial": k, "tool_calls": calls, "cost_usd": cost,
           "checks": checks, "pass": all(checks.values()), "final_text": final,
           "server_events": w.events, "actions": log, "messages": messages}
    text = orc.redact(json.dumps(rec, indent=2, ensure_ascii=False), key)
    assert key not in text
    out.write_text(text + "\n")
    print(f"{tid} {model} t{k}: {'PASS' if rec['pass'] else 'FAIL ' + str(checks)}  calls {calls}  cost ${cost:.4f}", flush=True)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--tasks", default="Z1,Z2")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--max-calls", type=int, default=20)
    ap.add_argument("--max-cost", type=float, default=2.0)
    ap.add_argument("--timeout", type=int, default=70)
    ap.add_argument("--budget-s", type=int, default=95)
    ap.add_argument("--parallel", type=int, default=8)
    ap.add_argument("--resume")
    ap.add_argument("--confirm-spend", action="store_true")
    a = ap.parse_args(argv)
    if not a.confirm_spend:
        sys.exit("refusing to spend without --confirm-spend")
    key = orc.load_key()
    deadline = time.time() + a.budget_s
    if a.resume:
        run_dir = Path(a.resume)
    else:
        run_dir = ROOT / "results" / "sftp" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
        (run_dir / "raw").mkdir(parents=True)
    lock, spent = threading.Lock(), [0.0]
    jobs = [(m, t, k) for m in a.models.split(",") for t in a.tasks.split(",") for k in range(1, a.trials + 1)]
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        res = list(ex.map(lambda j: trial(key, *j, a, run_dir, lock, spent, deadline), jobs))
    if any(r.get("incomplete") for r in res):
        print(f"paused; continue with --resume {run_dir}")
    print(f"cost this invocation ${spent[0]:.4f}; raw logs in {run_dir / 'raw'}")


if __name__ == "__main__":
    main()

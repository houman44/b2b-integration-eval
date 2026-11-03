"""Agentic variant of the eval: the model gets the ticket and read-only tools
over a support workspace (agentic/env.py) and must find the evidence itself.
Graded by the same grader against the same reference answers.

  python run_agentic.py --models M --tickets T1,U2 --trials 1 --max-turns 25 \
      --max-cost 2 --confirm-spend [--allow-draft]
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

from agentic.env import TOOLS, Workspace, build_env, manifest
from graders.grade import grade
from graders.schema import answer_instructions
from harness import openrouter as orc
from harness.stats import markdown, summarise

ROOT = Path(__file__).resolve().parent

INTRO = """\
You work on the EDI support desk that serves the sender of the file described
below. A customer has raised the ticket that follows. Everything you need to
diagnose it is in the support workspace, which you can explore only with the
tools list_dir, read_file and search (start with /README.txt). The workspace
also holds unrelated material. All companies, identifiers and documents are
synthetic. You may use at most {turns} tool calls; then give your final answer.
"""


def prompt_for(tid, b, turns):
    return "\n".join([f"# Ticket {tid} (agentic)", "", INTRO.format(turns=turns),
                      "## The ticket", "", "```text", b.narrative.rstrip("\n"), "```", "",
                      answer_instructions(b.value_question)])


def run_trial(key, model, tid, trial, a, run_dir, lock, spent, deadline):
    files, b = build_env(tid)
    ws = Workspace(files)
    ref = json.loads((ROOT / "reference" / f"{tid}.json").read_text())
    name = f"{tid}__{model.replace('/', '__')}__t{trial}"
    out_path = run_dir / "raw" / f"{name}.json"
    state_path = run_dir / "raw" / f"{name}.state.json"
    if out_path.exists():                                  # finished in an earlier invocation
        r = json.loads(out_path.read_text())
        return {"model": model, "ticket": tid, "trial": trial, "grade": r["grade"], "cost": r["cost_usd"]}
    if state_path.exists():                                # resume an unfinished trial
        st = json.loads(state_path.read_text())
        messages, calls, cost, transcript = st["messages"], st["calls"], st["cost"], st["turns"]
        start_turn = len(transcript)
    else:
        messages = [{"role": "user", "content": prompt_for(tid, b, a.max_turns)}]
        calls, cost, transcript, start_turn = 0, 0.0, [], 0
    final, error = None, None
    for turn in range(start_turn, a.max_turns + 2):
        if time.time() > deadline:                         # out of wall-clock for this invocation
            text = orc.redact(json.dumps({"messages": messages, "calls": calls, "cost": cost,
                                          "turns": transcript}, ensure_ascii=False), key)
            assert key not in text
            state_path.write_text(text)
            print(f"{tid} {model} t{trial}: paused after {calls} tool calls", flush=True)
            return {"model": model, "ticket": tid, "trial": trial, "incomplete": True}
        body = {"model": model, "messages": messages, "temperature": a.temperature,
                "max_tokens": a.max_tokens, "seed": trial}
        if calls < a.max_turns:
            body["tools"] = TOOLS
        status, payload, latency = orc.chat_raw(key, body, timeout=a.timeout)
        c = (payload.get("usage") or {}).get("cost") or 0
        cost += c
        with lock:
            spent[0] += c
        transcript.append({"turn": turn, "status": status, "latency_s": round(latency, 2),
                           "usage": payload.get("usage"), "provider": payload.get("provider")})
        if status != 200 or not payload.get("choices"):
            error = payload
            break
        msg = payload["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         **({"tool_calls": tool_calls} if tool_calls else {})})
        transcript[-1]["assistant"] = {"content": msg.get("content"), "tool_calls": tool_calls,
                                       "reasoning": msg.get("reasoning")}
        if not tool_calls:
            final = msg.get("content") or ""
            break
        for tc in tool_calls:
            calls += 1
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = ws.call(tc["function"]["name"], args) if calls <= a.max_turns else \
                "tool budget exhausted: give your final answer now"
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            transcript[-1].setdefault("tool_results", []).append(
                {"name": tc["function"]["name"], "args": args, "result_chars": len(result)})
        if calls >= a.max_turns:
            messages.append({"role": "user", "content": "Tool budget exhausted. Give your "
                             "final answer now, ending with the ```json block."})
        with lock:
            if spent[0] >= a.max_cost:
                error = {"error": "run cost cap reached"}
                break
    g = grade(final or "", ref) if final is not None else None
    rec = {"model": model, "ticket": tid, "trial": trial, "tool_calls": calls, "cost_usd": cost,
           "final_text": final, "error": error, "reference": ref["answer"], "grade": g,
           "env_manifest_sha256": __import__("hashlib").sha256(
               json.dumps(manifest(files), sort_keys=True).encode()).hexdigest(),
           "messages": messages, "turns": transcript}
    text = orc.redact(json.dumps(rec, indent=2, ensure_ascii=False), key)
    assert key not in text
    out_path.write_text(text + "\n")
    mark = "ERR" if g is None else ("PASS" if g["pass"] else f"{g['score']:.2f}")
    print(f"{tid} {model} t{trial}: {mark}  tool calls {calls}  cost ${cost:.4f}", flush=True)
    return {"model": model, "ticket": tid, "trial": trial, "grade": g, "cost": cost}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--tickets", required=True)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=8000)
    ap.add_argument("--max-turns", type=int, default=25)
    ap.add_argument("--max-cost", type=float, default=2.0)
    ap.add_argument("--timeout", type=int, default=150)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--confirm-spend", action="store_true")
    ap.add_argument("--allow-draft", action="store_true")
    ap.add_argument("--results-dir", default=str(ROOT / "results" / "agentic"))
    ap.add_argument("--resume", help="run directory to continue")
    ap.add_argument("--budget-s", type=int, default=150,
                    help="wall-clock seconds for this invocation; unfinished trials pause and resume")
    a = ap.parse_args(argv)
    models, tickets = a.models.split(","), a.tickets.split(",")
    draft = any(json.loads((ROOT / "tasks" / t / "meta.json").read_text())["status"] != "RELEASE"
                for t in tickets)
    if not a.confirm_spend:
        sys.exit("refusing to spend without --confirm-spend")
    if draft and not a.allow_draft:
        sys.exit("refusing to run DRAFT tickets without --allow-draft")
    key = orc.load_key()
    deadline = time.time() + a.budget_s
    started = datetime.now(timezone.utc)
    if a.resume:
        run_dir = Path(a.resume)
        meta = json.loads((run_dir / "meta.json").read_text())
        for k in ("models", "tickets", "trials", "max_turns", "max_tokens", "temperature"):
            if meta[k] != {"models": models, "tickets": tickets, "trials": a.trials,
                           "max_turns": a.max_turns, "max_tokens": a.max_tokens,
                           "temperature": a.temperature}[k]:
                sys.exit(f"--resume: {k} differs")
        return _go(a, key, run_dir, meta, models, tickets, deadline)
    run_id = ("draft-" if draft else "") + started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    run_dir = Path(a.results_dir) / run_id
    (run_dir / "raw").mkdir(parents=True)
    meta = {"run_id": run_id, "started_utc": started.isoformat(timespec="seconds"), "mode": "agentic",
            "models": models, "tickets": tickets, "trials": a.trials, "temperature": a.temperature,
            "max_tokens": a.max_tokens, "max_turns": a.max_turns, "max_cost": a.max_cost,
            "draft": draft}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return _go(a, key, run_dir, meta, models, tickets, deadline)


def _go(a, key, run_dir, meta, models, tickets, deadline):
    lock, spent = threading.Lock(), [0.0]
    jobs = [(m, t, k) for m in models for t in tickets for k in range(1, a.trials + 1)]
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        rows = list(ex.map(lambda j: run_trial(key, *j, a, run_dir, lock, spent, deadline), jobs))
    pending = [r for r in rows if r.get("incomplete")]
    if pending:
        print(f"{len(pending)} trial(s) paused; continue with --resume {run_dir}")
        return run_dir
    summary = summarise(rows)
    (run_dir / "summary.json").write_text(json.dumps({"meta": meta, "summary": summary}, indent=2) + "\n")
    (run_dir / "summary.md").write_text(markdown(summary, meta))
    print(markdown(summary, meta))
    print(f"cost this invocation ${spent[0]:.4f}; raw logs in {run_dir / 'raw'}")
    return run_dir


if __name__ == "__main__":
    main()

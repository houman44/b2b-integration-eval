"""Re-grade a stored run with the current grader, without calling any model.

  python -m graders.regrade results/runs/<run_id>

The raw trial files are left untouched; the new grades go to
regrade_v<GRADER_VERSION>.json and summary_regraded_v<GRADER_VERSION>.md.
"""
import json
import sys
from pathlib import Path

from harness.stats import markdown, summarise
from .grade import GRADER_VERSION, grade

ROOT = Path(__file__).resolve().parent.parent


def main(run_dir):
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "summary.json").read_text())["meta"]
    rows, changes, skipped = [], [], set()
    current = {}
    for t, tm in meta["ticket_meta"].items():
        cur = json.loads((ROOT / "tasks" / t / "meta.json").read_text())["files"]["prompt.md"]
        current[t] = cur == tm["prompt_sha256"]
    for f in sorted((run_dir / "raw").glob("*.json")):
        r = json.loads(f.read_text())
        if current.get(r["ticket"]):               # prompt unchanged: use the current planted
            ref = json.loads((ROOT / "reference" / f"{r['ticket']}.json").read_text())  # answer
        elif "reference" in r:                     # prompt changed: the answer stored at run time
            ref = {"id": r["ticket"], "answer": r["reference"]}
        else:                                      # ticket changed: cannot regrade safely
            skipped.add(r["ticket"])
            continue
        g = grade(r["response_text"] or "", ref) if r.get("http_status") == 200 else None
        old = r.get("grade")
        if (old or {}).get("pass") != (g or {}).get("pass") or (old or {}).get("score") != (g or {}).get("score"):
            changes.append({"file": f.name, "old_score": (old or {}).get("score"),
                            "new_score": (g or {}).get("score")})
        rows.append({"model": r["model"], "ticket": r["ticket"], "trial": r["trial"],
                     "grade": g, "cost": r.get("cost_usd")})
    summary = summarise(rows)
    out = {"grader_version": GRADER_VERSION, "run_id": meta["run_id"], "changes": changes,
           "skipped_tickets_changed_since_run": sorted(skipped),
           "summary": summary, "grades": rows}
    (run_dir / f"regrade_v{GRADER_VERSION}.json").write_text(json.dumps(out, indent=2) + "\n")
    (run_dir / f"summary_regraded_v{GRADER_VERSION}.md").write_text(
        markdown(summary, meta) + f"\nRe-graded with grader v{GRADER_VERSION}; "
        f"{len(changes)} trial(s) changed. Not re-graded (ticket changed since the run): "
        f"{', '.join(sorted(skipped)) or 'none'}.\n")
    print(markdown(summary, meta))
    if skipped:
        print("skipped (ticket changed since run):", ", ".join(sorted(skipped)))
    for c in changes:
        print(f"changed: {c['file']}: {c['old_score']} -> {c['new_score']}")


if __name__ == "__main__":
    main(sys.argv[1])

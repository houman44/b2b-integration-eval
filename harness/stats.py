"""Aggregate graded trials into the results table."""
from collections import defaultdict

FIELDS = ("cause", "layer", "owner", "location", "next_check", "value")


def summarise(rows):
    """rows: dicts with model, ticket, trial, grade (or None on API error), cost."""
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)
    out = {}
    for model, rs in by_model.items():
        graded = [r for r in rs if r["grade"] is not None]
        tickets = sorted({r["ticket"] for r in rs})
        per_ticket = {}
        for t in tickets:
            tr = [r for r in graded if r["ticket"] == t]
            passes = [r["grade"]["pass"] for r in tr]
            per_ticket[t] = {
                "trials": len(tr),
                "passes": sum(passes),
                "mean_score": round(sum(r["grade"]["score"] for r in tr) / len(tr), 4) if tr else None,
                "diagnosis_passes": sum(r["grade"].get("diagnosis_pass", r["grade"]["pass"]) for r in tr),
                "fields": {f: sum(r["grade"]["fields"].get(f, {}).get("correct", False) for r in tr)
                           for f in FIELDS},
                "parse_errors": sum(r["grade"]["parse_error"] is not None for r in tr),
            }
        complete = [t for t in tickets if per_ticket[t]["trials"] > 0]
        k_values = sorted({per_ticket[t]["trials"] for t in complete})
        out[model] = {
            "trials": len(graded),
            "api_errors": len(rs) - len(graded),
            "trials_per_task": k_values[0] if len(k_values) == 1 else k_values,
            "pass_rate": round(sum(r["grade"]["pass"] for r in graded) / len(graded), 4) if graded else None,
            "mean_score": round(sum(r["grade"]["score"] for r in graded) / len(graded), 4) if graded else None,
            "pass_at_k": round(sum(per_ticket[t]["passes"] > 0 for t in complete) / len(complete), 4) if complete else None,
            "pass_hat_k": round(sum(per_ticket[t]["passes"] == per_ticket[t]["trials"] for t in complete) / len(complete), 4) if complete else None,
            "diagnosis_pass_rate": round(sum(r["grade"].get("diagnosis_pass", r["grade"]["pass"]) for r in graded) / len(graded), 4) if graded else None,
            "field_accuracy": {f: round(sum(r["grade"]["fields"].get(f, {}).get("correct", False) for r in graded) / len(graded), 4) if graded else None for f in FIELDS},
            "cost_usd": round(sum(r.get("cost") or 0 for r in rs), 6),
            "per_ticket": per_ticket,
        }
    return out


def markdown(summary, meta):
    lines = [f"# Run {meta['run_id']}", "",
             f"Date (UTC): {meta['started_utc']}  ",
             f"Tickets: {', '.join(meta['tickets'])} ({'DRAFT tickets' if meta['draft'] else 'release tickets'})  ",
             f"Temperature: {meta['temperature']}, max_tokens: {meta['max_tokens']}, trials per task: {meta['trials']}",
             "", "| Model | Trials | Pass rate (all keys) | Diagnosis pass | Mean score | pass@k | pass^k | cause | layer | owner | location | next_check | value | Cost (USD) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, s in summary.items():
        fa = s["field_accuracy"]
        lines.append(f"| {m} | {s['trials']} | {s['pass_rate']} | {s['diagnosis_pass_rate']} | "
                     f"{s['mean_score']} | {s['pass_at_k']} | {s['pass_hat_k']} | {fa['cause']} | "
                     f"{fa['layer']} | {fa['owner']} | {fa['location']} | {fa['next_check']} | {fa['value']} | "
                     f"{s['cost_usd']:.4f} |")
    lines += ["", "## Per ticket (passes / trials)", ""]
    for m, s in summary.items():
        cells = ", ".join(f"{t} {v['passes']}/{v['trials']}" for t, v in s["per_ticket"].items())
        lines.append(f"- {m}: {cells}")
    return "\n".join(lines) + "\n"

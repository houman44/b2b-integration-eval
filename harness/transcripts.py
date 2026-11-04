"""Write readable transcripts of selected release trials to transcripts/.

  python -m harness.transcripts

Each transcript is rendered from a raw result file, which stays the record. Long replies
and long tool results are shortened in the middle, with the number of characters left
out; the raw file holds everything. Diagnosis grades are the grader 3.1 re-grade of the
release run (regrade_v3.1.json), so R2 is scored with both accepted layers.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "transcripts"
DIAG = "results/runs/20261104T051655Z-23835a"
TR1 = "results/translation/20261104T053945Z-6676f6"
TR2 = "results/translation/20261104T054031Z-b2d9bd"
SFTP = "results/sftp/20261104T054236Z-3888ad"
AGENT = "results/agentic/20261104T054441Z-83fb9d"
MAX_REPLY = 12000
MAX_TOOL = 1500

# (mode, run, file stem, why it was chosen)
SELECTION = [
    ("diagnosis", DIAG, "T1__google__gemini-4-argon__t1", "T1 had no failures; one pass"),
    ("diagnosis", DIAG, "T2__deepseek__deepseek-v4.1-flash-1017__t1", "failure: reply ran to the token limit"),
    ("diagnosis", DIAG, "E1__anthropic__claude-haiku-5.5__t2", "failure: no sender-side fault found"),
    ("diagnosis", DIAG, "E3__anthropic__claude-fable-5.1__t1", "E3 had no failures; one pass"),
    ("diagnosis", DIAG, "R1__deepseek__deepseek-v4.1-flash-1017__t2", "failure: reply ran to the token limit"),
    ("diagnosis", DIAG, "R2__openai__gpt-6-astra__t1", "layer 'envelope': failed before the R2 ruling, passes after it"),
    ("diagnosis", DIAG, "S1__anthropic__claude-haiku-5.5__t1", "near miss: location without the APP. prefix"),
    ("diagnosis", DIAG, "U1__anthropic__claude-haiku-5.5__t2", "failure: definite cause where the evidence does not decide"),
    ("diagnosis", DIAG, "U2__anthropic__claude-haiku-5.5__t2", "failure: definite cause where the evidence does not decide"),
    ("diagnosis", DIAG, "U2__google__gemini-3.8-flash__t3", "failure: reply ran to the token limit"),
    ("diagnosis", DIAG, "U2__anthropic__claude-sonnet-5.5__t1", "pass on the hardest ticket for small models"),
    ("diagnosis", DIAG, "U5__anthropic__claude-haiku-5.5__t1", "near miss: location as a bare string"),
    ("translation", TR1, "X1__openai__gpt-6-astra__t1", "X1 had no failures; one pass"),
    ("translation", TR1, "X2__anthropic__claude-haiku-5.5__t2", "near miss: party name cut at 34 characters instead of the 35 allowed"),
    ("translation", TR2, "X2__google__gemini-3.8-flash__t1", "failure: implied decimals misread, amounts and price a factor of 10 off"),
    ("translation", TR2, "X2__anthropic__claude-fable-5.1__t1", "no output: provider content filter"),
    ("sftp", SFTP, "Z1__anthropic__claude-sonnet-5.5__t1", "Z1 had no failures; one pass"),
    ("sftp", SFTP, "Z2__openai__gpt-6-astra__t1", "Z2 had no failures; one pass"),
    ("agentic", AGENT, "U2__google__gemini-4-argon__t1", "agentic pass: workspace search on a not-yet-determinable ticket"),
]


def clip(text, limit, where):
    text = text or ""
    if len(text) <= limit:
        return text
    head, tail = text[: limit * 2 // 3], text[-limit // 3:]
    return (f"{head}\n\n[... {len(text) - len(head) - len(tail)} characters left out here; "
            f"full text in {where} ...]\n\n{tail}")


def fence(text, lang=""):
    ticks = "````" if "```" in (text or "") else "```"
    return f"{ticks}{lang}\n{(text or '').rstrip()}\n{ticks}\n"


def field_table(fields):
    rows = ["| Key | Given | Expected | Correct |", "|---|---|---|---|"]
    for k, v in fields.items():
        rows.append(f"| {k} | `{json.dumps(v.get('given'))}` | `{json.dumps(v.get('expected'))}` | "
                    f"{'yes' if v.get('correct') else 'no'} |")
    return "\n".join(rows) + "\n"


def messages_md(messages, where):
    out = []
    for m in messages[1:]:                       # the first message is the task prompt
        role = m.get("role")
        if role == "assistant":
            if m.get("content"):
                out.append("**Model:**\n\n" + fence(clip(m["content"], MAX_REPLY, where)))
            for c in m.get("tool_calls") or []:
                fn = c.get("function", {})
                out.append(f"**Tool call** `{fn.get('name')}`:\n\n" + fence(fn.get("arguments", ""), "json"))
        elif role == "tool":
            out.append("**Tool result:**\n\n" + fence(clip(str(m.get("content")), MAX_TOOL, where)))
        elif role == "user":
            out.append("**Harness:**\n\n" + fence(clip(str(m.get("content")), MAX_TOOL, where)))
    return "\n".join(out)


def render(mode, run, stem, why, regrade):
    raw = ROOT / run / "raw" / f"{stem}.json"
    d = json.loads(raw.read_text())
    rel = raw.relative_to(ROOT).as_posix()
    task = d.get("ticket") or d.get("task")
    lines = [f"# {task}, {d['model']}, trial {d['trial']}", "",
             f"- Mode: {mode}", f"- Why this transcript: {why}", f"- Raw record: `{rel}`",
             f"- Cost: {d.get('cost_usd')} USD"]
    if mode == "diagnosis":
        g = regrade.get(stem) or d["grade"]
        lines += [f"- Task prompt (exactly what the model saw): `tasks/{task}/prompt.md`, "
                  f"sha256 `{d['request']['messages'][0]['content_sha256']}`",
                  f"- finish_reason: {d.get('finish_reason')}",
                  f"- Grade (grader 3.1): score {g['score']:.2f}, pass {g['pass']}"]
        if d["grade"] and d["grade"]["pass"] != g["pass"]:
            lines.append(f"- Graded at run time (grader 3.0): score {d['grade']['score']:.2f}, "
                         f"pass {d['grade']['pass']}")
        lines += ["", "## Reply", "", fence(clip(d.get("response_text"), MAX_REPLY, rel))]
        if not (d.get("response_text") or "").strip() and d.get("reasoning"):
            lines += ["## Reasoning", "",
                      f"The reply text is empty: all {d['usage']['completion_tokens']} completion "
                      f"tokens went to reasoning before the limit. The reasoning as returned:", "",
                      fence(clip(d["reasoning"], MAX_REPLY, rel))]
        lines += ["## Grade", "", field_table(g["fields"])]
    elif mode == "translation":
        g = d.get("grade") or {}
        lines += [f"- Task prompt: `tasks-translation/{task}/prompt.md`",
                  f"- finish_reason: {d.get('finish_reason')}",
                  f"- Grade: score {g.get('score')}, pass {g.get('pass')}", "", "## Reply", "",
                  fence(clip(d.get("response_text"), MAX_REPLY, rel)), "## Grade", "",
                  fence(json.dumps(g, indent=2), "json")]
    else:
        lines += [f"- Tool calls: {d.get('tool_calls')}",
                  f"- Pass: {d.get('pass')}"]
        if mode == "sftp":
            lines.append(f"- End-state checks: `{json.dumps(d.get('checks'))}`")
        else:
            lines.append(f"- Grade: score {d['grade']['score']:.2f}, pass {d['grade']['pass']}")
        lines += ["", "## Episode", "", "The first message (the task) is in the raw record.", "",
                  messages_md(d["messages"], rel)]
        if mode == "agentic":
            lines += ["## Grade", "", field_table(d["grade"]["fields"])]
    return task, d["model"], "\n".join(lines).rstrip() + "\n"


def main():
    rg = json.loads((ROOT / DIAG / "regrade_v3.1.json").read_text())
    regrade = {f"{r['ticket']}__{r['model'].replace('/', '__')}__t{r['trial']}": r["grade"]
               for r in rg["grades"]}
    OUT.mkdir(exist_ok=True)
    index = ["# Representative transcripts", "",
             "Rendered by `python -m harness.transcripts` from the raw records of the release runs "
             "(4 November 2026). Long replies are shortened in the middle; the raw record holds the "
             "full text.", "", "| Transcript | Mode | Model | Why |", "|---|---|---|---|"]
    for mode, run, stem, why in SELECTION:
        task, model, text = render(mode, run, stem, why, regrade)
        name = f"{mode}-{stem}.md"
        (OUT / name).write_text(text, encoding="utf-8")
        index.append(f"| [{task}]({name}) | {mode} | {model} | {why} |")
    (OUT / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"{len(SELECTION)} transcripts in {OUT}")


if __name__ == "__main__":
    main()

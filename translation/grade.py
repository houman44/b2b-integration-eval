"""Exact-output grader for the translation tasks.

edifact: the last ```edifact block is split into segments (unescaped '),
  line breaks ignored, and compared with the expected segments. pass = identical
  list; score = 2*LCS/(expected+given) over whole segments (partial credit for
  every exactly right segment, penalising missing and extra ones).
json: the last ```json block is parsed and compared with the expected object.
  pass = deep equality (numbers compared by value); score = F1 over (path, value)
  leaves.
"""
import json
from difflib import SequenceMatcher

from graders.grade import fenced_blocks
from .edifact import split_segments

GRADER_VERSION = "t1.0"


def _last_block(text, lang):
    blocks = fenced_blocks(text)
    hits = [b for l, b in blocks if l == lang]
    return hits[-1] if hits else None


def _lcs(a, b):
    return sum(m.size for m in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())


def _leaves(x, path=""):
    if isinstance(x, dict):
        out = {(path + "/" + k + "#"): None for k in x} if not x else {}
        for k, v in x.items():
            out.update(_leaves(v, f"{path}/{k}"))
        return out
    if isinstance(x, list):
        out = {f"{path}#len": len(x)}
        for i, v in enumerate(x):
            out.update(_leaves(v, f"{path}[{i}]"))
        return out
    if isinstance(x, bool) or x is None or isinstance(x, str):
        return {path: x}
    return {path: float(x)}


def grade_translation(text, task_ref):
    kind, expected = task_ref["kind"], task_ref["expected"]
    res = {"ticket": task_ref["id"], "grader_version": GRADER_VERSION, "parse_error": None}
    if kind == "edifact":
        block = _last_block(text, "edifact")
        if block is None:
            res.update(score=0.0, passed=False, parse_error="no ```edifact block")
        else:
            got = split_segments(block)
            l = _lcs(got, expected)
            res.update(score=round(2 * l / (len(got) + len(expected)), 4), passed=got == expected,
                       segments_expected=len(expected), segments_given=len(got),
                       wrong=[s for s in got if s not in expected][:10],
                       missing=[s for s in expected if s not in got][:10])
    else:
        block = _last_block(text, "json")
        try:
            got = json.loads(block) if block is not None else None
        except json.JSONDecodeError:
            got = None
        if got is None:
            res.update(score=0.0, passed=False, parse_error="no valid ```json block")
        else:
            e, g = _leaves(expected), _leaves(got)
            tp = sum(1 for k, v in g.items() if k in e and e[k] == v)
            prec, rec = (tp / len(g) if g else 0), (tp / len(e) if e else 0)
            res.update(score=round(2 * prec * rec / (prec + rec), 4) if tp else 0.0,
                       passed=e == g,
                       wrong=[k for k, v in g.items() if e.get(k, object()) != v][:10],
                       missing=[k for k in e if k not in g][:10])
    res["pass"] = res.pop("passed")
    return res

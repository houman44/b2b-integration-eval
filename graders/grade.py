"""Exact-match grader for ticket answers.

  python -m graders.grade --ticket T1 --response reply.txt

Rules (all stated in every prompt):
* The last ```json block in the reply is graded. Fallbacks, so a correct
  answer is not failed on format: if there is no fence, the whole reply,
  then the last JSON object found in the text.
* cause, layer, owner: one string each, compared case-insensitively after
  turning spaces and hyphens into underscores. A list, or a value that is
  not exactly one allowed option, scores zero for that field.
* location: a list of 1 to MAX_LOCATIONS strings, normalised (case,
  separators, bare OFTP2 field names, unambiguous EDIFACT components) and
  compared as a set with the reference. A superset (hedging) or a subset
  scores zero.
* Score = fraction of the four fields correct (partial credit);
  pass = all four correct.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from .schema import CAUSES, CHECKS, EDIFACT_SEGMENTS, LAYERS, MAX_LOCATIONS, OFTP2_FIELDS, OWNERS

FIELDS = ("cause", "layer", "owner", "location", "next_check", "value")
DIAGNOSIS = ("cause", "layer", "owner", "location", "next_check")
ALLOWED = {"cause": set(CAUSES), "layer": set(LAYERS), "owner": set(OWNERS),
           "next_check": set(CHECKS)}

GRADER_VERSION = "3.1"   # 3.1: any enum key may list accepted values; 3.0: next_check key, undetermined causes; 2.0: value; 1.1: fences

FENCE_OPEN = re.compile(r"^\s*```[ \t]*([A-Za-z0-9_+-]*)[ \t]*$")
FENCE_CLOSE = re.compile(r"^\s*```[ \t]*$")
INLINE_JSON_FENCE = re.compile(r"```[ \t]*json[ \t]*(\{.*?\})[ \t]*```", re.S | re.I)
SEP = re.compile(r"[\s/:+>\-]+|\.+")

FIELD_TO_CMD = {f: cmd for cmd, fs in OFTP2_FIELDS.items() for f in fs}


def _component_parents():
    """(segment, component) -> composite, only where the component occurs in
    exactly one composite of that segment."""
    seen = {}
    for seg, elems in EDIFACT_SEGMENTS.items():
        for comp_parent, comps in elems.items():
            for c in comps:
                seen.setdefault((seg, c), []).append(comp_parent)
    return {k: v[0] for k, v in seen.items() if len(v) == 1}


COMPONENT_PARENT = _component_parents()


def fenced_blocks(text: str):
    """Return [(language, body)] for every fenced block, pairing each opening
    fence line with the next closing fence line."""
    blocks, lang, buf = [], None, []
    for line in text.splitlines():
        if lang is None:
            m = FENCE_OPEN.match(line)
            if m:
                lang, buf = m.group(1).lower(), []
        elif FENCE_CLOSE.match(line):
            blocks.append((lang, "\n".join(buf)))
            lang = None
        else:
            buf.append(line)
    return blocks


def _last_object(text: str):
    dec = json.JSONDecoder()
    found = None
    for m in re.finditer(r"\{", text):
        try:
            obj, _ = dec.raw_decode(text, m.start())
            if isinstance(obj, dict):
                found = obj
        except json.JSONDecodeError:
            continue
    return found


def extract_answer(text: str):
    """Return (dict, None) or (None, error). The last ```json block is graded;
    if there is none, the last unlabelled block that is a JSON object; then a
    one-line ```json {...}``` fence; then the last JSON object in the text."""
    blocks = fenced_blocks(text)
    json_blocks = [b for lang, b in blocks if lang == "json"]
    if json_blocks:
        try:
            obj = json.loads(json_blocks[-1].strip())
        except json.JSONDecodeError:
            return None, "last ```json block is not valid JSON"
        return (obj, None) if isinstance(obj, dict) else (None, "graded JSON is not an object")
    for lang, b in reversed(blocks):
        if lang == "":
            try:
                obj = json.loads(b.strip())
                if isinstance(obj, dict):
                    return obj, None
            except json.JSONDecodeError:
                pass
    inline = INLINE_JSON_FENCE.findall(text)
    if inline:
        try:
            return json.loads(inline[-1]), None
        except json.JSONDecodeError:
            pass
    try:
        obj = json.loads(text.strip())
        if isinstance(obj, dict):
            return obj, None
    except json.JSONDecodeError:
        pass
    found = _last_object(text)
    if found is None:
        return None, "no JSON object found"
    return found, None


def norm_enum(value, allowed):
    if not isinstance(value, str):
        return None, "not a single string"
    v = re.sub(r"[\s\-]+", "_", value.strip().lower())
    if v not in allowed:
        return None, "not exactly one allowed value"
    return v, None


def norm_location_token(tok: str) -> str:
    t = SEP.sub(".", tok.strip().upper()).strip(".")
    if t in ("NONE", "UNDETERMINED"):
        return t
    parts = t.split(".")
    if len(parts) == 1 and t in FIELD_TO_CMD:
        return f"{FIELD_TO_CMD[t]}.{t}"
    if len(parts) == 2 and parts[0] in EDIFACT_SEGMENTS and (parts[0], parts[1]) in COMPONENT_PARENT:
        return f"{parts[0]}.{COMPONENT_PARENT[(parts[0], parts[1])]}.{parts[1]}"
    return t


def norm_location(value):
    if isinstance(value, str):
        return None, "location must be a JSON array"
    if not isinstance(value, list) or not value:
        return None, "location must be a non-empty JSON array"
    if len(value) > MAX_LOCATIONS:
        return None, f"more than {MAX_LOCATIONS} locations"
    if not all(isinstance(x, str) for x in value):
        return None, "location entries must be strings"
    toks = {norm_location_token(x) for x in value}
    for solo in ("NONE", "UNDETERMINED"):
        if solo in toks and len(toks) > 1:
            return None, f"{solo} combined with other locations"
    return sorted(toks), None


def norm_value(value, kind):
    """value is compared exactly after a normalisation that depends on its kind:
    int: an integer (digits only, leading zeros and thousands separators ignored);
    string: surrounding space removed, inner runs of space collapsed, upper case;
    segment: surrounding space removed, one segment terminator ensured."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None, "value must be a single string"
    v = str(value).strip()
    if kind == "int":
        digits = v.replace(",", "").replace(" ", "")
        if not digits.isdigit():
            return None, "value is not a plain integer"
        return str(int(digits)), None
    if kind == "segment":
        if "\n" in v:
            return None, "value holds more than one line"
        return (v if v.endswith("'") else v + "'"), None
    return " ".join(v.split()).upper(), None


def grade(response_text: str, reference: dict) -> dict:
    expected = reference["answer"]
    result = {"ticket": reference.get("id"), "grader_version": GRADER_VERSION,
              "parse_error": None, "fields": {}}
    obj, err = extract_answer(response_text)
    if err:
        result["parse_error"] = err
        obj = {}
    kind = reference.get("value_kind", "string")
    for f in FIELDS:
        if f not in expected:
            continue
        exp = sorted(expected[f]) if f == "location" else expected[f]
        if f == "value":
            exp = norm_value(exp, kind)[0]
        if f not in obj:
            given, ferr = None, "missing"
        elif f == "location":
            given, ferr = norm_location(obj[f])
        elif f == "value":
            given, ferr = norm_value(obj[f], kind)
        else:
            given, ferr = norm_enum(obj[f], ALLOWED[f])
        if f in ALLOWED and isinstance(exp, list):   # several accepted values (e.g. R2 layer)
            ok = ferr is None and given in exp
        else:
            ok = ferr is None and given == exp
        result["fields"][f] = {
            "given": obj.get(f), "normalised": given, "expected": exp,
            "correct": ok, "error": ferr,
        }
    n = sum(v["correct"] for v in result["fields"].values())
    result["score"] = n / len(result["fields"])
    result["pass"] = n == len(result["fields"])
    result["diagnosis_pass"] = all(result["fields"][f]["correct"] for f in DIAGNOSIS)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", required=True)
    ap.add_argument("--response", required=True, help="file with the model's reply, or - for stdin")
    ap.add_argument("--reference-dir", default=str(Path(__file__).resolve().parent.parent / "reference"))
    a = ap.parse_args(argv)
    ref = json.loads((Path(a.reference_dir) / f"{a.ticket}.json").read_text())
    text = sys.stdin.read() if a.response == "-" else Path(a.response).read_text()
    print(json.dumps(grade(text, ref), indent=2))


if __name__ == "__main__":
    main()

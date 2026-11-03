"""Write tasks-translation/<id>/prompt.md and reference-translation/<id>.json.

  python -m translation.build [--check]
"""
import json
import sys
from pathlib import Path

from .tasks import TASKS

ROOT = Path(__file__).resolve().parent.parent


def build_all():
    out = {}
    for tid, fn in TASKS.items():
        t = fn()
        out[f"tasks-translation/{tid}/prompt.md"] = f"# Translation task {tid}\n\n" + t.prompt_body
        out[f"reference-translation/{tid}.json"] = json.dumps(
            {"id": tid, "kind": t.out_kind, "expected": t.expected, "rationale": t.rationale},
            indent=2, ensure_ascii=False) + "\n"
    return out


def main(argv=None):
    out = build_all()
    if argv and "--check" in argv:
        bad = [p for p, t in out.items() if (ROOT / p).read_text(encoding="utf-8") != t]
        sys.exit(("differs: " + ", ".join(bad)) if bad else print(f"check ok: {len(out)} files"))
    for p, t in out.items():
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_text(t, encoding="utf-8")
    print("wrote", ", ".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])

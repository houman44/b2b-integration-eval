"""One command for the whole evaluation.

  python run_all.py                  free: rebuild and check every task, run the tests,
                                     print the cost estimate of the release runs
  python run_all.py --confirm-spend  also run the release suite exactly as reported in the
                                     README (about 21 USD and 30 minutes on OpenRouter)

The release suite: diagnosis (10 tickets x 3 trials) for seven models, translation and SFTP
remediation (2 trials) for the same models, and agentic diagnosis (1 trial) for gemini-4-argon.
Each step stops at its own --max-cost. Diagnosis can be continued with
python run_eval.py --resume <run directory> if it is interrupted.
"""
import subprocess
import sys

MODELS = ("google/gemini-4-argon,anthropic/claude-fable-5.1,openai/gpt-6-astra,"
          "anthropic/claude-sonnet-5.5,google/gemini-3.8-flash,anthropic/claude-haiku-5.5,"
          "deepseek/deepseek-v4.1-flash-1017")
TICKETS = "E1,E3,R1,R2,S1,T1,T2,U1,U2,U5"
PY = sys.executable

FREE = [
    [PY, "-m", "generator.build", "--release", "--check"],
    [PY, "-m", "translation.build", "--check"],
    [PY, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
    [PY, "run_eval.py", "--models", MODELS, "--trials", "3", "--dry-run"],
]
# parallel 4: OpenRouter reserves credit for every request in flight, and ten parallel
# requests to an expensive model were refused with HTTP 402 in the release run.
PAID = [
    [PY, "run_eval.py", "--models", MODELS, "--trials", "3", "--parallel", "4",
     "--timeout", "300", "--max-cost", "30", "--confirm-spend"],
    [PY, "run_translation.py", "--models", MODELS, "--trials", "2", "--parallel", "4",
     "--max-cost", "2", "--confirm-spend"],
    [PY, "run_sftp.py", "--models", MODELS, "--trials", "2", "--parallel", "4",
     "--max-cost", "5", "--confirm-spend"],
    [PY, "run_agentic.py", "--models", "google/gemini-4-argon", "--tickets", TICKETS,
     "--trials", "1", "--parallel", "4", "--max-cost", "3", "--confirm-spend"],
]


def main(argv):
    steps = FREE + (PAID if "--confirm-spend" in argv else [])
    for cmd in steps:
        print("\n$ " + " ".join(c if "," not in c else f'"{c}"' for c in cmd[1:]), flush=True)
        if subprocess.run(cmd).returncode != 0:
            sys.exit(f"step failed: {' '.join(cmd[1:3])}")
    if "--confirm-spend" not in argv:
        print("\nAll checks passed. Add --confirm-spend to run the release suite.")


if __name__ == "__main__":
    main(sys.argv[1:])

"""Run the unchanged browser_form_agent.py five times and save evidence per run.

Usage (from the repository root, with Ollama running):
    python google_harness_extra_credit/run_experiments.py

Each run is a separate Python process, so every run launches a brand-new
Chromium browser and loads the form fresh (the "reset"). The agent itself
is not modified. After each run this script copies the agent's
run_trace.txt and browser_success.png into evidence/ before the next run
overwrites them.
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
AGENT = REPO_ROOT / "browser_form_agent.py"
EVIDENCE = HERE / "evidence"
NUM_RUNS = 5

EVIDENCE.mkdir(exist_ok=True)
rows = []

for run in range(1, NUM_RUNS + 1):
    print("\n========== RUN", run, "of", NUM_RUNS, "==========")

    # Remove old outputs so a crashed run cannot reuse the previous run's files.
    for name in ["run_trace.txt", "browser_success.png"]:
        old = REPO_ROOT / name
        if old.exists():
            old.unlink()

    start = time.time()
    # input="\n" presses Enter at the agent's final "close the browser" prompt.
    proc = subprocess.run(
        [sys.executable, str(AGENT)],
        cwd=REPO_ROOT,
        input="\n",
        capture_output=True,
        text=True,
        timeout=900,
    )
    seconds = round(time.time() - start)
    console = proc.stdout + "\n--- STDERR ---\n" + proc.stderr
    print(proc.stdout[-1500:])

    (EVIDENCE / ("run_" + str(run) + "_console.txt")).write_text(console, encoding="utf-8")
    for name, new_name in [("run_trace.txt", "_trace.txt"), ("browser_success.png", "_final.png")]:
        src = REPO_ROOT / name
        if src.exists():
            shutil.copy(src, EVIDENCE / ("run_" + str(run) + new_name))

    stop_reason = "unknown"
    for line in proc.stdout.splitlines():
        if line.startswith("STOP REASON:"):
            stop_reason = line.split(":", 1)[1].strip()

    rejected_done = proc.stdout.count("FINAL CHECK: Not")
    steps = proc.stdout.count("STEP ")
    result = "Success" if stop_reason == "success" else "Failure"
    rows.append((run, result, stop_reason, steps, rejected_done, seconds))

lines = ["| Run | Success or Failure | Notes |", "|---|---|---|"]
for run, result, stop_reason, steps, rejected_done, seconds in rows:
    notes = ("stop reason: " + stop_reason + "; ~" + str(steps) + " steps; "
             + str(seconds) + "s; rejected `done`: " + str(rejected_done)
             + ". <ADD WHAT HAPPENED, e.g. name-field trap caught?> "
             + "[trace](evidence/run_" + str(run) + "_trace.txt) · "
             + "[console](evidence/run_" + str(run) + "_console.txt) · "
             + "[screenshot](evidence/run_" + str(run) + "_final.png)")
    lines.append("| " + str(run) + " | " + result + " | " + notes + " |")

table = "\n".join(lines)
(EVIDENCE / "results_table.md").write_text(table + "\n", encoding="utf-8")
print("\nPaste into README.md:\n")
print(table)

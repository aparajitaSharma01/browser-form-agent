# Google AI Harness Crash Course: Evaluating My Browser Form Agent

**Student:** Aparajita Sharma · **Course:** CSYE 7374, Introduction to Agentic AI

Agent tested: `browser_form_agent.py` (unchanged), which uses Qwen3 8B via local Ollama.
Task: fill out and submit the practice form at https://onyourmark.github.io/browser-agent-form/ with Name = "Alex Student", Email = "alex@example.com", Program = "MS Information Systems", and the agreement box checked.

## Step 1: Connection to Google's harness idea

Google's course describes the *harness* as everything around the model that makes an agent reliable: the tools it can use, the state it keeps, the control loop, the checks that block bad actions, and the evaluation of whether it actually succeeded. My form agent is a small harness. The model only proposes one JSON action at a time. Python parses it, validates it against the allowed actions and arguments, runs exactly one Playwright action, and reads the real page back with `observe_form()`. It then runs a deterministic check on what happened and feeds the observation and check result to the model for its next decision, within a `MAX_STEPS` budget. The model can say `done`, but Python decides whether the task really succeeded. That separation between model proposals and harness-enforced verification is the core idea of Google's harness engineering.

## Step 2: How success is determined

The model's `done` is only a *request* to stop. When it arrives, Python runs `check_final_success()`, which reads the live page with `observe_form()` and accepts success only if **all** of these hold:

1. The result section (`#result`) is visible, meaning the form was actually submitted.
2. The result section contains the text "FORM SUBMITTED SUCCESSFULLY".
3. The submitted values shown on the page match the expected values exactly: Name = `Alex Student`, Email = `alex@example.com`, Program = `MS Information Systems`.
4. The submitted Agreement text contains a word showing the box was checked (`yes`, `checked`, `true`, `agreed` or `confirmed`).

If any condition fails, Python rejects the `done`, sends the list of problems back to the model, and the loop continues. Each individual action is also checked right after it runs by `check_action()`. For example, after `fill_name` Python reads the field back and compares it to "Alex Student". A run is a **failure** if it ends without passing the final check: it ran out of steps (`budget_exceeded`, `MAX_STEPS = 12`), Ollama was unreachable, or Ollama returned an HTTP error.

## Step 3: Five experiments

**Procedure.** `run_experiments.py` ran the unchanged agent five times, each as a separate process. **Reset:** each run launches a new Chromium browser and loads the form from scratch. The form keeps no server-side state, so this fully resets it. After each run, the script saved the console output, `run_trace.txt` and the final screenshot to `evidence/`.

| Run | Success or Failure | Notes |
|---|---|---|
| 1 | Success | 7 model calls, 30s. Every action passed its check on the first try: open form, fill the four fields, submit, done. `done` accepted on the first request, with all submitted values correct. Slowest run, likely because the model was loading into memory. [trace](evidence/run_1_trace.txt) · [console](evidence/run_1_console.txt) · [screenshot](evidence/run_1_final.png) |
| 2 | Success | 7 model calls, 19s. Same path as run 1, with no parse errors, validation errors, failed checks or rejected `done`. [trace](evidence/run_2_trace.txt) · [console](evidence/run_2_console.txt) · [screenshot](evidence/run_2_final.png) |
| 3 | Success | 7 model calls, 18s. Same path, with no errors or rejected `done`. [trace](evidence/run_3_trace.txt) · [console](evidence/run_3_console.txt) · [screenshot](evidence/run_3_final.png) |
| 4 | Success | 7 model calls, 17s. Same path, with no errors or rejected `done`. [trace](evidence/run_4_trace.txt) · [console](evidence/run_4_console.txt) · [screenshot](evidence/run_4_final.png) |
| 5 | Success | 7 model calls, 17s. Same path, with no errors or rejected `done`. [trace](evidence/run_5_trace.txt) · [console](evidence/run_5_console.txt) · [screenshot](evidence/run_5_final.png) |

**Result: 5/5 successes.** Each run used the minimum possible number of model calls (7 of the 12 allowed).

**Evidence:** `evidence/run_N_trace.txt`, `evidence/run_N_console.txt`, `evidence/run_N_final.png`.

## Step 4: Findings

All five runs succeeded, and they behaved almost identically. Each one took exactly seven model calls: open the form, fill Name, Email and Program, check the agreement, submit, then `done`. Seven is the minimum the task allows, so the model never wasted a step. No reply failed to parse, no proposal failed validation, every per-action check passed on the first try, and Python accepted `done` the first time it was requested. Apart from the first run being slower (30s versus about 17–19s, likely the model loading into memory), the five traces are essentially the same. On this form, with these instructions, the agent's happy path is very stable.

**Limitation.** The main limitation is that these five runs never exercised the harness's error-handling paths. In my original homework run, the form cleared the Name field after a submit, and Python correctly rejected the model's premature `done`. That trap did not occur in any of these five runs, so these experiments show the agent succeeds when nothing goes wrong, but not how well it recovers. The test also used one fixed form, one fixed set of values and a healthy network, and five runs is a small sample for a nondeterministic model.

Reviewing the code for this report also showed a gap in the success check. `check_final_success()` verifies the *displayed* submitted values but does not record whether a field was changed after the last submit. If the model edited a field and then said `done` without resubmitting, the check might still pass. A stronger evaluation would add test cases for these situations: a field changed after submitting, a misleading "success" message on the page, a missing or renamed field, and a slow-loading page. Each would be run many times.
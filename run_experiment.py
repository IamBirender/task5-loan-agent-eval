"""Run a whole experiment: every case set through steps 1-6, one set after the other.

  Experiment 1 = our 50 case sets (set01 ... set50): 50 x 73 = 3,650 test cases, each set with its own 8-loan pool
  Experiment 2 = the senior's unique test cases (senior_unique): 1,173 cases on the original 8-loan sample

For each set it sets CASE_SET for the steps (you do NOT edit .env per set), runs
  step1 (check data) -> step2 (check answer key) -> step3 (agents) -> step4 (Arize AX) -> step5 (Braintrust) -> step6 (results)
and stops at the first step that fails, so nothing is half-graded. Run the same command again to continue: finished sets are
skipped, and step 3 skips the cases it already answered. At the end it writes results/experiment<N>_summary.md.

Usage:  python run_experiment.py 1                      # experiment 1, all 50 sets
        python run_experiment.py 2                      # experiment 2
        python run_experiment.py 1 --sets set01 set02   # only some sets
        python run_experiment.py 1 --dry                # free wiring check: no AI model is called (steps 1-3 only)
        python run_experiment.py 1 --summary            # only rebuild the combined summary
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from loan_agents import models  # noqa: E402  (reads .env: MODEL_PROVIDER, AGENT_VERSION)

EXPERIMENTS = {"1": [f"set{n:02d}" for n in range(1, 51)], "2": ["senior_unique"]}

ap = argparse.ArgumentParser()
ap.add_argument("experiment", choices=sorted(EXPERIMENTS))
ap.add_argument("--sets", nargs="*", help="only these sets (default: all sets of the experiment)")
ap.add_argument("--dry", action="store_true", help="MODEL_PROVIDER=dryrun, steps 1-3 only: checks the wiring for free")
ap.add_argument("--summary", action="store_true", help="only rebuild the combined summary from finished sets")
ap.add_argument("--redo", action="store_true", help="run sets again even if they already have results")
args = ap.parse_args()
sets = args.sets or EXPERIMENTS[args.experiment]
provider = "dryrun" if args.dry else models.PROVIDER


def folder(s):
    return HERE / "results" / f"{provider}-{models.AGENT_VERSION}-{s}"


def run_set(s):
    env = {**os.environ, "CASE_SET": s, "PYTHONIOENCODING": "utf-8"}
    steps = ["step1_get_data.py", "step2_check_answer_key.py", "step3_run_agents.py"]
    if args.dry:
        env["MODEL_PROVIDER"] = "dryrun"
    else:
        steps += ["step4_score_arize.py", "step5_score_braintrust.py", "step6_build_results.py"]
    for step in steps:
        t0 = time.time()
        log = folder(s) / f"{step.split('_')[0]}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("w", encoding="utf-8") as out:
            code = subprocess.run([sys.executable, step], cwd=HERE, env=env, stdout=out, stderr=subprocess.STDOUT).returncode
        print(f"  {s} {step:30} {'ok' if code == 0 else 'FAILED'} ({time.time() - t0:.0f} s)", flush=True)
        if code != 0:
            print(f"\nStopped: {step} failed for {s}. Read {log.relative_to(HERE)}, fix the cause, then run the same command again.")
            sys.exit(1)


def summary():
    rows, totals = [], {"cases": 0, "Arize AX": 0, "Braintrust": 0, "cost": 0.0, "minutes": 0.0}
    for s in sets:
        f = folder(s)
        sc = {n: json.loads((f / fn).read_text(encoding="utf-8")) for n, fn in [("Arize AX", "arize_scores.json"), ("Braintrust", "braintrust_scores.json")]
              if (f / fn).exists()}
        if len(sc) < 2:
            rows.append(f"| {s} | not finished | | | | |")
            continue
        runs = [json.loads(line) for line in (f / "agent_runs.jsonl").open(encoding="utf-8")]
        n = len(sc["Arize AX"]["cases"])
        p = {k: sum(1 for v in sc[k]["cases"].values() if v["verdict"] == "PASS") for k in sc}
        fails = sorted({g["gate"].split()[0] for g in sc["Arize AX"]["gates"] if g["gate_verdict"] == "FAIL"}, key=lambda g: int(g[1:]))
        cost = sum(r.get("est_cost_usd") or 0 for r in runs)
        mins = sum(r["seconds"] for r in runs) / 60
        totals.update({"cases": totals["cases"] + n, "Arize AX": totals["Arize AX"] + p["Arize AX"], "Braintrust": totals["Braintrust"] + p["Braintrust"],
                       "cost": totals["cost"] + cost, "minutes": totals["minutes"] + mins})
        rows.append(f"| {s} | {n} | {p['Arize AX']} | {p['Braintrust']} | {', '.join(fails) or '-'} | ${cost:.2f} |")
    out = HERE / "results" / f"experiment{args.experiment}_summary.md"
    out.write_text("\n".join([f"# Experiment {args.experiment} - agent model {models.agent_model_name()}, judge {models.JUDGE_MODEL}", "",
                              f"Cases graded: {totals['cases']}. Passed: Arize AX {totals['Arize AX']}, Braintrust {totals['Braintrust']}. "
                              f"Agent time {totals['minutes']:.0f} min, estimated agent cost ${totals['cost']:.2f}.", "",
                              "| Set | Cases | Arize AX pass | Braintrust pass | Gates that FAIL (Arize AX) | Agent cost |", "|---|---|---|---|---|---|"]
                             + rows) + "\n", encoding="utf-8")
    print(f"-> {out.relative_to(HERE)}")


if not args.summary:
    print(f"Experiment {args.experiment}: {len(sets)} set(s), model {'none (dry run)' if args.dry else models.agent_model_name()}")
    for s in sets:
        if not args.redo and not args.dry and (folder(s) / "summary.md").exists():
            print(f"  {s} already finished (results in {folder(s).relative_to(HERE)}) - skipped")
            continue
        run_set(s)
if not args.dry:
    summary()

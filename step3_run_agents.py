"""STEP 3 - Run the test cases (the original 73, or one case set when CASE_SET is set) through the loan agents ONCE
and save every answer and tool call.

Both platforms (step 4 Arize AX, step 5 Braintrust) then grade these same saved answers, so any difference in
results comes from the platform, not from the agent answering differently.
The model is chosen in .env with MODEL_PROVIDER: ollama (local test), anthropic (final run), dryrun (free wiring test).

Usage:  python step3_run_agents.py                 # all cases (cases already finished are skipped)
        python step3_run_agents.py --limit 3        # quick smoke test
        python step3_run_agents.py --ids AV-G1-001 AV-G4-002
        python step3_run_agents.py --fresh          # start again from zero
Output: results/<provider>/agent_runs.jsonl  (one line per case; a re-run case gets a newer line)
"""
import argparse
import json

from loan_agents import data, models, runner
from scoring import cases, runs

ap = argparse.ArgumentParser()
ap.add_argument("--ids", nargs="*")
ap.add_argument("--limit", type=int)
ap.add_argument("--fresh", action="store_true", help="delete earlier results and run everything again")
args = ap.parse_args()

out = runs.runs_file()
if args.fresh:
    out.unlink(missing_ok=True)
done = {i for i, r in runs.load().items() if not r["error"]}
todo = [c for c in cases.load() if (not args.ids or c["id"] in args.ids) and c["id"] not in done][: args.limit]
print(f"model: {models.PROVIDER} / {models.agent_model_name()}   cases to run: {len(todo)}   (already done: {len(done)})")

for n, case in enumerate(todo, 1):
    rec = runner.run_case(case)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    print(f"[{n}/{len(todo)}] {case['id']:10} {rec['seconds']:6.1f}s  tools={[c['tool'] for c in rec['tool_calls']]}"
          + (f"  ERROR {rec['error'][:150]}" if rec["error"] else ""), flush=True)
print(f"-> {out.relative_to(data.HERE)}")

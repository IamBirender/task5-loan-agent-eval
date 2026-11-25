"""STEP 5 - Grade the SAME saved answers in BRAINTRUST (run after step 4).

What it does in Braintrust (project "loan-agents"):
  1. Uploads the test cases (60 from the spreadsheet + our G9-G20 cases) as a Braintrust Dataset (re-running updates the same records, by case id).
  2. Runs a Braintrust Eval (an "experiment"): the task hands over the saved answer from step 3 and Braintrust
     runs the same 4 scorers as Arize (tool_check, facts_check, ai_judge, verdict).
  3. Optional --trace N: re-runs N cases live with Braintrust tracing on (OpenTelemetry), so the agent's
     step-by-step trace shows in the project's Logs.
Needs BRAINTRUST_API_KEY in .env.
Usage:  python step5_score_braintrust.py            # grade all saved answers
        python step5_score_braintrust.py --trace 3  # also send 3 live agent traces
Output: results/<provider>/braintrust_scores.json
"""
import argparse
import json
import os
import time

import braintrust
from braintrust import Score

from loan_agents import data, models, runner
from scoring import cases, runs

ap = argparse.ArgumentParser()
ap.add_argument("--trace", type=int, default=0, help="also re-run this many cases live with Braintrust tracing")
args = ap.parse_args()

assert os.getenv("BRAINTRUST_API_KEY"), "Add BRAINTRUST_API_KEY to .env (free account at braintrust.dev)."
PROJECT = "loan-agents"
ALL = {c["id"]: c for c in cases.load()}
DATASET = cases.dataset_name()   # e.g. loan-agent-test-cases-73, or loan-agent-test-cases-set07 for a case set
SAVED = runs.load()
assert SAVED, "No saved answers. Run step3_run_agents.py first."

# ---- 1. Dataset ----
dataset = braintrust.init_dataset(project=PROJECT, name=DATASET)
for c in ALL.values():
    dataset.insert(id=c["id"], input={"case_id": c["id"], "question": c["input"]}, expected=c["expected"],
                   metadata={"quality_gate": c["gate"], "agent": c["agent"], "method": c["method"],
                             "guidelines": c["guidelines"], "expected_tools": c["expected_tools"]})
dataset.flush()
print(f"Braintrust dataset {DATASET}: {len(ALL)} cases")

# ---- 2. Eval: the task returns the saved answer; the scorers grade it ----
GRADES: dict = {}


def grades(inp):
    cid = inp["case_id"]
    if cid not in GRADES:
        GRADES[cid] = runs.grade(ALL[cid], SAVED[cid])
    return GRADES[cid]


def task(inp, hooks=None):
    r = SAVED.get(inp["case_id"], {"answer": "", "tool_calls": [], "error": "not run in step 3"})
    if hooks is not None and r.get("tokens") is not None:   # per-case time, tokens and cost from the saved run
        try:
            hooks.span.log(metrics={"prompt_tokens": r["input_tokens"], "completion_tokens": r["output_tokens"],
                                    "tokens": r["tokens"], "agent_seconds": r["seconds"]},
                           metadata={"est_cost_usd": r.get("est_cost_usd"), "model": r.get("model")})
        except Exception:
            pass
    return {"answer": r["answer"], "tools_used": [c["tool"] for c in r["tool_calls"]], "error": r["error"],
            "seconds": r.get("seconds"), "tokens": r.get("tokens"), "est_cost_usd": r.get("est_cost_usd")}


def as_score(name, check):
    if check is None:  # this check does not apply to the case -> Braintrust skips it
        return None
    return Score(name=name, score=check["score"], metadata={k: v for k, v in check.items() if k != "score"})


def tool_check(input, output, expected, **_):
    return as_score("tool_check", grades(input)["tool_check"])


def facts_check(input, output, expected, **_):
    return as_score("facts_check", grades(input)["facts_check"])


def ai_judge(input, output, expected, **_):
    j = grades(input)["ai_judge"]
    return Score(name="ai_judge", score=j["score"], metadata={"reason": j["reason"]})


def policy_check(input, output, expected, **_):
    return as_score("policy_check", grades(input).get("policy_check"))


def verdict(input, output, expected, **_):
    v = grades(input)["verdict"]
    return None if v == "REVIEW" else Score(name="verdict", score=1.0 if v == "PASS" else 0.0, metadata={"verdict": v})


t0 = time.time()
result = braintrust.Eval(PROJECT, data=[r for r in dataset if r["input"]["case_id"] in SAVED], task=task,
                         scores=[tool_check, facts_check, policy_check, ai_judge, verdict], max_concurrency=1,
                         experiment_name=f"{models.AGENT_VERSION}{'-' + data.CASE_SET if data.CASE_SET else ''}-{models.PROVIDER}-{models.agent_model_name()}-{time.strftime('%Y%m%d-%H%M')}",
                         metadata={"agent_model": models.agent_model_name(), "judge_model": models.JUDGE_MODEL})
seconds = round(time.time() - t0, 1)

# ---- 3. Optional live traces ----
if args.trace:
    from braintrust.otel import BraintrustSpanProcessor
    from strands.telemetry import StrandsTelemetry
    StrandsTelemetry().tracer_provider.add_span_processor(BraintrustSpanProcessor(parent=f"project_name:{PROJECT}"))
    for c in [c for c in ALL.values() if c["id"] in SAVED and not SAVED[c["id"]]["error"]][: args.trace]:
        r = runner.run_case(c)
        print(f"traced {c['id']} -> Braintrust project '{PROJECT}' logs ({r['seconds']}s)")

table = runs.gate_table(GRADES, list(ALL.values()))
summary = getattr(result, "summary", None)
out = runs.runs_file().parent / "braintrust_scores.json"
out.write_text(json.dumps({"platform": "Braintrust", "model": models.agent_model_name(), "judge": models.JUDGE_MODEL,
                           "experiment_url": getattr(summary, "experiment_url", None), "grading_seconds": seconds,
                           "gates": table, "cases": GRADES}, indent=1, default=str), encoding="utf-8")
for r in table:
    print(f"{r['gate']:45} pass {r['pass']} fail {r['fail']} review {r['review']}  -> {r['gate_verdict']}")
print(f"-> {out.relative_to(data.HERE)}   (graded in {seconds}s)  {getattr(summary, 'experiment_url', '')}")

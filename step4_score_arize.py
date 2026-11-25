"""STEP 4 - Grade the saved answers in ARIZE AX (run this before step 5).

What it does in Arize:
  1. Uploads the test cases (60 from the spreadsheet + our G9-G20 cases) as an Arize Dataset (once; reused after).
  2. Runs an Arize Experiment: for each case it hands Arize the saved answer from step 3, and Arize runs our
     4 evaluators (tool_check, facts_check, ai_judge, verdict) and stores every score with its reason.
  3. Optional --trace N: re-runs N cases live with Arize tracing on, so the agent's step-by-step trace
     (supervisor -> specialist -> tool) shows in the Arize project "loan-agents".
Needs ARIZE_SPACE_ID and ARIZE_API_KEY in .env.
Usage:  python step4_score_arize.py            # grade all saved answers
        python step4_score_arize.py --trace 3  # also send 3 live agent traces
Output: results/<provider>/arize_scores.json
"""
import argparse
import json
import os
import time

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")  # Windows: avoids gRPC DNS errors when talking to arize.com
from arize import ArizeClient                                       # noqa: E402
from arize.experiments.evaluators.types import EvaluationResult     # noqa: E402

from loan_agents import data, models, runner                        # noqa: E402
from scoring import cases, runs                                     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--trace", type=int, default=0, help="also re-run this many cases live with Arize tracing")
args = ap.parse_args()

SPACE = os.environ["ARIZE_SPACE_ID"]
client = ArizeClient(api_key=os.environ["ARIZE_API_KEY"])
ALL = {c["id"]: c for c in cases.load()}
SAVED = runs.load()
assert SAVED, "No saved answers. Run step3_run_agents.py first."
DATASET = cases.dataset_name()   # e.g. loan-agent-test-cases-73, or loan-agent-test-cases-set07 for a case set

# ---- 1. Dataset (Arize reserves the field name 'id', so the case id goes in 'case_id') ----
if not any(d.name == DATASET for d in client.datasets.list(name=DATASET, space=SPACE).datasets):
    client.datasets.create(name=DATASET, space=SPACE, examples=[
        {"case_id": c["id"], "quality_gate": c["gate"], "agent": c["agent"], "method": c["method"], "input": c["input"],
         "expected": c["expected"], "guidelines": json.dumps(c["guidelines"]), "expected_tools": json.dumps(c["expected_tools"]), "source": c["source"]}
        for c in ALL.values()])
    print(f"created Arize dataset {DATASET} ({len(ALL)} cases)")

# ---- 2. Experiment: the task returns the saved answer; the evaluators grade it ----
GRADES: dict = {}


NOT_RUN = {"tool_check": None, "facts_check": None, "policy_check": None, "ai_judge": {"score": None, "reason": "not run in step 3"}, "verdict": "NOT RUN"}


def grades(row):
    cid = row["case_id"]
    if cid not in SAVED:   # Arize runs over the whole dataset; cases not answered yet are marked NOT RUN
        return NOT_RUN
    if cid not in GRADES:
        GRADES[cid] = runs.grade(ALL[cid], SAVED[cid])
    return GRADES[cid]


def task(dataset_row):
    r = SAVED.get(dataset_row["case_id"], {"answer": "", "tool_calls": [], "error": "not run in step 3"})
    return {"answer": r["answer"], "tools_used": [c["tool"] for c in r["tool_calls"]], "error": r["error"],
            "seconds": r.get("seconds"), "tokens": r.get("tokens"), "est_cost_usd": r.get("est_cost_usd")}


def result(check, name):
    if check is None:  # this check does not apply to the case
        return EvaluationResult(score=None, label="not_applicable", explanation=f"{name} does not apply to this case")
    return EvaluationResult(score=check["score"], label="pass" if check["score"] >= 0.8 else "fail",
                            explanation=json.dumps({k: v for k, v in check.items() if k != "score"})[:1000])


def tool_check(output, dataset_row):
    return result(grades(dataset_row)["tool_check"], "tool_check")


def facts_check(output, dataset_row):
    return result(grades(dataset_row)["facts_check"], "facts_check")


def ai_judge(output, dataset_row):
    j = grades(dataset_row)["ai_judge"]
    label = "not_run" if j["score"] is None else "pass" if j["score"] >= 0.8 else "fail"
    return EvaluationResult(score=j["score"], label=label, explanation=j["reason"])


def policy_check(output, dataset_row):
    return result(grades(dataset_row).get("policy_check"), "policy_check")


def verdict(output, dataset_row):
    v = grades(dataset_row)["verdict"]
    return EvaluationResult(score={"PASS": 1.0, "FAIL": 0.0}.get(v), label=v, explanation=f"case verdict {v}")


subset = [cid for cid in ALL if cid in SAVED]
t0 = time.time()
experiment, df = client.experiments.run(
    name=f"{models.AGENT_VERSION}{'-' + data.CASE_SET if data.CASE_SET else ''}-{models.PROVIDER}-{models.agent_model_name()}-{time.strftime('%Y%m%d-%H%M')}",
    dataset=DATASET, space=SPACE, task=task, evaluators=[tool_check, facts_check, policy_check, ai_judge, verdict], concurrency=1)
seconds = round(time.time() - t0, 1)
for cid in subset:  # make sure every saved case is graded even if Arize skipped one
    grades({"case_id": cid})

# ---- 3. Optional live traces ----
if args.trace:
    from arize.otel import register
    from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor
    register(space_id=SPACE, api_key=os.environ["ARIZE_API_KEY"], project_name="loan-agents",
             span_processors=[StrandsAgentsToOpenInferenceProcessor()])
    for c in [c for c in ALL.values() if c["id"] in SAVED and not SAVED[c["id"]]["error"]][: args.trace]:
        r = runner.run_case(c)
        print(f"traced {c['id']} -> Arize project 'loan-agents' ({r['seconds']}s)")

table = runs.gate_table(GRADES, list(ALL.values()))
out = runs.runs_file().parent / "arize_scores.json"
out.write_text(json.dumps({"platform": "Arize AX", "model": models.agent_model_name(), "judge": models.JUDGE_MODEL,
                           "experiment": str(getattr(experiment, "id", experiment)), "grading_seconds": seconds,
                           "gates": table, "cases": GRADES}, indent=1, default=str), encoding="utf-8")
for r in table:
    print(f"{r['gate']:45} pass {r['pass']} fail {r['fail']} review {r['review']}  -> {r['gate_verdict']}")
print(f"-> {out.relative_to(data.HERE)}   (graded in {seconds}s; open the experiment in Arize AX to see every score and reason)")

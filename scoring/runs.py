"""Saved agent runs (from step 3) and the grading of one run. Steps 4 and 5 both use grade()."""
import json

from loan_agents import data, models

from . import checks


def runs_file():
    folder = data.HERE / "results" / f"{models.PROVIDER}-{models.AGENT_VERSION}"   # e.g. results/bedrock-v3
    if data.CASE_SET:   # each case set gets its own folder, e.g. results/bedrock-v3-set07
        folder = folder.with_name(f"{folder.name}-{data.CASE_SET}")
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "agent_runs.jsonl"


def load() -> dict:
    """Case id -> its latest saved run."""
    f = runs_file()
    out = {}
    if f.exists():
        for line in f.open(encoding="utf-8"):
            r = json.loads(line)
            out[r["id"]] = r
    return out


def grade(case: dict, run: dict) -> dict:
    """All scores for one case: code checks, AI judge and the final PASS / FAIL / REVIEW."""
    answer, calls = run["answer"], run["tool_calls"]
    tool = checks.tool_check(case, calls)
    facts = checks.facts_check(case, answer)
    policy = checks.policy_check(case, run)
    if models.PROVIDER == "dryrun" or run["error"]:
        judged = {"score": 0.0, "reason": "dry run - judge not called" if models.PROVIDER == "dryrun" else f"agent error: {run['error'][:200]}"}
    else:
        judged = checks.judge(case, answer, calls)
    verdict = "FAIL" if run["error"] else checks.case_verdict(case, tool, facts, judged, policy)
    return {"tool_check": tool, "facts_check": facts, "policy_check": policy, "ai_judge": judged, "verdict": verdict,
            "seconds": run["seconds"], "tokens": run.get("tokens"), "est_cost_usd": run.get("est_cost_usd")}


def gate_table(graded: dict, all_cases: list[dict]) -> list[dict]:
    """One row per quality gate: case results and the gate verdict."""
    rows = []
    for g in dict.fromkeys(c["gate"] for c in all_cases):
        cs = [c for c in all_cases if c["gate"] == g]
        v = [graded[c["id"]]["verdict"] for c in cs if c["id"] in graded]
        rows.append({"gate": g, "cases": len(cs), "graded": len(v), "pass": v.count("PASS"), "fail": v.count("FAIL"),
                     "review": v.count("REVIEW"), "gate_verdict": checks.gate_verdict(cs[0]["gate_code"], v) if v else "NOT RUN"})
    # G20 readiness gate is derived: ready only if no earlier gate fails and the safety gates (G4, G12, G13) pass.
    before = [r for r in rows if int(r["gate"].split()[0][1:]) < 20 and r["gate_verdict"] != "NOT RUN"]
    if any(int(r["gate"].split()[0][1:]) > 8 for r in before):
        safety = [r for r in before if r["gate"].split()[0] in ("G4", "G12", "G13")]
        if any(r["gate_verdict"] == "FAIL" for r in before):
            verdict = "FAIL"
        elif len(safety) < 3 or any(r["gate_verdict"] != "PASS" for r in safety):
            verdict = "REVIEW"   # a safety gate was not run or not clean: not ready yet
        else:
            verdict = "REVIEW" if any(r["gate_verdict"] == "REVIEW" for r in before) else "PASS"
        at = next((i for i, r in enumerate(rows) if int(r["gate"].split()[0][1:]) > 20), len(rows))
        rows.insert(at, {"gate": "G20 · Readiness gate (derived from G1-G19)", "cases": 0, "graded": 0, "pass": 0, "fail": 0,
                         "review": 0, "gate_verdict": verdict})
    return rows

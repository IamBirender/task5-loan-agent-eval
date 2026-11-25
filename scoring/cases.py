"""Read the test cases: the senior's 60 cases (spreadsheet, column C holds each case as JSON) plus our own
G9-G20 cases (extra_test_cases_G9_G20.json). Set ONLY_SENIOR_CASES=1 to use just the 60.
With CASE_SET=set07 in .env, only that set's 73 cases are used (case_sets/set07/test_cases.json, made by case_sets/make_cases.py)."""
import json
import os
from pathlib import Path

import openpyxl

from loan_agents import data

HERE = Path(__file__).resolve().parent.parent
XLSX = HERE / "agentic_evaluation_test_cases.xlsx"
EXTRA = HERE / "extra_test_cases_G9_G20.json"


def _case(j: dict, row, title: str, source: str) -> dict:
    e, m, inp = j["expectations"], j["metadata"], j["inputs"]
    turns = inp.get("Turns") or [inp["UserInput"]]
    return {
        "id": j["name"], "row": row, "source": source,
        "gate": m["qualityGate"], "gate_code": m["qualityGate"].split()[0],
        "phase": m.get("phase", ""), "method": m["evaluationMethod"],
        "agent": j["evaluatedAgent"], "title": title,
        "turns": turns, "input": "\n".join(f"Turn {i + 1}: {t}" for i, t in enumerate(turns)) if len(turns) > 1 else turns[0],
        "session_id": inp.get("SessionId", ""),
        "expected": e["expectedResponse"]["Response"], "guidelines": e.get("guidelines", []),
        "expected_tools": [t if isinstance(t, dict) else {"name": t, "arguments": {}} for t in e.get("expectedTools", [])],
        "forbidden": e.get("forbiddenValues", []), "forbidden_patterns": e.get("forbiddenPatterns", []), "fault": m.get("fault"), "limits": m.get("limits", {}),
    }


def dataset_name() -> str:
    """Name of the dataset in Arize AX and Braintrust. Each case set gets its own dataset."""
    n = len(load())
    if data.CASE_SET:
        return f"loan-agent-test-cases-{data.CASE_SET}"
    return "loan-agent-test-cases-v1" if n == 60 else f"loan-agent-test-cases-{n}"   # 73 = with our G9-G20 cases


def load() -> list[dict]:
    if data.CASE_SET:   # one of the 50 generated case sets
        f = data.SET_DIR / "test_cases.json"
        assert f.exists(), f"{f} not found: run case_sets/make_cases.py first, or check CASE_SET in .env"
        cases = [_case(j, None, j["description"], f"case set {data.CASE_SET}") for j in json.loads(f.read_text(encoding="utf-8"))["testCases"]]
        return sorted(cases, key=lambda c: (int(c["gate_code"][1:]), c["id"]))
    ws = openpyxl.load_workbook(XLSX, data_only=True)["Evaluation Test Cases"]
    cases = []
    for row_no, (gate, title, js, *_rest) in enumerate(ws.iter_rows(min_row=4, max_col=6, values_only=True), start=4):
        if js and str(js).lstrip().startswith("{"):
            cases.append(_case(json.loads(js), row_no, str(title).split("\n")[0], "senior's spreadsheet"))
    if EXTRA.exists() and os.getenv("ONLY_SENIOR_CASES") != "1":
        for j in json.loads(EXTRA.read_text(encoding="utf-8"))["testCases"]:
            cases.append(_case(j, None, j["description"], "added by us"))
    gate_no = lambda c: int(c["gate_code"][1:])
    return sorted(cases, key=lambda c: (gate_no(c), c["id"]))


if __name__ == "__main__":
    cs = load()
    print(len(cs), "cases;", sorted({c["gate_code"] for c in cs}, key=lambda g: int(g[1:])))

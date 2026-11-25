"""STEP 2 - Check the answer key BEFORE testing the agents (no AI model is used here).

For every exact figure in each expected response, look for it in the real data (all tool outputs, computed straight
from the 8 loans) or in the case's own question. A figure found nowhere means the answer key itself may be wrong,
so a failure on that case is not the agent's fault.
Usage:  python step2_check_answer_key.py
"""
import json
import re

from loan_agents import data, tools
from scoring import cases, checks, runs

ids = [r[0] for r in data.connect().execute("SELECT loan_id FROM loan_static").fetchall()]
truth = [tools.credit_performance(), tools.memory_read(), tools.data_validation(),
         tools.rows("SELECT * FROM default_risk_screen"), tools.rows("SELECT * FROM loan_static"),
         {"configured_screen_thresholds": {"ltv_min": 80, "dti_min": 43, "min_score_below": 700}}]
truth += [tools.loan_performance(i) for i in ids] + [tools.cohort_comparison(i) for i in ids]
truth_text = json.dumps(truth, default=str)
# Raw monthly values too (e.g. a single month's balance), and the loan_features table
truth_text += json.dumps(data.connect().execute("SELECT * FROM loan_monthly").fetchall(), default=str)
known = {checks._norm(f) for f in checks.FACT.findall(truth_text)}

lines = ["# Answer key check (step 2)", "",
         "Every exact figure in the expected responses was looked up in the real data (computed from the 8 loans) "
         "and in the test case's own question. Figures found in neither place are listed below.", "",
         "| Case | Figures not found in the data or the question |", "|---|---|"]
# Figures that are not stored in the data but follow from it with simple arithmetic, or come from the documents.
DERIVED = {"218750": "Original Home Value = $175,000 / 80% LTV (a calculation)",
           "22.4": "share paid down = 1 - 114,920.58 / 148,000 (a calculation)",
           "9.7": "REO loan's $165,000 / $1,697,000 pool (a calculation)",
           "12.5": "one more loan of 8 (4/8 -> 5/8) (a calculation)"}
DOC_CASES = {"AV-G7-006": "dates quoted from the Fannie Mae FAQ document, not from the loan data"}
# Case sets (CASE_SET=setNN): implied purchase price = original amount / (LTV / 100) of a loan, for AV-G7-003
for upb, ltv in data.connect().execute("SELECT orig_upb, ltv FROM loan_static").fetchall():
    DERIVED.setdefault(checks._norm(f"{round(upb / (ltv / 100), 2):.2f}"), "implied purchase price = original amount / (LTV / 100) (a calculation)")
problems = 0
for c in cases.load():
    facts = checks.all_figures(c)   # every figure in the key, including ones in brackets
    own = {checks._norm(f) for f in checks.FACT.findall(c["input"])} | set(checks.VERDICT.findall(c["input"]))
    missing = [f for f in facts if f not in known and f not in own and not checks.VERDICT.fullmatch(f)
               # the scorer reads an amount like $102,000 as the date 10/2000; fine if the amount is in the data
               and not (re.fullmatch(r"\d\d/\d{4}", f) and f.replace("/", "") in known)]
    if re.sub(r"-SET\d+$", "", c["id"]) in DOC_CASES:
        lines.append(f"| {c['id']} | ok - {DOC_CASES[re.sub(r'-SET\d+$', '', c['id'])]} |")
        continue
    explained = [f"{f} ok - {DERIVED[f]}" for f in missing if f in DERIVED]
    missing = [f for f in missing if f not in DERIVED]
    if missing:
        problems += 1
    if missing or explained:
        cell = "; ".join(([f"**NOT FOUND: {', '.join(missing)}**"] if missing else []) + explained)
        lines.append(f"| {c['id']} | {cell} |")
lines += ["", f"**{problems} of {len(cases.load())} cases** have figures that could not be reproduced from the data. "
          "A failure on those cases may be the answer key's fault, not the agent's."]
out = (runs.runs_file().parent if data.CASE_SET else data.HERE / "results") / "answer_key_check.md"   # a case set: its own results folder
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[4:]))
print(f"-> {out.relative_to(data.HERE)}")

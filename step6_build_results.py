"""STEP 6 - Put the results together (no AI model, no platform calls).

  results/<provider>/summary.md                       gate results for Arize AX and Braintrust side by side
  results/<provider>/test_cases_with_results.xlsx     the senior's spreadsheet with "Actual response" and "Score" filled in
Usage:  python step6_build_results.py
"""
import json

import openpyxl
from openpyxl.styles import Alignment

from loan_agents import data, models
from scoring import cases, runs

folder = runs.runs_file().parent
saved = runs.load()
platforms = {}
for name, file in [("Arize AX", "arize_scores.json"), ("Braintrust", "braintrust_scores.json")]:
    if (folder / file).exists():
        platforms[name] = json.loads((folder / file).read_text(encoding="utf-8"))
assert platforms, "No scores yet. Run step 4 (Arize) and/or step 5 (Braintrust) first."
all_cases = cases.load()

# ---- summary.md ----
names = list(platforms)
L = [f"# Results - agent model `{models.agent_model_name()}`, judge `{models.JUDGE_MODEL}`", "",
     f"Cases answered: {sum(1 for c in all_cases if c['id'] in saved)} of {len(all_cases)} "
     + (f"(case set {data.CASE_SET}, its own 8-loan pool). " if data.CASE_SET else
        f"({sum(1 for c in all_cases if c['source'] != 'added by us')} from the senior's spreadsheet, "
        f"{sum(1 for c in all_cases if c['source'] == 'added by us')} added by us for G9-G19). ") +
     f"Agent errors: {sum(1 for r in saved.values() if r['error'])}.", "",
     "## Quality gates", "", "| Gate | " + " | ".join(f"{n} (pass/fail/review) | {n} gate" for n in names) + " |",
     "|---|" + "---|---|" * len(names)]
for i, g in enumerate(platforms[names[0]]["gates"]):
    cells = []
    for n in names:
        r = platforms[n]["gates"][i]
        cells += [f"{r['pass']}/{r['fail']}/{r['review']}", f"**{r['gate_verdict']}**"]
    L.append(f"| {g['gate']} | " + " | ".join(cells) + " |")
totals = {n: sum(1 for v in platforms[n]["cases"].values() if v["verdict"] == "PASS") for n in names}
L += ["", "Cases passed: " + ", ".join(f"{n} {totals[n]}/{len(all_cases)}" for n in names)]
runs_ok = [r for r in saved.values() if r.get("tokens") is not None]
if runs_ok:
    secs = sorted(r["seconds"] for r in runs_ok)
    costs = [r["est_cost_usd"] for r in runs_ok if r.get("est_cost_usd") is not None]
    L += ["", "## Time, tokens and cost (agent run)", "",
          f"- Time per case: median {secs[len(secs) // 2]} s, slowest {secs[-1]} s, total {round(sum(secs) / 60, 1)} min",
          f"- Tokens: {sum(r['tokens'] for r in runs_ok):,} in total, {round(sum(r['tokens'] for r in runs_ok) / len(runs_ok)):,} per case",
          f"- Estimated cost at list price: ${round(sum(costs), 2)} in total, ${round(sum(costs) / max(len(costs), 1), 3)} per case" if costs else "- Cost: no price known for this model"]
if len(names) == 2:
    a, b = (platforms[n]["cases"] for n in names)
    diff = [cid for cid in a if cid in b and a[cid]["verdict"] != b[cid]["verdict"]]
    L += ["", f"## Do the two platforms agree?", "",
          f"Same saved answers, same scorers: {len(a) - len(diff)} of {len(a)} verdicts match. "
          "The code checks are identical by design; any difference comes from the AI judge giving a different score on a re-run.",
          ""] + [f"- {cid}: {names[0]} {a[cid]['verdict']} (judge {a[cid]['ai_judge']['score']}) vs "
                 f"{names[1]} {b[cid]['verdict']} (judge {b[cid]['ai_judge']['score']})" for cid in diff]
L += ["", "## Every case", "", "| Case | Agent | Method | " + " | ".join(names) + " | Judge reason (" + names[0] + ") | Tools used | Seconds | Tokens | Est. cost $ |",
      "|---|---|---|" + "---|" * len(names) + "---|---|---|"]
for c in all_cases:
    g = platforms[names[0]]["cases"].get(c["id"])
    r = saved.get(c["id"], {})
    if not g:
        continue
    tools_used = sorted({t["tool"] for t in r.get("tool_calls", [])})
    L.append(f"| {c['id']} | {c['agent'].replace(' Agent', '')} | {c['method']} | "
             + " | ".join(platforms[n]["cases"][c["id"]]["verdict"] for n in names)
             + f" | {g['ai_judge']['reason'][:160].replace('|', '/')} | {', '.join(tools_used) or '-'} | {r.get('seconds', '')} | {r.get('tokens', '')} | {r.get('est_cost_usd', '')} |")
(folder / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")

# ---- filled spreadsheet ----
wb = openpyxl.load_workbook(cases.XLSX)
ws = wb["Evaluation Test Cases"]
extra = wb.create_sheet(f"Case set {data.CASE_SET}" if data.CASE_SET else "Added G9-G19 cases") if any(c["row"] is None for c in all_cases) else None
if extra:
    extra.append(["Quality gate", "Test case", "Input", "Expected response", "Actual response", "Score"])
for c in all_cases:
    r = saved.get(c["id"])
    if c["row"] is None and extra is not None and r:
        g = "; ".join(f"{n}: {platforms[n]['cases'][c['id']]['verdict']}" for n in names if c["id"] in platforms[n]["cases"])
        extra.append([c["gate"], c["id"], c["input"], c["expected"], (r["answer"] or f"ERROR: {r['error']}")[:32000], g])
        continue
    if not r:
        continue
    ws.cell(c["row"], 5, (r["answer"] or f"ERROR: {r['error']}")[:32000]).alignment = Alignment(wrap_text=True, vertical="top")
    parts = []
    for n in names:
        g = platforms[n]["cases"].get(c["id"])
        if g:
            sub = ([f"RULE FAILED: {'; '.join(g['policy_check']['problems'])}"] if g.get("policy_check") and g["policy_check"]["problems"] else [])
            sub += [f"judge {g['ai_judge']['score']:.2f}"] + [f"{k.split('_')[0]} {g[k]['score']:.2f}" for k in ("facts_check", "tool_check") if g[k]]
            parts.append(f"{n}: {g['verdict']} ({', '.join(sub)})")
    ws.cell(c["row"], 6, "\n".join(parts)).alignment = Alignment(wrap_text=True, vertical="top")
xlsx = folder / "test_cases_with_results.xlsx"
wb.save(xlsx)
print("\n".join(L[:20]))
print(f"-> {(folder / 'summary.md').relative_to(data.HERE)}\n-> {xlsx.relative_to(data.HERE)}")

"""CASE SETS - part 3: check all 50 case sets AGAINST THE RAW 2007Q4 FILE, with code written separately from make_cases.py.

Why: make_cases.py takes its figures from our database and tool code (loan_agents/). If that code had a bug, the expected
answers would carry the same bug and the agents would be marked wrong for giving the right answer. So this script:
  1. reads the 400 loans' rows straight from data/2007Q4.zip (all fields, by their position in Fannie Mae's file layout),
  2. works out every fact again in plain Python (no database, no loan_agents tools),
  3. checks every test case three ways:
       A. every figure in the question and the expected answer is a real value for that set's loans,
       B. for each data-based test, the key facts (right loan, right number, right order) are in the expected answer,
       C. sanity: only the pool's own loans appear, exactly one REO loss loan and one repurchased loan, no ties in rankings,
  4. checks the questions for repetition (inside each set and across the 50 sets).
Output: case_sets/verification_report.md
Usage : python case_sets/verify_cases.py data/2007Q4.zip
"""
import collections
import io
import json
import pickle
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from scoring.checks import FACT, VERDICT, _norm  # noqa: E402  (text-matching rules only; no facts come from here)

# Field positions (1-based) from the "CRT Glossary and File Layout" PDF, written out here on purpose (not data.COLS)
POS = {"loan": 2, "period": 3, "channel": 4, "orig_rate": 8, "rate": 9, "orig_upb": 10, "upb": 12, "term": 13, "orig_date": 14,
       "ltv": 20, "cltv": 21, "borrowers": 22, "dti": 23, "score": 24, "co_score": 25, "purpose": 27, "ptype": 28, "units": 29,
       "state": 31, "msa": 32, "zip": 33, "dq": 40, "history": 41, "mod": 42, "zb": 44, "zb_date": 45, "upb_removal": 46,
       "fc_date": 52, "disp_date": 53, "cost1": 54, "cost2": 55, "cost3": 56, "cost4": 57, "cost5": 58, "nsp": 59}
CACHE = HERE / "_verify_rows.pkl"   # the 400 loans' raw rows (Fannie Mae data: git-ignored)


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ym(p):          # MMYYYY -> YYYY-MM (sortable)
    return f"{p[2:]}-{p[:2]}"


def mmy(p):         # YYYY-MM -> MM/YYYY
    return f"{p[5:]}/{p[:4]}" if p else None


def money(x):
    return f"${x:,.0f}" if abs(x - round(x)) < 0.005 else f"${x:,.2f}"


# ---------------------------------------------------------------- 1. raw rows
def load_rows(zip_path, wanted):
    if CACHE.exists():
        rows = pickle.loads(CACHE.read_bytes())
        if wanted <= set(rows):
            return rows
    rows = collections.defaultdict(list)
    with zipfile.ZipFile(zip_path) as z, z.open(next(n for n in z.namelist() if n.endswith(".csv"))) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
            parts = line.rstrip("\r\n").split("|")
            if len(parts) > 2 and parts[POS["loan"] - 1] in wanted:
                rows[parts[POS["loan"] - 1]].append(parts)
    CACHE.write_bytes(pickle.dumps(dict(rows)))
    return dict(rows)


# ---------------------------------------------------------------- 2. facts, worked out again
def loan_facts(raw):
    g = lambda r, k: r[POS[k] - 1].strip()
    raw = sorted(raw, key=lambda r: ym(g(r, "period")))
    first = raw[0]
    vals = lambda k: [g(r, k) for r in raw if g(r, k)]
    nums = lambda k: [fnum(g(r, k)) for r in raw if fnum(g(r, k)) is not None]
    score = max(map(int, vals("score"))) if vals("score") else None
    co = max(map(int, vals("co_score"))) if vals("co_score") else None
    months = [(ym(g(r, "period")), g(r, "dq"), fnum(g(r, "upb")), fnum(g(r, "rate")), g(r, "mod"), g(r, "history")) for r in raw]
    dqs = [(p, int(d)) for p, d, *_ in months if d.isdigit()]
    peak = max((d for _, d in dqs), default=0)
    zb = (vals("zb") or [""])[-1]
    f = {"id": g(first, "loan"), "channel": g(first, "channel"), "orig_rate": fnum(g(first, "orig_rate")), "orig_upb": fnum(g(first, "orig_upb")),
         "term": int(g(first, "term")), "orig_date": g(first, "orig_date"), "ltv": int(g(first, "ltv")), "cltv": int(g(first, "cltv")),
         "borrowers": int(g(first, "borrowers")), "dti": int(g(first, "dti")), "score": score, "co_score": co,
         "min_score": min(score, co) if co is not None else score, "purpose": g(first, "purpose"), "ptype": g(first, "ptype"),
         "units": int(g(first, "units")), "state": g(first, "state"),
         "msas": {g(r, "msa") for r in raw} - {"", "00000"}, "zips": {g(r, "zip") for r in raw} - {""},
         "records": len(raw), "first_period": months[0][0], "last_period": months[-1][0], "last_dq": months[-1][1],
         "last_upb": months[-1][2] or 0.0, "peak": peak,
         "peak_first": next((p for p, d in dqs if d == peak), None) if peak else None,
         "dq_months": sum(1 for _, d in dqs if d >= 1),
         "first90": next((p for p, d in dqs if d >= 3), None), "first180": next((p for p, d in dqs if d >= 6), None),
         "first_mod": next((p for p, _, _, _, m, _ in months if m == "Y"), None),
         "zb": zb, "zb_date": (vals("zb_date") or [""])[-1], "upb_removal": max(nums("upb_removal"), default=None),
         "costs": sum(sum(nums(k)) for k in ("cost1", "cost2", "cost3", "cost4", "cost5")),
         "nsp": max(nums("nsp"), default=None), "fc_date": (vals("fc_date") or [None])[-1], "disp_date": (vals("disp_date") or [None])[-1],
         "max_upb": max((u for _, _, u, *_ in months if u), default=0.0),
         "history": [p for p, *_, h in months if h], "months": months}
    f["outcome"] = {"01": "prepaid", "06": "repurchased", "09": "REO", "": "active"}.get(zb, f"other ({zb})")
    f["loss"] = round(f["upb_removal"] + f["costs"] - f["nsp"], 2) if f["nsp"] is not None else None
    f["severity"] = round(f["loss"] / f["upb_removal"] * 100, 1) if f["loss"] is not None else None
    rc = next(((p, r) for p, _, _, r, _, _ in months if r and abs(r - f["orig_rate"]) > 1e-9), None)
    f["rate_change"] = rc
    f["flags"] = {"LTV": f["ltv"] >= 80, "DTI": f["dti"] >= 43, "credit score": f["min_score"] < 700, "subordinate financing": f["cltv"] > f["ltv"]}
    f["nflags"] = sum(f["flags"].values())
    return f


def pool_facts(L):
    ids = sorted(L)
    P = {"ids": ids, "L": L, "records": sum(L[i]["records"] for i in ids), "last": max(L[i]["last_period"] for i in ids)}
    P["flagged"] = [i for i in sorted(ids, key=lambda i: (-L[i]["nflags"], -L[i]["cltv"])) if L[i]["nflags"]]
    P["tie_in_screen"] = any((L[a]["nflags"], L[a]["cltv"]) == (L[b]["nflags"], L[b]["cltv"]) for a, b in zip(P["flagged"], P["flagged"][1:]))
    P["unflagged"] = [i for i in ids if i not in P["flagged"]]
    P["ever90"] = [i for i in ids if L[i]["first90"]]
    P["ever180"] = [i for i in ids if L[i]["first180"]]
    P["active"] = [i for i in ids if L[i]["outcome"] == "active"]
    P["orig_total"] = sum(L[i]["orig_upb"] for i in ids)
    P["outstanding"] = round(sum(L[i]["last_upb"] for i in P["active"]), 2)
    P["reo"] = [i for i in ids if L[i]["loss"] is not None and L[i]["loss"] > 0]
    P["rep"] = [i for i in ids if L[i]["outcome"] == "repurchased"]
    P["mods"] = [i for i in ids if L[i]["first_mod"]]
    P["events"] = [i for i in ids if L[i]["first90"] or L[i]["first_mod"] or L[i]["loss"] is not None]
    P["history"] = sorted(p for i in ids for p in L[i]["history"])
    # peers: each feature scaled 0-1 across the 8 loans, distance = mean absolute difference (same definition, new code)
    feats = ["score", "ltv", "orig_rate", "term", "units"]
    rng = {k: (min(L[i][k] for i in ids), max(L[i][k] for i in ids)) for k in feats}
    sc = lambda i, k: (L[i][k] - rng[k][0]) / ((rng[k][1] - rng[k][0]) or 1)
    P["peers"] = {i: sorted(((round(sum(abs(sc(j, k) - sc(i, k)) for k in feats) / len(feats), 3), j) for j in ids if j != i)) for i in ids}
    return P


def truth_set(P):
    """Every figure the raw data gives for this pool, in the scorer's normal form, plus calculations from it."""
    L, out = P["L"], set()
    add = lambda *xs: out.update(_norm(str(x)) for x in xs if x is not None)
    for i in P["ids"]:
        f = L[i]
        add(i, f["orig_rate"], f["orig_upb"], f["ltv"], f["cltv"], f["dti"], f["score"], f["co_score"], f["min_score"], f["records"],
            f["peak"], f["dq_months"], f["loss"], f["severity"], f["upb_removal"], round(f["costs"], 2), f["nsp"], f["max_upb"], f["last_upb"],
            f["term"], f["units"], f["borrowers"])
        add(*(mmy(p) for p in [f["first_period"], f["last_period"], f["peak_first"], f["first90"], f["first180"], f["first_mod"]]))
        add(*(f"{d[:2]}/{d[2:]}" for d in [f["zb_date"], f["fc_date"], f["disp_date"], f["orig_date"]] if d))
        add(*(u for _, _, u, *_ in f["months"] if u), *(r for *_, r, _, _ in f["months"] if r))
        if f["first_mod"]:
            add(f"{f['first_mod'][5:]}{f['first_mod'][:4]}")                       # source value MMYYYY
        if f["rate_change"]:
            add(mmy(f["rate_change"][0]))
        add(round(f["max_upb"] / f["orig_upb"] * 100, 1), round((1 - f["last_upb"] / f["orig_upb"]) * 100, 1),
            f"{round(f['orig_upb'] / (f['ltv'] / 100), 2):.2f}")                     # % of original, % paid down, implied price
        add(round(f["orig_upb"] / P["orig_total"] * 100, 1))
        add(*(u for p, _, u, *_ in f["months"] if u and u > f["orig_upb"]), *(round(u / f["orig_upb"] * 100, 1) for _, _, u, *_ in f["months"] if u))
        add(*(d for d, _ in P["peers"][i][:3]))
        add(f["peak"] + 5)                                                           # the wrong figure in the false-claim tests
        if f["loss"]:
            add(round(f["loss"] + 450, 2), round(f["severity"] + 0.3, 1))             # the wrong candidate in the shadow test
    add(P["records"], mmy(P["last"]), P["orig_total"], P["outstanding"], len(P["history"]),
        round(sum(L[i]["loss"] for i in P["reo"]) / P["orig_total"] * 100, 2))
    if P["history"]:
        add(mmy(P["history"][0]), mmy(P["history"][-1]))
    return out


# figures that are rules or quotes, the same for every set (thresholds, layout, the documents, fixed scenario numbers)
CONSTANT = {_norm(x) for x in ["80", "43", "700", "36", "108", "110", "61", "900000", "$900,000", "95", "19", "20", "100", "12.5",
                               "01/2000", "30/2015", "01/2009", "30/2016", "2021", "2023", "2025", "13",
                               # zero balance codes, the test loan number, "90+ / 180+ days", "24-month", and document quotes
                               "01", "06", "09", "04", "30", "999999999999", "90", "180", "24", "2020", "97",
                               "2024", "2026", "104", "106", "109", "112"]}   # years and column counts used in the questions


# ---------------------------------------------------------------- 3B. key facts per test (right loan, right figure, right order)
def in_screen_order(text, ids, L):
    """All `ids` appear, and in the text they follow the screen rule (flag count, then CLTV, both descending); ties may swap."""
    if not all(i in text for i in ids):
        return False
    keys = [(L[i]["nflags"], L[i]["cltv"]) for i in sorted(ids, key=text.find)]
    return keys == sorted(keys, reverse=True)


def in_order(text, items):
    pos = -1
    for x in items:
        pos = text.find(x, pos + 1)
        if pos < 0:
            return False
    return True


def key_facts(base, q, e, P):
    """List of (what, ok) for one case. q = question text, e = expected answer text."""
    L, out = P["L"], []
    chk = lambda what, ok: out.append((what, bool(ok)))
    qids = [i for i in re.findall(r"\b\d{12}\b", q) if i != "999999999999"]
    reo, rep = P["reo"][0], P["rep"][0]
    loss = L[reo]
    if base in ("AV-G1-003", "AV-G17-X01", "AV-G22-006", "AV-G5-001", "AV-G9-X01", "AV-G3-001"):
        chk("flagged loans, in screen order", in_screen_order(e, P["flagged"], L) if base != "AV-G3-001"
            else any(i in e.split(" first with")[0][-20:] for i in P["flagged"] if (L[i]["nflags"], L[i]["cltv"]) == (L[P["flagged"][0]]["nflags"], L[P["flagged"][0]]["cltv"])))
        if base == "AV-G1-003" and P["tie_in_screen"]:
            chk("tie is explained", "either order is correct" in e)
        if base == "AV-G1-003":
            for i in P["flagged"]:
                rules = [k for k, v in L[i]["flags"].items() if v]
                m = re.search(rf"{i} \((\w+) rules?: ([^)]*)\)", e)
                chk(f"rules for {i}", m and m.group(2).split(", ") == rules)
    if base in ("AV-G1-002", "AV-G3-002"):
        f = L[qids[0]]
        chk("loan has one borrower and no co-borrower score", f["co_score"] is None and f["borrowers"] == 1)
        chk("borrower score", str(f["score"]) in e)
    if base == "AV-G1-001":
        chk("record count", f"{P['records']}-record" in e)
    if base == "AV-G1-006":
        dates = sorted(L[i]["orig_date"][2:] + L[i]["orig_date"][:2] for i in P["ids"])
        chk("origination range", f"{dates[0][4:]}/{dates[0][:4]} to {dates[-1][4:]}/{dates[-1][:4]}" in e)
        chk("last period", f"through {mmy(P['last'])}" in e)
        chk("ever 90+ count", f"({len(P['ever90'])} of 8 loans" in e)
    if base in ("AV-G2-001", "AV-G4-005"):
        ltv80 = [i for i in sorted(P["ids"], key=lambda i: (-L[i]["nflags"], -L[i]["cltv"])) if L[i]["ltv"] >= 80]
        chk("LTV >= 80 loans in order", (in_screen_order(e, ltv80, L) if base == "AV-G2-001" else all(i in e for i in ltv80)) and len(ltv80) == len(set(re.findall(r"\b\d{12}\b", e))))
    if base == "AV-G2-002":
        f = L[qids[0]]
        chk("peak and when", f"peak of {f['peak']} months delinquent (reported {mmy(f['peak_first'])})" in e)
        chk("delinquent months", f"{f['dq_months']} months with a delinquency status above zero" in e)
        chk("ending code and date", f"code {f['zb']}) effective {f['zb_date'][:2]}/{f['zb_date'][2:]}" in e)
    if base in ("AV-G2-003", "AV-G21-002"):
        for x in (loss["upb_removal"], loss["costs"], loss["nsp"], loss["loss"]):
            chk(f"loss figure {money(x)}", money(round(x, 2)) in e)
        chk("severity", f"{loss['severity']}%" in e)
        chk("question names the REO loan", base != "AV-G2-003" or qids == [reo])
    if base in ("AV-G6-004", "AV-G9-X01", "AV-G11-X01", "AV-G19-X01"):
        chk("REO loss", money(loss["loss"]) in e and reo in (e + q if base != "AV-G11-X01" else e))
    if base == "AV-G6-004":
        chk("pool loss rate", f"{round(loss['loss'] / P['orig_total'] * 100, 2)}%" in e)
        chk("REO share of pool", f"{round(loss['orig_upb'] / P['orig_total'] * 100, 1)}%" in e)
    if base in ("AV-G2-004", "AV-G7-002"):
        for i in qids:
            chk(f"minimum score of {i}", f"{L[i]['min_score']} for loan {i}" in e)
    if base in ("AV-G2-005", "AV-G21-003"):
        peers = P["peers"][reo][:3]
        chk("peer ranking", in_order(e, [j for _, j in peers]))
        chk("peer distances", all(str(d) in e for d, _ in peers))
        chk("no tie at rank 3", P["peers"][reo][2][0] != P["peers"][reo][3][0])
    if base == "AV-G5-005":
        peer = P["peers"][reo][0][1]
        chk("REO loan and closest peer", reo in e and f"closest peer {peer}" in e)
    if base in ("AV-G2-006", "AV-G8-002"):
        f = L[rep]
        chk("right loan", qids == [rep])
        chk("false figure in question", f"{f['peak'] + 5} months" in q)
        chk("true peak and when", f"{f['peak']} months delinquent (reported {mmy(f['peak_first'])})" in e)
    if base == "AV-G3-003":
        f = L[qids[0]]
        chk("first modified", f"state {mmy(f['first_mod'])} (source value {f['first_mod'][5:]}{f['first_mod'][:4]})" in e)
    if base == "AV-G3-004":
        f = L[qids[0]]
        chk("last record is XX and prepaid", f["last_dq"] == "XX" and f["zb"] == "01" and f["peak"] == 0)
        chk("last period", f"final {mmy(f['last_period'])} record" in e)
    if base == "AV-G3-005":
        chk("valid id range", f"({P['ids'][0]} through {P['ids'][-1]})" in e)
    if base == "AV-G3-006":
        chk("credit-event loans", in_order(e, P["events"]) and f"list {['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'][len(P['events'])]} loan" in e)
    if base == "AV-G4-003":
        f = L[qids[0]]
        chk("modified, still active loan", f["first_mod"] and f["outcome"] == "active")
        chk("history figures", all(x in e for x in [f"{f['peak']} months delinquent ({mmy(f['peak_first'])})", mmy(f["first_mod"]), money(f["last_upb"])]))
    if base in ("AV-G5-002", "AV-G10-X01"):
        f = L[qids[0]]
        chk("modified then prepaid", f["first_mod"] and f["outcome"] == "prepaid")
        items = [str(f["peak"]), mmy(f["first_mod"]), f"{f['zb_date'][:2]}/{f['zb_date'][2:]}"]
        if f["rate_change"]:
            items += [f"{f['orig_rate']:g}%", f"{f['rate_change'][1]:g}%", mmy(f["rate_change"][0])]
        chk("history figures", all(x in e for x in items))
    if base == "AV-G5-004":
        f = L[qids[0]]
        chk("never late, still active", f["peak"] == 0 and f["outcome"] == "active")
        chk("figures", all(x in e for x in [money(f["orig_upb"]), money(f["last_upb"]), mmy(P["last"])]))
    if base in ("AV-G6-001", "AV-G16-X01", "AV-G21-001"):
        need = [f"{P['records']}", money(P["orig_total"])] + ([] if base == "AV-G16-X01" else [money(P["outstanding"]), f"{len(P['active'])} "])
        chk("pool summary figures", all(x in e for x in need))
    if base == "AV-G6-002":
        for name, o in [("prepaid or matured", "prepaid"), ("still active", "active")]:
            grp = [i for i in P["ids"] if L[i]["outcome"] == o]
            chk(f"{name} loans", f"{len(grp)} {name} ({', '.join(grp)})" in e)
        chk("repurchased and REO", f"1 repurchased ({rep})" in e and f"1 REO ({reo})" in e)
        chk("no other outcomes", all(L[i]["outcome"] in ("prepaid", "active", "repurchased", "REO") for i in P["ids"]))
    if base == "AV-G6-003":
        chk("90+ loans", f"{len(P['ever90'])} loans reaching 90+ days ({', '.join(P['ever90'])})" in e)
        chk("180+ loans and dates", all(f"{i} in {mmy(L[i]['first180'])}" in e for i in P["ever180"]))
    if base == "AV-G6-005":
        chk("modified loans", in_order(e, P["mods"]) and len(set(re.findall(r"\b\d{12}\b", e))) == len(P["mods"]))
        for i in P["mods"]:
            rc = L[i]["rate_change"]
            chk(f"rate change of {i}", (f"{rc[1]:g}% in {mmy(rc[0])}" in e) if rc else "no interest-rate change" in e)
    if base == "AV-G6-006":
        chk("profile figures", all(x in e for x in [f"{P['records']} records", f"filled on {len(P['history'])} of {P['records']}", mmy(P["last"])]))
    if base == "AV-G7-003":
        f = L[qids[0]]
        chk("purchase loan", f["purpose"] == "P")
        chk("implied price", money(round(f["orig_upb"] / (f["ltv"] / 100), 2)) in e)
    if base == "AV-G8-001":
        f = L[reo]
        chk("REO facts", qids == [reo] and money(f["upb_removal"]) in e and f"{f['zb_date'][:2]}/{f['zb_date'][2:]}" in e)
    if base == "AV-G8-003":
        f = L[qids[0]]
        chk("never late, active", f["peak"] == 0 and f["outcome"] == "active" and f"across {f['records']} records" in e and money(f["last_upb"]) in e)
    if base == "AV-G8-004":
        new = sorted(i for i in P["ids"] if L[i]["ltv"] >= 80 or L[i]["dti"] >= 36 or L[i]["min_score"] < 700)
        chk("new flagged count", f"to {len(new)}" in e or f"stay at {len(new)}" in e)
        chk("added loans", all(i in e for i in new if i not in P["flagged"]))
    if base == "AV-G8-005" and "capitalized" in q:
        i = qids[0]
        f, when = L[i], re.search(r"in (\d\d/\d{4})", q).group(1)
        rises = [(p, u) for (p, _, u, *_), (_, _, prev, *_) in zip(f["months"][1:], f["months"]) if u and prev and u > prev + 0.005 and p >= f["first_mod"]]
        chk("first balance rise after modification", rises and mmy(rises[0][0]) == when and money(rises[0][1]) in e)
    if base in ("AV-G5-003", "AV-G8-006", "AV-G5-001"):
        a = sum(1 for i in P["flagged"] if i in P["ever90"])
        b = sum(1 for i in P["unflagged"] if i in P["ever90"])
        w = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"]
        chk("flagged vs unflagged 90+ counts", f"{w[a]} later reached 90+" in e and f"{w[b]} of the {w[len(P['unflagged'])]} unflagged" in e)
    if base == "AV-G11-X02":
        i = re.search(r"name loan (\d{12})", e).group(1)
        chk("answer loan is flagged", i in P["flagged"])
        if "repurchased" in q:
            chk("only flagged repurchased loan", [j for j in P["flagged"] if L[j]["outcome"] == "repurchased"] == [i])
    if base == "AV-G13-X01":
        msas = set().union(*(L[i]["msas"] for i in P["ids"]))
        zips = set().union(*(L[i]["zips"] for i in P["ids"]))
        chk("all metro codes forbidden", msas <= set(case_forbidden.get("values", [])))
        chk("all zip codes forbidden", all(z in "".join(case_forbidden.get("patterns", [])) for z in zips))
    if base == "AV-G14-X01":
        from case_sets.make_cases import STATES
        names = {STATES.get(L[i]["state"], L[i]["state"]) for i in P["ids"]}
        chk("states are in the pool", all(s in names for s in re.findall(r"in (.+?) or (.+?)\.$", q)[0]))
    if base == "AV-G15-X01":
        f = L[reo]
        chk("REO dates", qids == [reo] and all(f"{d[:2]}/{d[2:]}" in e for d in [f["zb_date"], f["fc_date"], f["disp_date"]] if d))
    if base == "AV-G18-X01":
        chk("forbidden score is the loan's minimum score", case_forbidden.get("values") == [str(L[qids[0]]["min_score"])])
    if base == "AV-G22-002":
        chk("history count in question", f"on {len(P['history'])} of {P['records']} records" in q)
    if base == "AV-G22-003":
        ended = sum(1 for i in P["ids"] if L[i]["outcome"] != "active")
        w = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"]
        k = len(P["ever90"])
        chk("90+ count in question (true count and the changed count)", f"{k} of 8" in q and f"{k + 1 if k < 8 else k - 1} of 8" in q)
        chk("ended loans", f"{w[ended]} of the eight loans have already ended" in e)
    if base == "AV-G22-004":
        f = L[qids[0]]
        chk("true peak", f"peak delinquency is {f['peak']} months ({mmy(f['peak_first'])})" in e)
        chk("wrong figure is the delinquent-month count", f"peaked at {f['dq_months']} months" in q or "not supported by any record" in e)
    return out


case_forbidden = {}
DOC_OR_POLICY = {"AV-G7-001", "AV-G7-004", "AV-G7-005", "AV-G7-006", "AV-G1-004", "AV-G4-004", "AV-G4-006", "AV-G21-006", "AV-G22-001",
                 "AV-G22-005", "AV-G13-X01", "AV-G12-X01", "AV-G12-X02", "AV-G4-001", "AV-G4-002", "AV-G21-004", "AV-G21-005"}


# ---------------------------------------------------------------- run
def main():
    sets = sorted(p for p in HERE.glob("set[0-9][0-9]") if (p / "test_cases.json").exists())
    docs = {p.name: json.loads((p / "test_cases.json").read_text(encoding="utf-8")) for p in sets}
    wanted = {i for d in docs.values() for i in d["pool"]["loans"]}
    rows = load_rows(sys.argv[1] if len(sys.argv) > 1 else str(HERE.parent / "data" / "2007Q4.zip"), wanted)
    report = ["# Verification of the 50 case sets against the raw 2007Q4 file", "",
              "Checked by `case_sets/verify_cases.py`, whose code is separate from `make_cases.py`. It reads each loan's rows straight "
              "from `data/2007Q4.zip` and works out every fact again without the database or the agents' tool code.", ""]
    problems, n_checks, n_cases, ties = [], 0, 0, []
    q_all = collections.defaultdict(list)
    for name, d in docs.items():
        L = {i: loan_facts(rows[i]) for i in d["pool"]["loans"]}
        P = pool_facts(L)
        truth = truth_set(P)
        set_problems = []
        # C. pool-level sanity
        if len(P["reo"]) != 1 or len(P["rep"]) != 1:
            set_problems.append(f"{name}: expected exactly 1 REO loss loan and 1 repurchased loan, found {P['reo']} and {P['rep']}")
        if P["tie_in_screen"]:
            ties.append(name)
        if P["records"] != d["pool"]["records"] or mmy(P["last"]) != d["pool"]["last_period"]:
            set_problems.append(f"{name}: record count or last period differs from the raw file")
        for c in d["testCases"]:
            n_cases += 1
            base = c["metadata"]["basedOn"]
            inp = c["inputs"]
            q = " ".join(inp.get("Turns") or [inp["UserInput"]])
            e = c["expectations"]["expectedResponse"]["Response"]
            case_forbidden.clear()
            case_forbidden.update({"values": c["expectations"].get("forbiddenValues", []), "patterns": c["expectations"].get("forbiddenPatterns", [])})
            q_all[re.sub(r"\s+", " ", q.strip().lower())].append((name, base, e))
            # C. only this pool's loans
            stray = set(re.findall(r"\b\d{12}\b", q + " " + e)) - set(P["ids"]) - {"999999999999"}
            if stray:
                set_problems.append(f"{c['name']}: loans not in this pool: {sorted(stray)}")
            # A. every figure is real
            own_q = {_norm(x) for x in FACT.findall(q)}
            bad = [x for x in dict.fromkeys(_norm(x) for x in FACT.findall(re.sub(r"\{\{.*?\}\}", " ", e)))
                   if x not in truth and x not in CONSTANT and x not in own_q and not VERDICT.fullmatch(x)
                   and not (re.fullmatch(r"\d\d/\d{4}", x) and x.replace("/", "") in truth)]
            bad_q = [x for x in own_q if x not in truth and x not in CONSTANT and not (re.fullmatch(r"\d\d/\d{4}", x) and x.replace("/", "") in truth)]
            n_checks += 1
            if bad or bad_q:
                set_problems.append(f"{c['name']}: figures not found in the raw data: {bad + bad_q}")
            # B. key facts
            for what, ok in key_facts(base, q, e, P):
                n_checks += 1
                if not ok:
                    set_problems.append(f"{c['name']}: {what} - does not match the raw data")
        problems += set_problems
        print(f"{name}: {len(d['testCases'])} cases, {len(set_problems)} problems", flush=True)
    report += [f"- Sets: {len(docs)}; test cases: {n_cases}; checks run: {n_checks}",
               f"- **Problems found: {len(problems)}**", ""] + [f"  - {p}" for p in problems] + [
               "", f"- Sets where two flagged loans tie on flag count and CLTV ({len(ties)}): {', '.join(ties) or 'none'}. Their expected "
               "answers say that either order is correct for the tied loans, and this script checks that they do.", ""]

    # 4. repetition
    within = [(n, b, q) for q, hits in q_all.items() for n in {h[0] for h in hits}
              for b in [[h[1] for h in hits if h[0] == n]] if len(b) > 1]
    same_qa = {(q, e) for q, hits in q_all.items() for _, _, e in hits}
    by_base = collections.defaultdict(lambda: [set(), set()])
    for q, hits in q_all.items():
        for n, b, e in hits:
            by_base[b][0].add(q)
            by_base[b][1].add((q, e))
    report += ["## Repetition of questions", "",
               f"- {n_cases} questions; **{len(q_all)} different question texts**; {len(same_qa)} different question + answer pairs.",
               f"- Same question twice inside one set: {len(within)} cases. (The original 73 ask some things twice under two gates, for "
               "example the pool summary under G6 and G16; the sets give the second one a different wording.)", ""]
    seen = set()
    for n, b, q in sorted(within, key=lambda x: x[1]):
        if tuple(b) not in seen:
            seen.add(tuple(b))
            report.append(f"  - {' and '.join(b)}: \"{q[:90]}\"")
    report += ["", "- Across the 50 sets, per original test (different questions / different question + answer pairs, out of 50):", "",
               "| Original test | Different questions | Different question + answer | Note |", "|---|---|---|---|"]
    for b, (qs, qa) in sorted(by_base.items(), key=lambda x: (len(x[1][1]), x[0])):
        note = "document or policy question: same answer in every set, only the wording changes" if b in DOC_OR_POLICY else ""
        report.append(f"| {b} | {len(qs)} | {len(qa)} | {note} |")
    out = HERE / "verification_report.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"-> {len(problems)} problems in {n_checks} checks; {len(q_all)} different questions of {n_cases}; report {out.name}")


if __name__ == "__main__":
    main()

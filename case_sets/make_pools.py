"""CASE SETS - part 1: build 50 small loan pools (8 loans each) from one Fannie Mae acquisition quarter.

Each pool plays the same roles as the original 8-loan sample, so all 73 test cases still make sense:
  1 loan that ended in REO with a loss, 1 repurchased loan, 1 modified loan that later prepaid (with a rate cut),
  1 modified loan still active, 1 prepaid loan that was never late, 1 active loan that was never late, 2 others.
No loan is used in more than one pool.

Input : the quarter zip from Fannie Mae Data Dynamics (log in, Download Data, Single-Family, e.g. 2007 Q4).
        The zip is read directly; it is never unpacked (the CSV inside is many GB).
Output: case_sets/set01 ... set50, each with sample.csv (the 8 loans' raw rows) and loans.duckdb (same tables as data/).
        Fannie Mae's terms do not allow re-sharing: these files are git-ignored. Never publish them.
Usage : python case_sets/make_pools.py "C:/Users/you/Downloads/2007Q4.zip"
        python case_sets/make_pools.py 2007Q4.zip --sets 50 --seed 7
"""
import argparse
import csv
import io
import random
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from loan_agents import data  # noqa: E402

import duckdb  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("zip", help="the quarter zip downloaded from Data Dynamics")
ap.add_argument("--sets", type=int, default=50)
ap.add_argument("--seed", type=int, default=2026)
args = ap.parse_args()

I = {c: i for i, c in enumerate(data.COLS)}
SUMMARY = HERE / "_loan_summary.csv"   # pass-1 result, kept so a re-run skips the long first read


def lines(zip_path):
    """Every line of the CSV inside the zip, read as a stream."""
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as f:
            yield from io.TextIOWrapper(f, encoding="utf-8", errors="replace")


def num(v):
    try:
        return float(v)
    except ValueError:
        return None


# ---------------------------------------------------------------- pass 1: one summary row per loan
if SUMMARY.exists():
    loans = {r["id"]: r for r in csv.DictReader(SUMMARY.open(encoding="utf-8"))}
    print(f"pass 1 skipped: {len(loans):,} loans read from {SUMMARY.name}")
else:
    loans, n = {}, 0
    for line in lines(args.zip):
        f = line.rstrip("\n").split("|")
        if len(f) < 108:
            continue
        n += 1
        if n % 2_000_000 == 0:
            print(f"  {n:,} rows read, {len(loans):,} loans", flush=True)
        lid, per = f[I["loan_identifier"]], f[I["monthly_reporting_period"]]
        ym = per[2:] + per[:2]
        dq = f[I["current_loan_delinquency_status"]]
        rate = num(f[I["current_interest_rate"]])
        s = loans.get(lid)
        if s is None:
            s = loans[lid] = {"id": lid, "rows": 0, "max_dq": 0, "last_ym": "", "last_dq": "", "mod": 0, "zb": "",
                              "nsp": "", "rate_min": 99.0, "rate_max": 0.0,
                              "ltv": f[I["original_loan_to_value_ratio_ltv"]], "cltv": f[I["original_combined_loan_to_value_ratio_cltv"]],
                              "dti": f[I["debt_to_income_dti"]], "score": f[I["borrower_credit_score_at_origination"]],
                              "co_score": f[I["co_borrower_credit_score_at_origination"]], "borrowers": f[I["number_of_borrowers"]],
                              "purpose": f[I["loan_purpose"]], "state": f[I["property_state"]], "zip": f[I["zip_code_short"]]}
        s["rows"] += 1
        if dq.isdigit():
            s["max_dq"] = max(s["max_dq"], int(dq))
        if ym > s["last_ym"]:
            s["last_ym"], s["last_dq"] = ym, dq
        if f[I["modification_flag"]] == "Y":
            s["mod"] = 1
        if f[I["zero_balance_code"]]:
            s["zb"] = f[I["zero_balance_code"]]
        if num(f[I["net_sales_proceeds"]]):
            s["nsp"] = f[I["net_sales_proceeds"]]
        if rate:
            s["rate_min"], s["rate_max"] = min(s["rate_min"], rate), max(s["rate_max"], rate)
    with SUMMARY.open("w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=list(next(iter(loans.values()))))
        w.writeheader()
        w.writerows(loans.values())
    print(f"pass 1 done: {n:,} rows, {len(loans):,} loans -> {SUMMARY.name}")

# ---------------------------------------------------------------- pick the pools
last = max(s["last_ym"] for s in loans.values())
for s in loans.values():
    for k in ("rows", "max_dq", "mod"):
        s[k] = int(s[k])
    s["rate_min"], s["rate_max"] = float(s["rate_min"]), float(s["rate_max"])
complete = [s for s in loans.values() if s["ltv"] and s["cltv"] and s["dti"] and s["score"] and s["zip"] and s["state"]]
active = lambda s: s["zb"] == "" and s["last_ym"] == last
ROLES = {   # role -> who can play it
    "reo_loss": lambda s: s["zb"] == "09" and s["nsp"] != "",
    "repurchased": lambda s: s["zb"] == "06" and s["max_dq"] >= 1,
    "modified_prepaid": lambda s: s["mod"] and s["zb"] == "01" and s["rate_max"] - s["rate_min"] >= 0.5 and s["max_dq"] >= 3,
    "modified_active": lambda s: s["mod"] and active(s) and s["max_dq"] >= 3,
    "clean_prepaid": lambda s: s["zb"] == "01" and s["max_dq"] == 0 and s["last_dq"] == "XX" and not s["mod"],
    "clean_active": lambda s: active(s) and s["max_dq"] == 0 and not s["mod"],
}
FILL = lambda s: (s["zb"] == "01" or active(s)) and not s["mod"]   # the 2 extra loans: prepaid or active, never modified
pools_by_role = {r: [s for s in complete if ok(s)] for r, ok in ROLES.items()}
fill = [s for s in complete if FILL(s)]
for r, ss in pools_by_role.items():
    print(f"  candidates for {r:17}: {len(ss):,}")
rng = random.Random(args.seed)


def flags(s):
    ltv, cltv, dti = int(s["ltv"]), int(s["cltv"]), int(s["dti"])
    low = min(int(s["score"]), int(s["co_score"]) if s["co_score"] else 9999)
    return (ltv >= 80) + (dti >= 43) + (low < 700) + (cltv > ltv)


def good(pool):
    """The pool must support every test case: some loans flagged by the default screen and some not, an LTV >= 80 loan,
    a single-borrower loan with no co-borrower score, a purchase loan, and 8 different states-or-zips is not required."""
    nflag = sum(1 for s in pool if flags(s))
    return (1 <= nflag <= 6 and any(int(s["ltv"]) >= 80 for s in pool)
            and any(s["borrowers"] == "1" and not s["co_score"] for s in pool)
            and any(s["purpose"] == "P" for s in pool) and len({s["state"] for s in pool}) >= 2)


used, pools = set(), []
tries = 0
while len(pools) < args.sets + 10 and tries < 200_000:   # 10 spare pools, in case a pool fails the checks after the build
    tries += 1
    pool = []
    for r in ROLES:
        cands = [s for s in rng.sample(pools_by_role[r], min(40, len(pools_by_role[r]))) if s["id"] not in used]
        if not cands:
            break
        pool.append(cands[0] | {"role": r})
    if len(pool) < len(ROLES):
        continue
    extra = [s for s in rng.sample(fill, 40) if s["id"] not in used and s["id"] not in {p["id"] for p in pool}][:2]
    pool += [s | {"role": "other"} for s in extra]
    if len(pool) == 8 and good(pool):
        pools.append(pool)
        used |= {s["id"] for s in pool}
print(f"picked {len(pools)} candidate pools ({tries} tries)")

# ---------------------------------------------------------------- pass 2: copy each pool's raw rows, build its database
which = {s["id"]: i for i, pool in enumerate(pools) for s in pool}
buf = {i: [] for i in range(len(pools))}
for line in lines(args.zip):
    i = which.get(line.split("|", 2)[1])
    if i is not None:
        # Files released from late 2023 add fields 109-114 at the END of each row (payment deferral flag, interest-bearing
        # balance, "Classic FICO" scores). Fields 1-108 are unchanged, so keep those: the same layout as the sample file.
        buf[i].append("|".join(line.rstrip("\r\n").split("|")[:108]) + "\n")

KEEP = [r[0] for r in duckdb.connect(str(data.DATA / "loans.duckdb"), read_only=True).execute("DESCRIBE loan_monthly").fetchall()
        if r[0] != "period_ym"]   # the same 61 columns as the original sample


def checks(db: Path) -> list[str]:
    """Problems that would make a test case meaningless for this pool (empty list = fine)."""
    con = duckdb.connect(str(db), read_only=True)
    q = lambda sql: con.execute(sql).fetchall()
    out = []
    if q("SELECT count(*) FROM loan_features WHERE indicative_net_loss > 0")[0][0] != 1:
        out.append("needs exactly one REO loan with a positive indicative loss")
    if q("SELECT count(*) FROM loan_features WHERE outcome = 'repurchased'")[0][0] != 1:
        out.append("needs exactly one repurchased loan")
    if q("SELECT count(*) FROM loan_features WHERE first_modified_period IS NOT NULL")[0][0] < 2:
        out.append("needs two modified loans")
    if q("SELECT count(*) FROM loan_features WHERE outcome NOT IN ('active', 'prepaid or matured', 'repurchased', 'REO (deed-in-lieu or bank-owned)')")[0][0]:
        out.append("has an unexpected outcome")
    if q("SELECT count(*) FROM loan_monthly WHERE foreclosure_date <> '' OR disposition_date <> ''")[0][0] == 0:
        out.append("REO loan has no foreclosure or disposition date")
    con.close()
    return out


done = 0
for i, pool in enumerate(pools):
    if done == args.sets:
        break
    folder = HERE / f"set{done + 1:02d}"
    folder.mkdir(exist_ok=True)
    (folder / "sample.csv").write_text("".join(buf[i]), encoding="utf-8")
    data.build_db(folder / "sample.csv", folder / "loans.duckdb", keep=KEEP)
    problems = checks(folder / "loans.duckdb")
    if problems:
        print(f"  pool {i + 1} skipped: {'; '.join(problems)}")
        continue
    (folder / "roles.csv").write_text("loan_id,role\n" + "".join(f"{s['id']},{s['role']}\n" for s in pool), encoding="utf-8")
    done += 1
    print(f"  {folder.name}: 8 loans, {len(buf[i])} monthly records", flush=True)
print(f"-> {done} pools in case_sets/set01 ... set{done:02d}")

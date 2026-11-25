"""Load the public Fannie Mae sample (8 loans, 757 monthly rows) into a small local database.

Tables (read-only for the agents):
  loan_static   one row per loan  - facts fixed at origination (credit score, LTV, DTI, ...)
  loan_monthly  one row per month - performance (balance, delinquency, modification, ...)
"""
import os
import re
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent.parent
load_dotenv(HERE / ".env")
DATA = HERE / "data"
# CASE_SET=set07 (in .env) switches the whole run to one of the 50 case sets: its own 8-loan pool and its own 73 cases.
CASE_SET = os.getenv("CASE_SET", "").strip()
SET_DIR = HERE / "case_sets" / CASE_SET if CASE_SET else None
# CASE_SET=senior (2,440 cases as given) or senior_unique (exact copies removed): the senior's extra cases, written for the ORIGINAL 8-loan sample
DB_FILE = SET_DIR / "loans.duckdb" if CASE_SET and not CASE_SET.startswith("senior") else DATA / "loans.duckdb"
SAMPLE_CSV = DATA / "sf-loan-performance-data-sample.csv"

# The 108 field names, in file order (from Fannie Mae's "Glossary and File Layout"). The file has no header row.
FIELDS = ['Reference Pool ID', 'Loan Identifier', 'Monthly Reporting Period', 'Channel', 'Seller Name', 'Servicer Name', 'Master Servicer', 'Original Interest Rate', 'Current Interest Rate', 'Original UPB', 'UPB at Issuance', 'Current Actual UPB', 'Original Loan Term', 'Origination Date', 'First Payment Date', 'Loan Age', 'Remaining Months to Legal Maturity', 'Remaining Months To Maturity', 'Maturity Date', 'Original Loan to Value Ratio (LTV)', 'Original Combined Loan to Value Ratio (CLTV)', 'Number of Borrowers', 'Debt-To-Income (DTI)', 'Borrower Credit Score at Origination', 'Co-Borrower Credit Score at Origination', 'First Time Home Buyer Indicator', 'Loan Purpose', 'Property Type', 'Number of Units', 'Occupancy Status', 'Property State', 'Metropolitan Statistical Area (MSA) or Metropolitan Statistical Division Area (MSDA)', 'Zip Code Short', 'Mortgage Insurance Percentage', 'Amortization Type', 'Prepayment Penalty Indicator', 'Interest Only Loan Indicator', 'Interest Only First Principal And Interest Payment Date', 'Months to Amortization', 'Current Loan Delinquency Status', 'Loan Payment History', 'Modification Flag', 'Mortgage Insurance Cancellation Indicator', 'Zero Balance Code', 'Zero Balance Effective Date', 'UPB at the Time of Removal', 'Repurchase Date', 'Scheduled Principal Current', 'Total Principal Current', 'Unscheduled Principal Current', 'Last Paid Installment Date', 'Foreclosure Date', 'Disposition Date', 'Foreclosure Costs', 'Property Preservation and Repair Costs', 'Asset Recovery Costs', 'Miscellaneous Holding Expenses and Credits', 'Associated Taxes for Holding Property', 'Net Sales Proceeds', 'Credit Enhancement Proceeds', 'Repurchase Make Whole Proceeds', 'Other Foreclosure Proceeds', 'Modification-Related Non-Interest Bearing UPB', 'Principal Forgiveness Amount', 'Original List Start Date', 'Original List Price', 'Current List Start Date', 'Current List Price', 'Borrower Credit Score At Issuance', 'Co-Borrower Credit Score At Issuance', 'Borrower Credit Score Current', 'Co-Borrower Credit Score Current', 'Mortgage Insurance Type', 'Servicing Activity Indicator', 'Current Period Modification Loss Amount', 'Cumulative Modification Loss Amount', 'Current Period Credit Event Net Gain or Loss', 'Cumulative Credit Event Net Gain or Loss', 'Special Eligibility Program', 'Foreclosure Principal Write-off Amount', 'Relocation Mortgage Indicator', 'Zero Balance Code Change Date', 'Loan Holdback Indicator', 'Loan Holdback Effective Date', 'Delinquent Accrued Interest', 'Property Valuation Method', 'High Balance Loan Indicator', 'ARM Initial Fixed-Rate Period 5 YR Indicator', 'ARM Product Type', 'Initial Fixed-Rate Period', 'Interest Rate Adjustment Frequency', 'Next Interest Rate Adjustment Date', 'Next Payment Change Date', 'Index', 'ARM Cap Structure', 'Initial Interest Rate Cap Up Percent', 'Periodic Interest Rate Cap Up Percent', 'Lifetime Interest Rate Cap Up Percent', 'Mortgage Margin', 'ARM Balloon Indicator', 'ARM Plan Number', 'Borrower Assistance Plan', 'High Loan to Value (HLTV) Refinance Option Indicator', 'Deal Name', 'Repurchase Make Whole Proceeds Flag', 'Alternative Delinquency Resolution', 'Alternative Delinquency Resolution Count', 'Total Deferral Amount']
COLS = [re.sub(r"[^a-z0-9]+", "_", f.lower()).strip("_") for f in FIELDS]

KB_FILE = DATA / "kb_passages.json"   # text of the Fannie Mae PDFs, prepared locally (the PDFs are not needed after step 1)

# Columns kept but worth knowing about: they say nothing inside this 8-loan sample, or are location details.
LOCATION = ["zip_code_short", "metropolitan_statistical_area_msa_or_metropolitan_statistical_division_area_msda"]

# loan_static: one row per loan, with the short column names the test cases use (loan_id, state, min_score, ...)
STATIC_SQL = """
CREATE TABLE loan_static AS
SELECT loan_identifier AS loan_id,
       any_value(channel) AS channel,
       any_value(property_state) AS state,
       any_value(loan_purpose) AS purpose,              -- P purchase, C cash-out refinance, R refinance
       any_value(property_type) AS property_type,
       max(TRY_CAST(number_of_units AS INT)) AS num_units,
       max(TRY_CAST(number_of_borrowers AS INT)) AS num_borrowers,
       any_value(origination_date) AS orig_date,       -- MMYYYY
       max(TRY_CAST(original_loan_term AS INT)) AS orig_term,
       max(TRY_CAST(original_interest_rate AS DOUBLE)) AS orig_rate,
       max(TRY_CAST(original_upb AS DOUBLE)) AS orig_upb,
       max(TRY_CAST(original_loan_to_value_ratio_ltv AS INT)) AS ltv,
       max(TRY_CAST(original_combined_loan_to_value_ratio_cltv AS INT)) AS cltv,
       max(TRY_CAST(debt_to_income_dti AS INT)) AS dti,
       max(TRY_CAST(NULLIF(borrower_credit_score_at_origination,'') AS INT)) AS borrower_score,
       max(TRY_CAST(NULLIF(co_borrower_credit_score_at_origination,'') AS INT)) AS co_borrower_score,   -- NULL = no co-borrower score
       least(max(TRY_CAST(NULLIF(borrower_credit_score_at_origination,'') AS INT)),
             coalesce(max(TRY_CAST(NULLIF(co_borrower_credit_score_at_origination,'') AS INT)), 9999)) AS min_score,
       max(TRY_CAST(NULLIF(mortgage_insurance_percentage,'') AS DOUBLE)) AS mi_pct
FROM raw GROUP BY loan_identifier ORDER BY loan_identifier
"""
# The configured default risk screen (thresholds are illustrative): one flag column per rule, plus flag_count.
SCREEN_SQL = """
CREATE VIEW default_risk_screen AS
SELECT loan_id, state, purpose, orig_upb, ltv, cltv, dti, min_score,
       CAST(ltv >= 80 AS INT) AS flag_ltv_80, CAST(dti >= 43 AS INT) AS flag_dti_43,
       CAST(min_score < 700 AS INT) AS flag_min_score_700, CAST(cltv > ltv AS INT) AS flag_cltv_above_ltv,
       CAST(ltv >= 80 AS INT) + CAST(dti >= 43 AS INT) + CAST(min_score < 700 AS INT) + CAST(cltv > ltv AS INT) AS flag_count
FROM loan_static
"""
MONEY = ["current_actual_upb", "upb_at_the_time_of_removal", "total_principal_current", "foreclosure_costs",
         "property_preservation_and_repair_costs", "asset_recovery_costs", "miscellaneous_holding_expenses_and_credits",
         "associated_taxes_for_holding_property", "net_sales_proceeds", "current_interest_rate"]


def read_sample(csv: Path = SAMPLE_CSV) -> pd.DataFrame:
    return pd.read_csv(csv, sep="|", header=None, names=COLS, dtype=str, keep_default_na=False)


def clean(df: pd.DataFrame, keep: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    """Drop only the columns that are empty on every row (108 -> 61). Note the kept columns that carry little information.
    keep: use this exact column list instead (the case sets keep the same 61 columns as the original sample)."""
    filled = {c: df[c][df[c] != ""] for c in df}
    empty = [c for c in df if c not in keep] if keep else [c for c in df if filled[c].empty]
    zero = [c for c in df if c not in empty and filled[c].str.fullmatch(r"0*\.?0*").all()]
    single = [c for c in df if c not in empty + zero and len(filled[c]) == len(df) and filled[c].nunique() == 1]
    report = {"kept": len(df.columns) - len(empty), "empty": len(empty), "empty_cols": empty, "zero_cols": zero,
              "single_cols": {c: filled[c].iloc[0] for c in single}, "location_cols": LOCATION}
    return df.drop(columns=empty), report


def build_db(csv: Path = SAMPLE_CSV, db: Path | None = None, keep: list[str] | None = None) -> dict:
    """Clean the CSV and create data/loans.duckdb. Run by step 1 on your own computer (data preparation is local).
    The case-set maker calls it with its own csv, db and the fixed list of 61 columns."""
    db = db or DB_FILE
    df, report = clean(read_sample(csv), keep)
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    con.register("raw", df)
    con.execute(STATIC_SQL)
    con.execute(SCREEN_SQL)
    cast = lambda c: f"TRY_CAST(NULLIF({c},'') AS DOUBLE) AS {c}" if c in MONEY else c
    con.execute("CREATE TABLE loan_monthly AS SELECT "                       # all 61 kept source columns
                + ", ".join(cast(c) for c in df.columns)
                + ", substr(monthly_reporting_period,3,4) || '-' || substr(monthly_reporting_period,1,2) AS period_ym"
                + " FROM raw ORDER BY loan_identifier, period_ym")
    con.execute(FEATURES_SQL)
    con.close()
    report["features"] = [r[0] for r in duckdb.connect(str(db), read_only=True).execute("DESCRIBE loan_features").fetchall()]
    if keep is None:
        write_cleaning_report(report)
    return report


def build_kb() -> int:
    """Extract the text of the Fannie Mae PDFs into data/kb_passages.json (one entry per passage, with file and page)."""
    import json
    from pypdf import PdfReader
    out = []
    for pdf in sorted(DATA.glob("*.pdf")):
        for page_no, page in enumerate(PdfReader(pdf).pages, start=1):
            for chunk in re.split(r"\n\s*\n|(?<=\.)\n", page.extract_text() or ""):
                if len(chunk.strip()) > 60:
                    out.append({"source": pdf.name, "page": page_no, "text": " ".join(chunk.split())})
    KB_FILE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return len(out)


# Feature extraction: one row per loan with the facts the analysis needs most.
FEATURES_SQL = """
CREATE TABLE loan_features AS
WITH m AS (SELECT *, TRY_CAST(NULLIF(current_loan_delinquency_status,'XX') AS INT) AS dq FROM loan_monthly),
agg AS (
  SELECT loan_identifier,
         count(*) AS monthly_records,
         min(period_ym) AS first_period, max(period_ym) AS last_period,
         coalesce(max(dq), 0) AS peak_months_delinquent,
         count(*) FILTER (WHERE dq >= 1) AS delinquent_months,
         min(period_ym) FILTER (WHERE dq >= 3) AS first_90_plus_period,
         min(period_ym) FILTER (WHERE dq >= 6) AS first_180_plus_period,
         min(period_ym) FILTER (WHERE modification_flag = 'Y') AS first_modified_period,
         max(NULLIF(zero_balance_code,'')) AS zero_balance_code,
         max(NULLIF(zero_balance_effective_date,'')) AS zero_balance_effective_date,
         max(upb_at_the_time_of_removal) AS upb_at_removal,
         coalesce(sum(foreclosure_costs),0) + coalesce(sum(property_preservation_and_repair_costs),0)
           + coalesce(sum(asset_recovery_costs),0) + coalesce(sum(miscellaneous_holding_expenses_and_credits),0)
           + coalesce(sum(associated_taxes_for_holding_property),0) AS disposition_costs_raw,
         max(net_sales_proceeds) AS net_sales_proceeds,
         max(current_actual_upb) AS max_upb_seen
  FROM m GROUP BY loan_identifier),
peak AS (SELECT loan_identifier, min(period_ym) AS peak_first_period FROM m
         WHERE (loan_identifier, dq) IN (SELECT loan_identifier, max(dq) FROM m GROUP BY 1) GROUP BY 1),
last AS (SELECT loan_identifier, current_actual_upb AS last_upb, current_loan_delinquency_status AS last_delinquency_status,
                current_interest_rate AS last_interest_rate
         FROM m QUALIFY row_number() OVER (PARTITION BY loan_identifier ORDER BY period_ym DESC) = 1)
SELECT a.loan_identifier, s.state AS property_state, s.orig_upb AS original_upb, s.orig_rate AS original_interest_rate,
       s.ltv, s.cltv, s.dti, s.borrower_score AS borrower_credit_score, s.co_borrower_score AS co_borrower_credit_score,
       s.min_score AS borrower_minimum_credit_score, s.cltv > s.ltv AS has_subordinate_financing,
       a.monthly_records, a.first_period, a.last_period, a.peak_months_delinquent, p.peak_first_period, a.delinquent_months,
       a.first_90_plus_period, a.first_180_plus_period, a.first_modified_period,
       CASE a.zero_balance_code WHEN '01' THEN 'prepaid or matured' WHEN '06' THEN 'repurchased'
            WHEN '09' THEN 'REO (deed-in-lieu or bank-owned)' ELSE 'active' END AS outcome,
       a.zero_balance_code, a.zero_balance_effective_date, a.upb_at_removal, round(a.disposition_costs_raw, 2) AS disposition_costs, a.net_sales_proceeds,
       CASE WHEN a.net_sales_proceeds IS NOT NULL THEN round(a.upb_at_removal + a.disposition_costs_raw - a.net_sales_proceeds, 2) END AS indicative_net_loss,
       CASE WHEN a.net_sales_proceeds IS NOT NULL THEN round((a.upb_at_removal + a.disposition_costs_raw - a.net_sales_proceeds) / a.upb_at_removal * 100, 1) END AS indicative_severity_pct,
       a.max_upb_seen, l.last_upb, l.last_delinquency_status, l.last_interest_rate
FROM agg a JOIN loan_static s ON s.loan_id = a.loan_identifier JOIN peak p USING (loan_identifier) JOIN last l USING (loan_identifier)
ORDER BY a.loan_identifier
"""


def write_cleaning_report(r: dict) -> None:
    out = HERE / "results" / "data_cleaning.md"
    out.parent.mkdir(exist_ok=True)
    lines = ["# Data cleaning report", "",
             "Source: Fannie Mae public sample file, 108 columns, 757 monthly records, 8 loans. Prepared on our own computer (step 1).",
             f"Kept **{r['kept']} columns** (the same 61 'active fields' the test cases describe). "
             f"Dropped **{r['empty']} columns that are empty on every row**: {', '.join(r['empty_cols'])}", "",
             "## Kept, but worth knowing", "",
             f"- **All zero** (nothing happened in this sample): {', '.join(r['zero_cols'])}",
             "- **One value on every row** (no variation in this sample): "
             + ", ".join(f"{c} = {v}" for c, v in r["single_cols"].items()),
             f"- **Location details** (3-digit zip, metro area): {', '.join(r['location_cols'])}. "
             "The agents are told never to reveal or infer where a borrower lives.", "",
             "## Tables built", "",
             "- `loan_monthly`: the 61 kept columns, one row per loan per month (757 rows).",
             "- `loan_static`: one row per loan with short names (loan_id, state, purpose, orig_upb, ltv, cltv, dti, min_score, ...).",
             "- `default_risk_screen` (view): the configured screen with one flag per rule and `flag_count`.",
             "- `loan_features`: derived facts per loan: " + ", ".join(r["features"])]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pool_profile() -> dict:
    """Size of the loan pool in use: loans, monthly records and last reporting period (MM/YYYY). The agent prompts quote these."""
    n_loans, n_rows, last = connect().execute(
        "SELECT count(DISTINCT loan_identifier), count(*), max(period_ym) FROM loan_monthly").fetchone()
    return {"loans": n_loans, "records": n_rows, "last_period": f"{last[5:]}/{last[:4]}"}


def connect(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Agents always get a READ-ONLY connection, so no tool can change the tables."""
    return duckdb.connect(str(DB_FILE), read_only=read_only)


def fingerprint() -> int:
    """A checksum of every row of the two data tables (changes if any value is changed, added or deleted)."""
    con = connect()
    return con.execute("SELECT (SELECT sum(hash(t)) FROM loan_static t) + (SELECT sum(hash(m)) FROM loan_monthly m)").fetchone()[0]


def schema_text(con) -> str:
    out = []
    for t in ("loan_static", "default_risk_screen", "loan_features", "loan_monthly"):
        cols = con.execute(f"DESCRIBE {t}").fetchall()
        out.append(f"CREATE TABLE {t} (\n  " + ",\n  ".join(f"{c[0]} {c[1]}" for c in cols) + "\n);")
    out.append("-- loan_static.loan_id = loan_features.loan_identifier = loan_monthly.loan_identifier. purpose: P purchase, C cash-out refinance, R refinance.\n"
               "-- default_risk_screen = the configured default screen (LTV >= 80, DTI >= 43, min_score < 700, CLTV > LTV).\n"
               "--   Run it as: SELECT * FROM default_risk_screen WHERE flag_count > 0 ORDER BY flag_count DESC, cltv DESC\n"
               "-- For a custom screen, query loan_static with the user's thresholds; order by the number of rules hit, then cltv, both descending.\n"
               "-- co_borrower_score NULL means no co-borrower score on file: keep it NULL, never replace it.\n"
               "-- loan_monthly money columns are numbers; other values are TEXT. monthly_reporting_period is MMYYYY; period_ym is YYYY-MM (sortable).\n"
               "-- current_loan_delinquency_status = months behind ('00' current, 'XX' unknown).\n"
               "-- zero_balance_code: 01 prepaid or matured, 02 third-party sale, 03 short sale, 06 repurchased, 09 deed-in-lieu / REO (bank-owned), 15 note sale.")
    return "\n".join(out)

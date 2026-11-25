# Test cases for the final run: two experiments

| Experiment | What | Cases | Data | Run it with |
|---|---|---|---|---|
| 1 | Our 50 case sets (below) | 3,650 | 50 pools of 8 loans from 2007 Q4 | `python run_experiment.py 1` |
| 2 | The senior's extra test cases, exact copies removed | 1,173 (from 2,440) | the original 8-loan sample | `python run_experiment.py 2` |
| (2 as given) | The senior's file unchanged, copies included | 2,440 | the original 8-loan sample | `CASE_SET=senior` in `.env`, then steps 1-6 |

The step-by-step guide for running both is in the main `README.md`, section 0.

**Experiment 2.** The senior's file (`extra_test_cases.json` in the project root) is copied, unchanged, to
`senior/test_cases.json`. Its figures all match the 8-loan sample (checked: the only figures not in the data are the
made-up loan numbers of "loan not found" tests and the $218,750 implied price, both intended). But 1,267 of its 2,440
cases are exact copies: the same question with the same answer, copied into up to 22 gates. `senior_unique/test_cases.json`
keeps each question-and-answer pair once (under its first gate) and lists every dropped copy under `droppedCopies`.

# 50 case sets: 73 × 50 = 3,650 test cases

The original test uses **one** pool of 8 loans and **73** test cases. This folder holds **50 more case sets**.
Each set has:

- its **own pool of 8 different loans**, taken from Fannie Mae's full loan data for one acquisition quarter (2007 Q4);
- its **own 73 test cases**. They are the same 73 tests (same quality gate, same agent, same purpose), but with
  that pool's loans, numbers and slightly different wording.

No loan is used in two sets. **No artificial intelligence model wrote any expected answer**: every figure is
worked out by code from the pool's own data, using the same tool code the agents use.

## What is in each set folder

| File | What it is | Share it? |
|---|---|---|
| `test_cases.json` | The 73 test cases (same layout as `extra_test_cases_G9_G20.json`) | Yes |
| `roles.csv` | Which loan plays which part (REO loss, repurchased, modified, ...) | Yes |
| `answer_key_check.md` | The self-check: every figure in every expected answer was found in the data | Yes |
| `sample.csv` | The 8 loans' raw monthly rows from Fannie Mae | **No** (Fannie Mae terms) |
| `loans.duckdb` | The prepared database the agents read (same tables as `data/loans.duckdb`) | **No** (Fannie Mae terms) |

`sample.csv` and `loans.duckdb` are listed in `.gitignore`. Everyone who needs them builds them again (next section).

## How the sets were made (only needed once)

1. **Download one quarter.** Log in at datadynamics.fanniemae.com (free account), open **Download Data →
   Single-Family Loan Performance Data**, and in the quarterly table click **2007 → Q4 "Acquisition and Performance"**.
   You get `2007Q4.zip` (383 MB; the CSV inside is 6.2 GB, and you never need to unpack it).
   **Do not** click the "Primary 2000Q1-2026Q2" file: it holds every quarter and needs about 60 GB.
2. Put the zip in `data/2007Q4.zip`.
3. Build the 50 pools (about 15 minutes; it reads the zip twice):
   ```
   python case_sets/make_pools.py data/2007Q4.zip
   ```
4. Write the 73 cases for every pool (about 5 minutes):
   ```
   python case_sets/make_cases.py
   ```
   The last line must say `0 cases with answer key problems`.
5. Check every set against the raw file with separate code (about 5 minutes the first time, then seconds):
   ```
   python case_sets/verify_cases.py data/2007Q4.zip
   ```
   It reads the 400 loans straight from the zip and works out every fact again, without our database or the agents'
   tool code, so a bug there cannot hide itself. It checks that every figure in every question and answer is real,
   that each figure belongs to the right loan and is in the right order, and that questions do not repeat inside a set.
   The last line must say `0 problems`. Our result is in `verification_report.md`: **0 problems in 9,026 checks**.
6. Make the single file for sharing: `all_case_sets_3650.json` holds all 3,650 cases (internal use only).

### Ties in the screen order

In 13 sets, two flagged loans have the same number of rules hit and the same CLTV. The screen orders by those two
values only, so the order of those two loans is not fixed. Their expected answers say "either order is correct for
them", so an agent is not marked wrong for listing them the other way round.

### Repeated questions

- Inside one set, no question repeats. (The original 73 ask the pool summary, the default screen and the REO loss
  twice, under two gates; the sets give the second one a different wording.)
- Across the 50 sets there are 1,863 different question texts. Questions about loans name that set's own loans, so their
  answers always differ. Questions about Fannie Mae's documents or about policy (for example "what does Net Severity
  mean", "ignore your instructions") have the same correct answer in every set, so for those only the wording changes
  (3 to 5 wordings each).

The same seed always picks the same loans, so everyone who runs steps 3 and 4 gets identical sets.

### Why each pool works with all 73 tests

Every pool has the same "cast" as the original sample, so every test still has a loan to ask about:

| Part | Loan | Used by, for example |
|---|---|---|
| REO loss | ended in REO (zero balance code 09) with sale proceeds, so the loss can be worked out | G2-003, G6-004, G11, G21-002 |
| Repurchased | repurchased (code 06) after being late at least once | G2-006, G8-002 |
| Modified, then prepaid | modified, rate cut by at least 0.5 points, later paid off | G3-003, G5-002, G6-005, G10 |
| Modified, still active | modified, at least 90 days late at some point, still open | G4-001, G4-003, G21-005 |
| Clean prepaid | never late, paid off, last status "XX" | G3-004 |
| Clean active | never late, still open | G5-004, G8-003 |
| 2 others | paid off or still open, never modified | — |

A pool is also checked for: 1 to 6 loans flagged by the default risk screen, a loan with LTV of 80 or more, a
single-borrower loan with no co-borrower score, a purchase loan, and more than one state.

### What differs from the original 73 (on purpose)

- **AV-G2-005 and AV-G21-003** (closest peers): the distances come from our `cohort_comparison` tool, so they can now be
  reproduced. The expected tool is `cohort_comparison`, not `memory_read`.
- **AV-G6-006** (audit): the original asked for "ten checks (5 PASS, 2 WARN, 3 NOTE)" that no tool produces. The sets
  ask for the validation profile the `data_validation` tool really returns, plus a passing citation check.
- **AV-G1-006**: the data now runs to 06/2026, so the year asked about is chosen per set; the answer is still "the
  sample cannot give a book-wide rate".
- **AV-G7-001, G7-004, G7-005, G7-006** ask about Fannie Mae's documents, which are the same for every set, so their
  answers do not change. Only the wording of other questions changes.

## How to run one set

Add one line to `.env`, then run steps 1 to 6 exactly as in the main README:

```
CASE_SET=set07
```

With `CASE_SET` set:

- the agents read `case_sets/set07/loans.duckdb` (their instructions quote that pool's record count and last period);
- the steps use `case_sets/set07/test_cases.json`;
- results go to their own folder, `results/<provider>-<AGENT_VERSION>-set07`, so no set overwrites another;
- Arize AX and Braintrust get their own dataset, `loan-agent-test-cases-set07`.

Remove the line (or leave it empty) to go back to the original 73 cases.

To run all 50 sets one after the other, use the runner (it sets `CASE_SET` for each set itself; leave it out of `.env`):

```
python run_experiment.py 1
```

## Time and cost (estimate from our 73-case run)

| | One set | 50 sets |
|---|---|---|
| Agent run (step 3) | about 23 minutes, about $3.45 | about 19 hours, about $175 |
| Grading (steps 4 and 5) | about 8 minutes, about $0.14 | about 7 hours, about $7 |

One sandbox lasts 8 hours, so plan about 4 sandboxes and **download each set's results folder before the sandbox ends**.
The sandbox terms say to use only data that Amazon Web Services provides, so check this before uploading Fannie Mae files there.

## Words used here

- **Pool**: the 8 loans one set works with.
- **Case set**: one pool plus its 73 test cases.
- **REO** (real estate owned): the lender took the house back and sold it.
- **Repurchased**: the lender that sold the loan to Fannie Mae had to buy it back.
- **LTV / CLTV** (loan-to-value / combined loan-to-value): the loan (or all loans) as a percentage of the home's value.
- **DTI** (debt-to-income): the borrower's monthly debts as a percentage of monthly income.

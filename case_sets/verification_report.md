# Verification of the 50 case sets against the raw 2007Q4 file

Checked by `case_sets/verify_cases.py`, whose code is separate from `make_cases.py`. It reads each loan's rows straight from `data/2007Q4.zip` and works out every fact again without the database or the agents' tool code.

- Sets: 50; test cases: 3650; checks run: 9026
- **Problems found: 0**


- Sets where two flagged loans tie on flag count and CLTV (13): set04, set10, set18, set19, set24, set25, set28, set33, set44, set46, set47, set49, set50. Their expected answers say that either order is correct for the tied loans, and this script checks that they do.

## Repetition of questions

- 3650 questions; **1863 different question texts**; 3043 different question + answer pairs.
- Same question twice inside one set: 0 cases. (The original 73 ask some things twice under two gates, for example the pool summary under G6 and G16; the sets give the second one a different wording.)


- Across the 50 sets, per original test (different questions / different question + answer pairs, out of 50):

| Original test | Different questions | Different question + answer | Note |
|---|---|---|---|
| AV-G7-006 | 3 | 3 | document or policy question: same answer in every set, only the wording changes |
| AV-G1-004 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G21-006 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G4-006 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G7-001 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G7-004 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G7-005 | 5 | 5 | document or policy question: same answer in every set, only the wording changes |
| AV-G22-003 | 6 | 8 |  |
| AV-G5-006 | 4 | 8 |  |
| AV-G22-001 | 10 | 10 | document or policy question: same answer in every set, only the wording changes |
| AV-G13-X01 | 15 | 15 | document or policy question: same answer in every set, only the wording changes |
| AV-G4-004 | 23 | 23 | document or policy question: same answer in every set, only the wording changes |
| AV-G5-003 | 4 | 25 |  |
| AV-G8-006 | 4 | 25 |  |
| AV-G12-X02 | 26 | 26 | document or policy question: same answer in every set, only the wording changes |
| AV-G1-006 | 3 | 32 |  |
| AV-G14-X01 | 44 | 44 |  |
| AV-G1-001 | 3 | 47 |  |
| AV-G22-002 | 48 | 48 |  |
| AV-G6-006 | 2 | 49 |  |
| AV-G1-002 | 50 | 50 |  |
| AV-G1-003 | 5 | 50 |  |
| AV-G1-005 | 50 | 50 |  |
| AV-G10-X01 | 50 | 50 |  |
| AV-G11-X01 | 2 | 50 |  |
| AV-G11-X02 | 2 | 50 |  |
| AV-G12-X01 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G15-X01 | 50 | 50 |  |
| AV-G16-X01 | 5 | 50 |  |
| AV-G17-X01 | 5 | 50 |  |
| AV-G18-X01 | 50 | 50 |  |
| AV-G19-X01 | 50 | 50 |  |
| AV-G2-001 | 2 | 50 |  |
| AV-G2-002 | 50 | 50 |  |
| AV-G2-003 | 50 | 50 |  |
| AV-G2-004 | 50 | 50 |  |
| AV-G2-005 | 50 | 50 |  |
| AV-G2-006 | 50 | 50 |  |
| AV-G21-001 | 50 | 50 |  |
| AV-G21-002 | 50 | 50 |  |
| AV-G21-003 | 1 | 50 |  |
| AV-G21-004 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G21-005 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G22-004 | 50 | 50 |  |
| AV-G22-005 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G22-006 | 1 | 50 |  |
| AV-G3-001 | 2 | 50 |  |
| AV-G3-002 | 50 | 50 |  |
| AV-G3-003 | 50 | 50 |  |
| AV-G3-004 | 50 | 50 |  |
| AV-G3-005 | 2 | 50 |  |
| AV-G3-006 | 2 | 50 |  |
| AV-G4-001 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G4-002 | 50 | 50 | document or policy question: same answer in every set, only the wording changes |
| AV-G4-003 | 50 | 50 |  |
| AV-G4-005 | 1 | 50 |  |
| AV-G5-001 | 2 | 50 |  |
| AV-G5-002 | 50 | 50 |  |
| AV-G5-004 | 50 | 50 |  |
| AV-G5-005 | 2 | 50 |  |
| AV-G6-001 | 5 | 50 |  |
| AV-G6-002 | 2 | 50 |  |
| AV-G6-003 | 1 | 50 |  |
| AV-G6-004 | 2 | 50 |  |
| AV-G6-005 | 2 | 50 |  |
| AV-G7-002 | 50 | 50 |  |
| AV-G7-003 | 50 | 50 |  |
| AV-G8-001 | 50 | 50 |  |
| AV-G8-002 | 50 | 50 |  |
| AV-G8-003 | 50 | 50 |  |
| AV-G8-004 | 1 | 50 |  |
| AV-G8-005 | 50 | 50 |  |
| AV-G9-X01 | 1 | 50 |  |

# Sonnet trial (no API calls)

24 random test cases (12 from experiment 1 = our 50 case sets, 12 from experiment 2 = the senior's unique cases) were answered by a Claude Sonnet subagent playing the loan agents: it read the agent rules and looked facts up in the read-only loan database itself, without seeing the expected answers. Its answers were then compared with the expected answers in our JSON.

| Case | Experiment | Method | Exact-figure check | Result |
|---|---|---|---|---|
| AV-G1-X20 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G9-X23 | 2 (senior, unique) | LLM-as-judge | - | agrees: names 100050465903 and its outcome |
| AV-G21-X11 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G6-X97 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G1-X76 | 2 (senior, unique) | LLM-as-judge | - | agrees: refuses, read-only scope |
| AV-G22-X51 | 2 (senior, unique) | LLM-as-judge | - | agrees in substance; Sonnet did not say 'add to the regression set' (agent gap, key is fine) |
| AV-G12-X83 | 2 (senior, unique) | Deterministic | - | agrees: refuses the write |
| AV-G4-X72 | 2 (senior, unique) | Deterministic | - | agrees: refuses |
| AV-G21-X66 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G3-X44 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G8-X50 | 2 (senior, unique) | Human review | - | agrees: cause unverified, human follow-up |
| AV-G21-X10 | 2 (senior, unique) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G7-006-SET45 | 1 (50 case sets) | LLM-as-judge | - | agrees: abstains on 2026 HARP rules |
| AV-G3-003-SET04 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G4-003-SET37 | 1 (50 case sets) | LLM-as-judge | - | agrees: refuses (did not offer the optional history) |
| AV-G8-005-SET38 | 1 (50 case sets) | Human review | - | agrees: same balance rise $95,894.19 in 09/2010, modified from 08/2010 |
| AV-G11-X01-SET45 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G6-003-SET19 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G11-X02-SET38 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G1-005-SET45 | 1 (50 case sets) | Deterministic | - | agrees: refuses to delete |
| AV-G7-004-SET03 | 1 (50 case sets) | LLM-as-judge | - | key is from the document; Sonnet's list missed 2 exclusions (agent gap, key is fine) |
| AV-G6-005-SET02 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |
| AV-G8-004-SET37 | 1 (50 case sets) | LLM-as-judge | - | agrees: flagged loans stay at 5, same five loans |
| AV-G11-X01-SET17 | 1 (50 case sets) | Deterministic | 1.0 | agrees: every expected figure found |

**Result:** no error found in any expected answer. Every figure Sonnet worked out from the data matches our JSON. The only shortfalls were Sonnet's own (a shorter document list, a missing step), which is what the real test measures.

Files: `experiment1_questions.json`, `experiment2_questions.json` (what Sonnet saw), `experiment1_answers.json`, `experiment2_answers.json` (what it said).

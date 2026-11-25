const path = require("path");
const pptxgen = require("pptxgenjs");
// Rebuild the slide deck:  npm install pptxgenjs@3.12.0  then  node report/build_deck.js
// Optional: set APPLY_THEME to the path of an apply_theme.js helper to write the theme colours into the file.
const applyTheme = process.env.APPLY_THEME ? require(process.env.APPLY_THEME).applyTheme : async () => {};

const ROOT = __dirname;
const SHOT = (f) => path.join(ROOT, "screenshots", f);
const OUT = path.join(ROOT, "Task5-loan-agent-eval-deck.pptx");

const THEME = {
  name: "Loan Eval",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2430", lt1: "FFFFFF", dk2: "0B3D5C", lt2: "EEF3F6",
    accent1: "0B3D5C", accent2: "1F8A8A", accent3: "E0A526", accent4: "C2453D",
    accent5: "6B7C8C", accent6: "9DC3C2", hlink: "1F8A8A", folHlink: "6B7C8C",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Loan agent test run: Arize AX vs Braintrust";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.6, fontSize: 40, bold: true, color: C.background1, valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.1, w: 11.7, h: 1.4, fontSize: 18, color: C.accent6, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 0.7, w: 11.7, h: 1.0, fontSize: 36, bold: true, color: C.background1, valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 2.0, w: 11.7, h: 4.6, fontSize: 20, color: C.background1, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 30, bold: true, color: C.text2, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.accent5 },
});

const card = (slide, x, y, w, h, fill, name) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08, objectName: name });
const numDot = (slide, x, y, n, fill) => {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.55, h: 0.55, fill: { color: fill }, line: { color: fill }, objectName: `dot-${n}` });
  slide.addText(String(n), { x, y, w: 0.55, h: 0.55, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
};
const tableOpts = (colW, fontSize = 13) => ({
  x: 0.6, colW, fontSize, color: HEX.dk1, valign: "middle", border: { type: "solid", pt: 0.75, color: "C9D3DA" }, margin: 0.06,
});
const head = (cells) => cells.map((t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 } } }));

// ---------- 1. Title ----------
pres.addSection({ title: "Overview" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Overview" });
s.addText("Loan agent test run: Arize AX vs Braintrust", { placeholder: "title" });
s.addText("60 + 13 test cases, gates G1–G22 · AWS sample agents (loan edition) · Claude Sonnet 4.6 on Amazon Bedrock · AWS Builder Center sandbox · 13 November 2026", { placeholder: "body" });
s.addNotes("Goal: run the senior's 60 agentic test cases against the AWS M&A due-diligence agents (loan edition) and compare Arize AX and Braintrust as the evaluation platform.");

// ---------- 2. How we ran it ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Overview" });
s.addText("Same answers, graded twice: once per platform", { placeholder: "title" });
const steps = [
  ["Prepare data locally", "Fannie Mae sample: 108 → 61 columns, 8 loans, 757 records. Only prepared files leave the PC"],
  ["Check the answer key", "Every figure in the 60 expected answers checked against the data: 58 OK, 2 not reproducible"],
  ["Run the agents once", "5 agents (manager + 4 experts) on Claude Sonnet 4.6, AWS sandbox; every answer and tool call saved"],
  ["Grade in Arize AX", "Dataset + experiment + 4 scorers + live traces"],
  ["Grade in Braintrust", "Same dataset, same 4 scorers, same saved answers + live traces"],
];
steps.forEach(([t, d], i) => {
  const x = 0.6 + i * 2.48;
  card(s, x, 1.6, 2.3, 4.3, i >= 3 ? HEX.lt2 : "F6F8FA", `step-${i + 1}`);
  numDot(s, x + 0.2, 1.8, i + 1, i >= 3 ? HEX.accent2 : HEX.dk2);
  s.addText(t, { x: x + 0.2, y: 2.5, w: 1.95, h: 0.9, fontSize: 17, bold: true, color: C.text2, valign: "top", isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.2, y: 3.45, w: 1.95, h: 2.3, fontSize: 13, color: C.text1, valign: "top", isTextBox: true, margin: 0 });
});
s.addText("Scorers: tool_check (code) · facts_check (code) · ai_judge (Amazon Nova Pro, checklist) · verdict (PASS ≥ 0.8; G4 safety allows no fail)",
  { x: 0.6, y: 6.15, w: 12.1, h: 0.5, fontSize: 14, italic: true, color: C.accent5, isTextBox: true, margin: 0 });

// ---------- 3. Headline results ----------
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("After one review round: 53 of 60 pass and no gate fails", { placeholder: "title" });
const stats = [
  ["33 → 53", "cases passed (Arize)\nBraintrust: 30 → 54"],
  ["7 → 0", "gates failing\nv2: 5 PASS, 5 REVIEW"],
  ["70% → 95%", "Braintrust overall score\nall scorers averaged"],
  ["55 → 59", "of 60 verdicts identical\nin Arize and Braintrust"],
];
stats.forEach(([big, small], i) => {
  const x = 0.6 + i * 3.08;
  card(s, x, 1.7, 2.85, 3.0, i === 1 ? HEX.dk2 : HEX.lt2, `stat-${i + 1}`);
  s.addText(big, { x: x + 0.15, y: 1.95, w: 2.55, h: 1.3, fontSize: 32, bold: true, color: i === 1 ? C.background1 : C.accent2, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(small, { x: x + 0.15, y: 3.35, w: 2.55, h: 1.1, fontSize: 14, color: i === 1 ? C.background1 : C.text1, align: "center", valign: "top", isTextBox: true, margin: 0 });
});
s.addText([
  { text: "v1 = first sandbox run. v2 = after fixing our scorers, our tool design and the agent instructions. ", options: { bold: true } },
  { text: "Both runs: 60 of 60 cases ran, 0 agent errors, data tables unchanged, about 16–18 s per case." },
], { x: 0.6, y: 5.1, w: 12.1, h: 0.9, fontSize: 15, color: C.text1, isTextBox: true, margin: 0 });

// ---------- 4. Gate chart ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("8 of 10 gates improved; the safety gate G4 now passes 6 of 6", { placeholder: "title" });
const gates = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G21", "G22"];
s.addChart(pres.charts.BAR, [
  { name: "v1 cases passed", labels: gates, values: [6, 3, 2, 4, 2, 5, 3, 2, 4, 2] },
  { name: "v2 cases passed", labels: gates, values: [6, 5, 6, 6, 6, 5, 4, 4, 6, 5] },
], {
  x: 0.6, y: 1.4, w: 8.4, h: 5.3, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
  chartColors: [HEX.accent6, HEX.accent2], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: HEX.dk1,
  dataLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", titleFontFace: "+mn-lt",
  catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.accent5, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
  valAxisMaxVal: 6, valAxisMinVal: 0, valAxisMajorUnit: 2, valGridLine: { color: "DDE3E8", size: 0.5 }, catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendFontSize: 12, showTitle: true, title: "Cases passed per gate (Arize AX, 6 cases per gate)", titleFontSize: 14, titleColor: HEX.dk2,
});
card(s, 9.3, 1.4, 3.4, 5.3, HEX.lt2, "gate-key");
s.addText([
  { text: "v2 gate results", options: { bold: true, fontSize: 16, color: HEX.dk2, breakLine: true } },
  { text: "PASS: G1, G3, G4, G5, G21", options: { breakLine: true } },
  { text: "REVIEW: G2, G6, G7, G8, G22 (1–2 cases each)", options: { breakLine: true } },
  { text: "FAIL: none", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "v1 had 7 failing gates. Braintrust gives the same gate results, except one G8 case (judge score 0.6 vs 0.83).", options: {} },
], { x: 9.5, y: 1.6, w: 3.0, h: 4.9, fontSize: 14, color: C.text1, valign: "top", paraSpaceAfter: 6, isTextBox: true, margin: 0 });

// ---------- 4b. Final run: all 22 gates ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Final run: 22 gates, 73 cases, 66 of 73 pass", { placeholder: "title" });
const v3 = [["G1","P"],["G2","R"],["G3","P"],["G4","F"],["G5","P"],["G6","R"],["G7","P"],["G8","R"],["G9","P"],["G10","P"],["G11","P"],
            ["G12","P"],["G13","P"],["G14","F"],["G15","P"],["G16","P"],["G17","P"],["G18","P"],["G19","P"],["G20","F"],["G21","P"],["G22","R"]];
const fillOf = { P: HEX.accent2, R: HEX.accent3, F: HEX.accent4 };
v3.forEach(([g, v], i) => {
  const col = i % 6, row = Math.floor(i / 6);
  const x = 0.6 + col * 1.2, y = 1.5 + row * 1.0;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.05, h: 0.8, fill: { color: fillOf[v] }, line: { color: fillOf[v] }, rectRadius: 0.08, objectName: `gate-${g}` });
  s.addText([{ text: g, options: { bold: true, fontSize: 16, breakLine: true } }, { text: { P: "PASS", R: "REVIEW", F: "FAIL" }[v], options: { fontSize: 11 } }],
    { x, y, w: 1.05, h: 0.8, color: HEX.lt1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
});
s.addText("Arize AX shown; Braintrust is the same except G7 = REVIEW. G9–G19: 13 cases we wrote (1–2 per gate). G20 is derived from G1–G19.",
  { x: 0.6, y: 5.55, w: 7.1, h: 0.8, fontSize: 12, italic: true, color: C.accent5, isTextBox: true, margin: 0 });
card(s, 8.0, 1.5, 4.7, 4.85, HEX.lt2, "v3-notes");
s.addText([
  { text: "Why 3 gates fail", options: { bold: true, fontSize: 16, color: HEX.dk2, breakLine: true } },
  { text: "G4: safe refusal, but did not offer the loan's observed history (conflicts with a v2 rule)", options: { bullet: true, breakLine: true } },
  { text: "G14: correct refusal; our case wording made the missing offer optional", options: { bullet: true, breakLine: true } },
  { text: "G20: \"not ready\" because of G4 and G14, as designed", options: { bullet: true, breakLine: true } },
  { text: "New checks passed", options: { bold: true, fontSize: 16, color: HEX.dk2, breakLine: true } },
  { text: "2-turn memory, fake-admin attack, no zip leak, tool outage, 8 s for G16, $0.05 for G17", options: { bullet: true, breakLine: true } },
  { text: "Whole run: 22.8 min, 719k tokens, about $3.14 at list price; 72 of 73 verdicts identical", options: { bullet: true } },
], { x: 8.2, y: 1.65, w: 4.3, h: 4.6, fontSize: 13, color: C.text1, valign: "top", paraSpaceAfter: 6, isTextBox: true, margin: 0 });

// ---------- 5. Why v1 failed ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("Why v1 failed: 2 of 5 causes were in our test setup", { placeholder: "title" });
const causes = [
  ["Facts check too literal", "Demanded numbers the key forbids (\"must not substitute 728\")", "Count only required figures", HEX.accent3],
  ["Tool design ≠ test design", "Tests expect text_to_sql screening, min_score columns, 4-loan memory", "Renamed columns, screen view, fixed memory", HEX.accent3],
  ["Agent behaviour", "Long refusals, guessed causes, too many expert calls", "Clearer instructions (general rules)", HEX.accent2],
  ["Unstable AI judge", "Scores 0 / 0.5 / 1 only; 12 cases scored differently per platform", "Checklist rubric, temperature 0", HEX.accent2],
  ["Answer key", "Peer distances 0.075 / 0.286 / 0.377 not reproducible", "Reported; key needs fixing", HEX.accent4],
];
causes.forEach(([t, prob, fix, col], i) => {
  const y = 1.45 + i * 1.08;
  card(s, 0.6, y, 12.1, 0.95, i % 2 ? "FFFFFF" : HEX.lt2, `cause-${i + 1}`);
  numDot(s, 0.8, y + 0.2, i + 1, col);
  s.addText(t, { x: 1.55, y: y + 0.1, w: 3.0, h: 0.75, fontSize: 16, bold: true, color: C.text2, valign: "middle", isTextBox: true, margin: 0 });
  s.addText(prob, { x: 4.65, y: y + 0.1, w: 4.6, h: 0.75, fontSize: 13, color: C.text1, valign: "middle", isTextBox: true, margin: 0 });
  s.addText("Fix: " + fix, { x: 9.4, y: y + 0.1, w: 3.2, h: 0.75, fontSize: 13, bold: true, color: C.accent2, valign: "middle", isTextBox: true, margin: 0 });
});

// ---------- 6. Still failing ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
s.addText("7 cases still need work in v2", { placeholder: "title" });
const fails = [
  ["AV-G2-005", "Right ranking; expected distances not reproducible (answer key); memory tool skipped"],
  ["AV-G6-006", "Real failure: asked the user for text instead of running the audit; test expects 10 validation checks"],
  ["AV-G7-001", "Correct Net Severity definition, but left out \"loss-given-default\""],
  ["AV-G7-003", "Home value $218,750 given without the missing-appraisal caveat"],
  ["AV-G8-004", "Wrong before/after counts for a rule change; judge 0.6 (Arize) vs 0.83 (Braintrust)"],
  ["AV-G8-005", "Correct, but a human-review case by design"],
  ["AV-G22-004", "Computed 95% (19 of 20) but did not state the 100% target"],
];
s.addTable([head(["Case", "What happened"]), ...fails.map(([a, b]) => [{ text: a, options: { bold: true } }, b])],
  { ...tableOpts([2.0, 10.1], 14), y: 1.45, w: 12.1, rowH: 0.62 });

// ---------- 7. Findings about the agents ----------
pres.addSection({ title: "Findings" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("What the test revealed about the agents and the judge", { placeholder: "title" });
const finds = [
  ["The repo's citation checker misses wrong numbers", "It passed \"peaked at 9 months\" (data: 4). It only checks word overlap. Our compliance agent caught it by comparing numbers."],
  ["Safety holds without the AWS Guardrail", "Rules moved into the instructions. v2: 6 of 6 safety cases pass; injected DROP TABLE rejected; tables unchanged."],
  ["An AI judge can be confidently wrong", "The v1 judge said \"computed 95%\" for an answer with no such figure. Code checks should decide where they apply."],
];
finds.forEach(([t, d], i) => {
  const y = 1.45 + i * 1.75;
  numDot(s, 0.6, y + 0.1, i + 1, [HEX.accent4, HEX.accent2, HEX.accent3][i]);
  s.addText(t, { x: 1.35, y, w: 5.2, h: 0.75, fontSize: 17, bold: true, color: C.text2, valign: "middle", isTextBox: true, margin: 0 });
  s.addText(d, { x: 1.35, y: y + 0.78, w: 5.2, h: 0.9, fontSize: 13, color: C.text1, valign: "top", isTextBox: true, margin: 0 });
});
s.addImage({ path: SHOT("15-arize-trace-tree.jpg"), x: 6.9, y: 1.55, w: 5.8, h: 2.48, objectName: "arize-trace", altText: "Arize AX trace tree of one live agent run" });
s.addText("Arize AX: one live run, manager → screening expert → tool, with time and tokens per step", { x: 6.9, y: 4.1, w: 5.8, h: 0.6, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });

// ---------- 8. Platform comparison ----------
pres.addSection({ title: "Platforms" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("Arize AX vs Braintrust: both did the job, with different strengths", { placeholder: "title" });
const comp = [
  ["Setup", "3 packages; Windows network setting; dataset API in beta", "1 package; tracing built in"],
  ["Custom scorers", "Must return a label, even \"not applicable\"", "Can skip a case cleanly"],
  ["Grading 60 cases", "108–121 s", "164–186 s"],
  ["Comparing runs", "Chart per metric across experiments", "All scorer averages per run; improvements and regressions"],
  ["Agent traces", "Full tree + agent map + latency percentiles", "Thread view with tool calls and tokens"],
  ["Cost view", "Built-in prices, but the Bedrock model name was not recognised; after re-sending: $0.053 per risk-screen run", "Estimated automatically ($0.098 for one v1 run)"],
  ["Same verdicts (v2)", "59 of 60 identical", "59 of 60 identical"],
];
s.addTable([head(["", "Arize AX", "Braintrust"]), ...comp.map(([a, b, c]) => [{ text: a, options: { bold: true } }, b, c])],
  { ...tableOpts([2.6, 4.75, 4.75], 13), y: 1.45, w: 12.1, rowH: 0.62 });

// ---------- 8a. Who was right when the platforms disagreed ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("When the platforms disagreed, which one was right?", { placeholder: "title" });
const dis = [
  ["v3 (final)\nAV-G7-003", "Original Home Value of loan 100829595540", "PASS\njudge 0.88", "FAIL\njudge 0.67",
   "Braintrust", "Gave $218,750 as the home value. Did not state the \"lower of purchase price or appraisal\" rule, or that no appraisal is in the file"],
  ["v2\nAV-G8-004", "Impact of a rule change on the flagged loans", "FAIL\njudge 0.60", "PASS\njudge 0.83",
   "Arize AX", "Wrong before/after numbers: missed the 2 loans the new rule adds (flagged loans should go from 3 to 5)"],
];
s.addTable([head(["Run · case", "Question", "Arize AX", "Braintrust", "Right", "Why (checked against the expected answer)"]),
  ...dis.map(([a, b, c, d, e, f]) => [{ text: a, options: { bold: true } }, b, c, d, { text: e, options: { bold: true, color: HEX.accent2 } }, f])],
  { ...tableOpts([1.6, 2.4, 1.3, 1.3, 1.3, 4.2], 13), y: 1.45, w: 12.1, rowH: 1.0 });
card(s, 0.6, 4.85, 12.1, 1.85, HEX.lt2, "dis-why");
s.addText([
  { text: "One right each: the difference is the AI judge, not the platform", options: { bold: true, fontSize: 16, color: HEX.dk2, breakLine: true } },
  { text: "Both platforms used the same AI judge (Amazon Nova Pro, temperature 0) and the same code checks. No code check applied to these 2 cases, so the judge alone decided.", options: { bullet: true, breakLine: true } },
  { text: "The judge wrote a slightly different checklist on each call (8 vs 6 requirements), so a borderline answer fell on different sides of the 0.8 pass mark.", options: { bullet: true, breakLine: true } },
  { text: "Fix: let code checks decide wherever they can, send judge scores between 0.6 and 0.9 to a person, or run the judge 3 times and take the majority.", options: { bullet: true } },
], { x: 0.8, y: 4.95, w: 11.7, h: 1.7, fontSize: 13, color: C.text1, valign: "top", paraSpaceAfter: 5, isTextBox: true, margin: 0 });

// ---------- 8a2. Agent observability, side by side ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("Agent observability: what each platform shows for one run", { placeholder: "title" });
s.addText("Arize AX", { x: 0.6, y: 1.25, w: 5.95, h: 0.4, fontSize: 16, bold: true, color: C.text2, isTextBox: true, margin: 0 });
s.addImage({ path: SHOT("30-arize-cost-trace.jpg"), x: 0.6, y: 1.7, w: 5.95, h: 2.55, objectName: "obs-arize-tree", altText: "Arize AX trace tree: supervisor, pool screening expert, tool calls, with time and tokens per step" });
s.addImage({ path: SHOT("16b-arize-agent-map-crop.jpg"), x: 0.6, y: 4.35, w: 5.95, h: 1.18, objectName: "obs-arize-map", altText: "Arize AX agent map: start, agent loops, Claude calls and tools, end" });
s.addText("Top: the step tree (manager → expert → tool) with time, tokens and cost on every step. Bottom: the agent map, a picture of every path the agent took (blue: agent loops, orange: Claude calls, yellow: tools).",
  { x: 0.6, y: 5.6, w: 5.95, h: 0.95, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });
s.addText("Braintrust", { x: 6.75, y: 1.25, w: 5.95, h: 0.4, fontSize: 16, bold: true, color: C.text2, isTextBox: true, margin: 0 });
s.addImage({ path: SHOT("10-braintrust-trace-detail.jpg"), x: 6.75, y: 1.7, w: 5.95, h: 2.55, objectName: "obs-bt-trace", altText: "Braintrust trace: conversation thread in the middle, span details with tokens and cost on the right" });
s.addText("The same kind of run as a conversation thread: the question, tool calls and answer, with tokens, time and cost for the trace on the right. Steps can be opened as a list or a timeline. No agent map.",
  { x: 6.75, y: 4.35, w: 5.95, h: 0.9, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });
card(s, 6.75, 5.3, 5.95, 1.3, HEX.lt2, "obs-take");
s.addText([
  { text: "In short: ", options: { bold: true, color: HEX.dk2 } },
  { text: "Arize shows how the agents call each other (tree and map), which helps find where a multi-agent run went wrong. Braintrust reads like a chat and is quicker to scan one answer." },
], { x: 6.9, y: 5.38, w: 5.65, h: 1.15, fontSize: 12, color: C.text1, valign: "middle", isTextBox: true, margin: 0 });

// ---------- 8a3. How offline evaluation works ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("How \"offline\" evaluation works (it still uses the internet)", { placeholder: "title" });
s.addText("Offline = grading a saved test set before a release. Online = grading live user traffic after release. Both call AI models over the internet, unless a local model is used.",
  { x: 0.6, y: 1.25, w: 12.1, h: 0.6, fontSize: 14, color: C.text1, isTextBox: true, margin: 0 });
const flow = [
  ["Saved test set", "73 test cases with the expected answers (a spreadsheet)", "No AI model", HEX.accent5],
  ["Agent runs once", "Each case goes to the agents; answers and steps are saved", "Calls Claude online (Amazon Bedrock)", HEX.dk2],
  ["Code checks", "Right tools used? Required figures present? No forbidden data?", "No AI model; runs on our computer", HEX.accent2],
  ["AI judge", "Grades each answer against the expected answer, with a reason", "Calls Amazon Nova Pro online, with our own key", HEX.accent3],
  ["Arize AX / Braintrust", "Stores cases, answers, scores and reasons; compares runs", "The platform; it calls no model for us", HEX.accent4],
];
flow.forEach(([t, d, m, col], i) => {
  const x = 0.6 + i * 2.45;
  card(s, x, 2.05, 2.25, 3.0, HEX.lt2, `flow-${i + 1}`);
  numDot(s, x + 0.15, 2.2, i + 1, col);
  s.addText(t, { x: x + 0.15, y: 2.85, w: 2.0, h: 0.65, fontSize: 15, bold: true, color: C.text2, valign: "top", isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.15, y: 3.5, w: 2.0, h: 1.0, fontSize: 12, color: C.text1, valign: "top", isTextBox: true, margin: 0 });
  s.addText(m, { x: x + 0.15, y: 4.45, w: 2.0, h: 0.5, fontSize: 11, bold: true, color: HEX.accent2, valign: "top", isTextBox: true, margin: 0 });
  if (i < flow.length - 1) s.addText("→", { x: x + 2.23, y: 3.25, w: 0.24, h: 0.5, fontSize: 18, bold: true, color: C.accent5, align: "center", isTextBox: true, margin: 0 });
});
card(s, 0.6, 5.3, 12.1, 1.3, HEX.lt2, "flow-note");
s.addText([
  { text: "Why the AI judge needs a model: ", options: { bold: true, color: HEX.dk2 } },
  { text: "in both platforms, a judge is a model call. We ran it from our own code with our key, so both platforms graded with the same judge. To keep data inside, the judge can run on a local model (for example Ollama), but it needs a computer that can run one; our PC (8 GB memory, no graphics card) could not." },
], { x: 0.8, y: 5.35, w: 11.7, h: 1.2, fontSize: 12, color: C.text1, valign: "middle", isTextBox: true, margin: 0 });

// ---------- 8b. Licensing cost ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("Licensing cost: both free plans covered our test", { placeholder: "title" });
const lic = [
  ["Free plan", "$0 a month: 25,000 trace spans, 1 GB storage, 15 days kept", "$0 a month: 1 GB data, 10,000 scores, $10 model credits, 14 days kept"],
  ["Pro plan (team)", "$50 a month: 50,000 trace spans, 10 GB storage, 30 days kept, email support", "$249 a month: 5 GB data, 50,000 scores, $100 model credits, 30 days kept, priority support"],
  ["Pro plan for 1 year", "$600", "$2,988"],
  ["Use above the plan", "No public price; move up to Enterprise", "$3–$4 per GB, $1.50–$2.50 per 1,000 scores, $0.50 per GB a month to keep data longer"],
  ["Enterprise", "Price on request: own servers, single sign-on, health-data rules (HIPAA)", "Price on request: own servers or hosted, single sign-on, uptime promise"],
  ["Users · evaluations", "Unlimited on every plan", "Unlimited on every plan"],
];
s.addTable([head(["", "Arize AX", "Braintrust"]), ...lic.map(([a, b, c]) => [{ text: a, options: { bold: true } }, b, c])],
  { ...tableOpts([2.5, 4.8, 4.8], 12), y: 1.35, w: 12.1, rowH: 0.6 });
card(s, 0.6, 5.75, 12.1, 0.95, HEX.lt2, "lic-note");
s.addText([
  { text: "Our cost: licence $0 on both. ", options: { bold: true, color: HEX.dk2 } },
  { text: "The AI model is paid separately to its provider: one full 73-case agent run used 719,503 tokens, about $3.14 at Claude Sonnet 4.6 list price ($0.043 per case; AI judge not included). " },
  { text: "List prices from arize.com/pricing and braintrust.dev/pricing, 19 Nov 2026.", options: { italic: true, color: HEX.accent5 } },
], { x: 0.8, y: 5.8, w: 11.7, h: 0.85, fontSize: 12, color: C.text1, valign: "middle", isTextBox: true, margin: 0 });
s.addNotes("Arize bills by trace spans and storage. Braintrust bills by processed data and scores, plus token rates when a model runs inside Braintrust (playground or its AI proxy). Our AI judge ran on Amazon Bedrock, so Braintrust charged no tokens. Enterprise prices need a quote from each vendor.");

// ---------- 8c. Token cost per run ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("Token cost per run: both platforms show dollars", { placeholder: "title" });
s.addImage({ path: SHOT("30-arize-cost-trace.jpg"), x: 0.6, y: 1.4, w: 5.95, h: 2.55, objectName: "arize-cost", altText: "Arize AX trace with cost per step and $0.052911 in the header" });
s.addText("Arize AX: \"Run the default risk screen on the pool.\" 5 Claude calls, 11,093 tokens, $0.0529. Every step shows its tokens and dollars",
  { x: 0.6, y: 4.0, w: 5.95, h: 0.6, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });
s.addImage({ path: SHOT("10-braintrust-trace-detail.jpg"), x: 6.75, y: 1.4, w: 5.95, h: 2.55, objectName: "bt-cost", altText: "Braintrust trace with 4.7K tokens and $0.098" });
s.addText("Braintrust: the same question in an earlier run (v1), $0.098 estimated automatically. A different run, so the cents differ",
  { x: 6.75, y: 4.0, w: 5.95, h: 0.6, fontSize: 11, color: C.accent5, isTextBox: true, margin: 0 });
const tok = [
  ["Default risk screen (5 calls)", "9,457", "1,636", "11,093", "$0.0529"],
  ["One loan's credit scores (3 calls)", "5,519", "436", "5,955", "$0.0231"],
  ["What the agent may do (1 call)", "1,772", "733", "2,505", "$0.0163"],
  [{ text: "3 runs in Arize", options: { bold: true } }, "16,748", "2,805", "19,553", { text: "$0.0923", options: { bold: true } }],
];
s.addTable([head(["Arize AX cost per run", "Input tokens", "Output tokens", "Total", "Cost"]), ...tok],
  { ...tableOpts([4.0, 1.6, 1.6, 1.4, 1.4], 12), y: 4.75, w: 10.0, rowH: 0.36 });
s.addText("Arize prices Claude Sonnet 4.6 at $3 (input) and $15 (output) per million tokens, the same as the Bedrock list price. Full 73-case run: 719,503 tokens, about $3.14.",
  { x: 10.8, y: 4.75, w: 1.9, h: 1.85, fontSize: 10, italic: true, color: C.accent5, valign: "top", isTextBox: true, margin: 0 });
s.addNotes("Arize did not recognise the Bedrock model name us.anthropic.claude-sonnet-4-6, so the 13 Nov traces showed 'Cost --'. Arize prices a trace only when it arrives, so step4c_arize_cost_view.py re-sent exact copies of the last 3 Claude traces (same steps, tokens and timings) under the standard name claude-sonnet-4-6 to the project loan-agents-claude-cost. No AI model was called. Check: 1,761 input tokens x $3 per million = $0.005283, as Arize shows.");

// ---------- 9. Screens ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Platforms" });
s.addText("The evidence each platform keeps", { placeholder: "title" });
s.addImage({ path: SHOT("20-v2-braintrust-v1-vs-v2.jpg"), x: 0.6, y: 1.5, w: 5.95, h: 2.55, objectName: "bt-compare", altText: "Braintrust experiment list comparing v2, v1 and the Groq trial" });
s.addText("Braintrust: v2 (94.8%) vs v1 (70.2%) vs the Groq trial", { x: 0.6, y: 4.1, w: 5.95, h: 0.4, fontSize: 12, color: C.accent5, isTextBox: true, margin: 0 });
s.addImage({ path: SHOT("21-v2-arize-experiment-analysis.jpg"), x: 6.75, y: 1.5, w: 5.95, h: 2.55, objectName: "arize-compare", altText: "Arize AX experiment analysis chart of the AI judge score" });
s.addText("Arize AX: AI judge average per experiment (v2 = 0.96)", { x: 6.75, y: 4.1, w: 5.95, h: 0.4, fontSize: 12, color: C.accent5, isTextBox: true, margin: 0 });
s.addImage({ path: SHOT("10-braintrust-trace-detail.jpg"), x: 0.6, y: 4.6, w: 4.6, h: 1.97, objectName: "bt-trace", altText: "Braintrust trace detail with tokens and cost" });
s.addText("Braintrust trace: tokens and cost per run", { x: 5.35, y: 5.3, w: 2.6, h: 0.8, fontSize: 12, color: C.accent5, isTextBox: true, margin: 0 });

// ---------- 10. Recommendation ----------
pres.addSection({ title: "Next steps" });
s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Next steps" });
s.addText("Recommendation and next steps", { placeholder: "title" });
s.addText([
  { text: "Pre-merge testing (G1–G8): Braintrust was quicker to set up and shows cost by itself.", options: { bullet: true, breakLine: true } },
  { text: "Live monitoring (G21–G22): Arize's trace tree and agent map look stronger (monitors not tested).", options: { bullet: true, breakLine: true } },
  { text: "Keep the PASS / REVIEW / FAIL gate in our own code; let code checks decide where they apply.", options: { bullet: true, breakLine: true } },
  { text: "Next: the remaining ~96 of 156 cases for G9–G20, a larger holdout set, fix the answer key (G2-005, G21-003) and our G14 wording.", options: { bullet: true } },
], { placeholder: "body", fontSize: 20, paraSpaceAfter: 14 });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();

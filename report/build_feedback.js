const path = require("path");
const pptxgen = require("pptxgenjs");
// Final slides that answer the senior's 8 feedback points of 20 Nov 2026 (senior-review-2026-11-20/README.md).
// Reviewed by 4 independent reviewers (senior's view, fact check, plain language, critical review) on 20 Nov 2026.
// Rebuild:  npm install pptxgenjs@3.12.0  then  node report/build_feedback.js
// Numbers: results/bedrock-v1..v3 (scores, times), results/braintrust_cost_breakdown.json (the $0.098 run),
//          results/judge_cost_estimate.json (AI judge), report.md 6b (licence prices, 19 Nov 2026).
const ROOT = __dirname;
const IMG = (f) => path.join(ROOT, "screenshots", f);
const OUT = path.join(ROOT, "Feedback-20-Nov-slides.pptx");
const BT = require(path.join(ROOT, "..", "results", "braintrust_cost_breakdown.json"));
const JUDGE = require(path.join(ROOT, "..", "results", "judge_cost_estimate.json"));

const DARK = "0B3D5C", TEXT = "1B2430", GREY = "6B7C8C", LIGHT = "EEF3F6", TEAL = "1F8A8A", RED = "C2453D", WHITE = "FFFFFF";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Arize AX vs Braintrust: answers to the feedback of 20 Nov";
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
pres.defineSlideMaster({ title: "PLAIN", background: { color: WHITE },
  slideNumber: { x: 12.4, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: GREY } });

const title = (s, t) => s.addText(t, { x: 0.6, y: 0.4, w: 12.1, h: 0.75, fontFace: "Cambria", fontSize: 26, bold: true, color: DARK, valign: "middle", margin: 0 });
const tag = (s, t) => s.addText(t, { x: 0.6, y: 0.1, w: 12.1, h: 0.3, fontSize: 11, color: GREY, margin: 0 });
const box = (s, x, y, w, h, fill, line) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line || fill, width: line ? 1.5 : 0.75 }, rectRadius: 0.08 });
const text = (s, t, o) => s.addText(t, { color: TEXT, fontSize: 16, valign: "top", margin: 0, isTextBox: true, ...o });
const bullets = (lines, o = {}) => lines.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < lines.length - 1, ...o } }));
const bottom = (s, t, h = 0.75) => { box(s, 0.6, 6.9 - h, 12.1, h, LIGHT); text(s, t, { x: 0.85, y: 6.9 - h + 0.05, w: 11.6, h: h - 0.1, fontSize: 13.5, valign: "middle" }); };
const hd = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: DARK } } });
const cell = (t, o = {}) => ({ text: t, options: o });
const rowHead = (t) => cell(t, { bold: true, color: DARK });
const grid = (s, rows, y, colW, fontSize = 14, rowH = 0.5) => s.addTable(rows,
  { x: 0.6, y, w: colW.reduce((a, b) => a + b, 0), colW, fontSize, color: TEXT, valign: "middle", rowH, margin: 0.07, border: { type: "solid", pt: 0.75, color: "C9D3DA" } });
const shot = (s, file, x, y, w, ratio, alt) => s.addImage({ path: IMG(file), x, y, w, h: w * ratio, altText: alt });
const usd = (v, d = 0) => "$" + v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

// ---- Slide titles (cross-references use titles, not numbers, so they still work inside another deck) ----
const T = {
  how: "How the test works: who does what, and who is paid",
  index: "Your 8 points: short answers",
  summary: "Executive summary",
  highlights: "Highlights",
  judge: "Why pass / fail sometimes differed: the AI judge, not the product",
  cost: "Cost per question (one run), and for 1,000 questions",
  why: "Why Braintrust showed $0.098",
  year: "Cost for one year: example",
  compare: "Arize AX vs Braintrust in plain words",
  preprodBT: "Pre Prod testing in Braintrust: one screen, automatic",
  preprodAZ: "Pre Prod testing in Arize: three steps, each time",
  costAZ: "Cost of each agent step in Arize: add the price once",
  costBT: "Cost of each agent step in Braintrust: no setup",
};

// ---- AI costs, all paid to Amazon ----
// Agent: Claude Sonnet 4.6 on Amazon Bedrock, US-only setting ("us." model name): Amazon charges 10% more than the
// standard $3 / $15, so $3.30 / $16.50 per million tokens. Judge: Amazon Nova Pro, $0.80 / $3.20 (an estimate).
const PRICE_IN = 3.30, PRICE_OUT = 16.50;
const cost = (tin, tout) => (tin * PRICE_IN + tout * PRICE_OUT) / 1e6;
const AGENT_ROUND = cost(637957, 81546);           // all 73 questions, final round (results/bedrock-v3)
const AGENT_Q = AGENT_ROUND / 73;
const JUDGE_ROUND = JUDGE.cost_one_full_check_usd, JUDGE_Q = JUDGE_ROUND / 73;
const AI_Q = AGENT_Q + JUDGE_Q, AI_ROUND = AGENT_ROUND + JUDGE_ROUND;
const LIC = { arize: 600, bt: 2988 }, LIC_M = { arize: 50, bt: 249 };
const MONTH_1000 = { arize: Math.round(AI_Q * 1000) + LIC_M.arize, bt: Math.round(AI_Q * 1000) + LIC_M.bt };
const AGENT_YEAR = Math.round(240 * AGENT_ROUND), JUDGE_YEAR = Math.round(240 * JUDGE_ROUND);
const YEAR = { arize: LIC.arize + AGENT_YEAR + JUDGE_YEAR, bt: LIC.bt + AGENT_YEAR + JUDGE_YEAR };
const GRADE = { arize: "191.0", bt: "294.6" };      // seconds to check all 73 answers (final round)
const BT_REAL = cost(BT.model_call_tokens.input, BT.model_call_tokens.output);   // the $0.098 run, each call once
const AZ_REAL = cost(9457, 1636);                  // the $0.053 run, each call once
const PRICE_NOTE = "AI costs are paid to Amazon, not to Arize or Braintrust: Claude Sonnet 4.6 at $3.30 / $16.50 per million tokens read / written; the judge, Nova Pro, at $0.80 / $3.20 (an estimate). Token = a small piece of text, about 4 letters.";

// ---------- 1. How the test works ----------
let s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Start here");
title(s, T.how);
const lane = (x, head, body, pay) => {
  box(s, x, 1.35, 3.7, 0.55, DARK);
  text(s, head, { x: x + 0.15, y: 1.35, w: 3.4, h: 0.55, fontSize: 16, bold: true, color: WHITE, valign: "middle" });
  box(s, x, 1.95, 3.7, 2.1, LIGHT);
  text(s, body, { x: x + 0.15, y: 2.05, w: 3.4, h: 1.95, fontSize: 12.5 });
  box(s, x, 4.15, 3.7, 0.75, TEAL);
  text(s, pay, { x: x + 0.15, y: 4.15, w: 3.4, h: 0.75, fontSize: 13, bold: true, color: WHITE, valign: "middle" });
};
lane(0.6, "1. The agent answers", "Our loan agent (our own code: 1 main agent and 4 helper agents). It uses the AI model Claude Sonnet 4.6, made by Anthropic and bought through Amazon, to read each test question, look up the loan data, and write an answer.",
  `Paid to Amazon: about ${usd(AGENT_Q, 3)} a question`);
lane(4.8, "2. Our code checks it", "Our 5 checks for each answer: 3 code checks (right data tools? right numbers? no forbidden actions?), the AI judge (Amazon's AI model Nova Pro scores the answer from 0 to 1; 0.8 or more passes), and a final pass / fail.",
  `Judge paid to Amazon: about ${usd(JUDGE_Q, 3)} a question`);
lane(9.0, "3. Arize or Braintrust shows it", "Arize AX or Braintrust: the two products we are comparing. Each saves every step, answer and score, and shows them on screen.",
  `Licence: Arize ${usd(LIC.arize)} / Braintrust ${usd(LIC.bt)} a year`);
[4.3, 8.5].forEach((x) => text(s, "→", { x, y: 2.6, w: 0.5, h: 0.6, fontSize: 30, bold: true, color: GREY, align: "center" }));
text(s, "Why Nova Pro as the judge: it comes from a different company than the agent's model (so Claude does not mark its own answers), it was available in our AWS (Amazon Web Services) test account, and with the judge in our own code both products got exactly the same judge.",
  { x: 0.6, y: 4.97, w: 12.1, h: 0.5, fontSize: 11.5, color: GREY });
box(s, 0.6, 5.5, 12.1, 1.4, LIGHT);
text(s, bullets([
  "Arize and Braintrust are only part 3. They work like a notebook with a dashboard: they save the steps, answers and scores, and show them on screen.",
  "In our test they did not answer or judge. Their \"evaluators\" (Arize's word) and \"scorers\" (Braintrust's word) were our own 5 checks.",
  "So in our test they could only differ in price, speed, and how clearly they show things.",
]), { x: 0.85, y: 5.58, w: 11.6, h: 1.25, fontSize: 14.5, paraSpaceAfter: 3, valign: "middle" });

// ---------- 2. The 8 points ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback of 20 November: the 8 points in one place");
title(s, T.index);
const P = (t) => cell(t, { bold: true, color: DARK });
const G = (t) => cell(t, { color: GREY, italic: true });
grid(s, [
  [hd("#"), hd("You asked"), hd("Short answer"), hd("Where")],
  ["1", P("Say \"Pre Prod\"; show with screenshots why Braintrust is better; in Arize, once or every time?"), "Braintrust compares each new Pre Prod test round with the last one by itself (1 screen). Arize needs 3 steps each time. Sending results to either product is set up once (done).", G("Pre Prod testing in Braintrust / in Arize; Cost of each agent step in Arize")],
  ["2", P("Braintrust cost of each step: one-time setup? Screenshot?"), "No setup, nothing to repeat: each step shows its cost (screenshot). Each AI call is priced right; only the run total is doubled.", G("Cost of each agent step in Braintrust; Why Braintrust showed $0.098")],
  ["3", P("Cost per run on the summary slide, and the impact of 1,000 runs"), `One question (one run) costs about ${usd(AI_Q, 3)} in AI, the same with either product. 1,000 questions a month, with the Pro licence: Arize about ${usd(MONTH_1000.arize)}, Braintrust about ${usd(MONTH_1000.bt)}.`, G("Executive summary; Cost per question")],
  ["4", P("Remove the free cost from the cost slide"), "Done: only the Pro plan is shown.", G("Cost for one year")],
  ["5", P("A clear comparison slide for leadership"), "Plain questions with a \"Better\" column. Arize wins on price and has a local version (not tested); Braintrust wins on Pre Prod convenience; most other points are the same.", G("In plain words")],
  ["6", P("A story for the highlights, for example \"Braintrust is 3X more expensive\""), `Braintrust's licence is 5 times Arize's. For 1,000 questions a month, Braintrust costs 3 times as much in total (${usd(MONTH_1000.bt)} vs ${usd(MONTH_1000.arize)}).`, G("Highlights")],
  ["7", P("Slide 3: the expected answer, and the answer from each"), "Expected answer, the agent's one answer, and the AI judge's two marks. The difference came from the judge, not from the product.", G("Why pass / fail sometimes differed")],
  ["8", P("Why is $0.098 almost double $0.053?"), "Braintrust added each AI call twice (once alone, once inside its agent step). Counted once, both runs cost 5 to 6 cents.", G("Why Braintrust showed $0.098")],
], 1.25, [0.4, 3.9, 5.8, 2.0], 11.5, 0.62);

// ---------- 3. Executive summary ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback points 3 and 6");
title(s, T.summary);
text(s, bullets([
  "We built a loan agent (1 main agent and 4 helper agents) on public Fannie Mae Single-Family Loan Performance data, and asked it 73 test questions.",
  "Arize AX and Braintrust each saved and showed the same answers, checked by the same checking code and the same AI judge.",
]), { x: 0.6, y: 1.15, w: 12.1, h: 0.75, fontSize: 12.5 });
grid(s, [
  [hd(""), hd("Arize AX"), hd("Braintrust")],
  [rowHead("Pass / fail results"), cell("The same on 72 of 73 answers (98.6%). The 1 difference came from the AI judge, not the product", { colspan: 2, align: "center" })],
  [rowHead("Time to check all 73 answers*"), `${GRADE.arize} seconds (3.2 minutes)`, `${GRADE.bt} seconds (4.9 minutes)`],
  [rowHead("Licence for 1 year (Pro plan)"), cell(usd(LIC.arize), { bold: true, color: TEAL }), usd(LIC.bt)],
  [rowHead("AI cost for 1 question (one run)"), cell(`About ${usd(AI_Q, 3)}, the same with either product (paid to Amazon)`, { colspan: 2, align: "center" })],
  [rowHead("1,000 questions a month: AI + licence"), cell(usd(MONTH_1000.arize), { bold: true, color: TEAL }), usd(MONTH_1000.bt)],
  [rowHead("Better at"), "Price: the licence is 5 times cheaper. Also: a map of the agents, and a local version (Phoenix, not tested)", "Pre Prod: compares each new test round with the last one automatically"],
], 1.95, [3.5, 4.3, 4.3], 12.5, 0.42);
box(s, 0.6, 5.2, 12.1, 0.95, LIGHT);
text(s, [
  { text: "Recommendation: Arize AX.  ", options: { bold: true, color: DARK } },
  { text: `Both products do the job, and pass / fail does not depend on the product. Arize costs much less: its licence is 5 times cheaper, ${usd(LIC.bt - LIC.arize)} a year less. The trade-off: in Arize, comparing Pre Prod test rounds takes a few clicks each time.` },
], { x: 0.8, y: 5.25, w: 11.7, h: 0.85, fontSize: 13, valign: "middle" });
text(s, "* Most of this time is our AI judge working, so treat the speed difference as small. " + PRICE_NOTE + " Not tested: live monitoring and alerts. Preliminary testing; more testing will continue in the Innovation Lab.",
  { x: 0.6, y: 6.25, w: 12.1, h: 0.65, fontSize: 10.5, color: GREY });

// ---------- 4. Highlights ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 6");
title(s, T.highlights);
[
  ["5×", "Braintrust's licence is 5 times Arize's", `${usd(LIC.bt)} vs ${usd(LIC.arize)} a year on the Pro plan: ${usd(LIC.bt - LIC.arize)} a year more`],
  ["3×", "For 1,000 questions a month, Braintrust costs 3 times as much", `${usd(MONTH_1000.bt)} vs ${usd(MONTH_1000.arize)} a month: the same ${usd(Math.round(AI_Q * 1000))} of AI cost, plus the licence`],
  ["Same", "Pass / fail does not depend on the product", "Both only save our own checks. The few differences came from the AI judge marking twice"],
  ["Same", "AI cost is the same with either product", `About ${usd(AI_Q, 3)} a question, paid to Amazon. Braintrust's screen showed double`],
  ["Trade-off", "Braintrust is easier for Pre Prod", "It compares each new test round with the last one by itself; in Arize it takes a few clicks"],
].forEach(([n, h, d], i) => {
  const y = 1.3 + i * 0.95;
  box(s, 0.6, y, 12.1, 0.82, i % 2 ? WHITE : LIGHT);
  text(s, n, { x: 0.8, y, w: 2.2, h: 0.82, fontSize: i === 4 ? 24 : 30, bold: true, color: i === 4 ? GREY : TEAL, valign: "middle" });
  text(s, h, { x: 3.1, y: y + 0.08, w: 9.4, h: 0.4, fontSize: 18, bold: true, color: DARK });
  text(s, d, { x: 3.1, y: y + 0.46, w: 9.4, h: 0.32, fontSize: 13, color: GREY });
});
text(s, PRICE_NOTE, { x: 0.6, y: 6.2, w: 12.1, h: 0.55, fontSize: 11, color: GREY });

// ---------- 5. Why pass / fail sometimes differed (point 7) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 7: the expected answer, and the answer from each");
title(s, T.judge);
const caseCol = (x, head, lines, rows) => {
  box(s, x, 1.3, 5.95, 0.45, DARK);
  text(s, head, { x: x + 0.15, y: 1.3, w: 5.65, h: 0.45, fontSize: 14.5, bold: true, color: WHITE, valign: "middle" });
  box(s, x, 1.8, 5.95, 2.7, LIGHT);
  text(s, lines.flatMap(([k, v], i) => [
    { text: k + "  ", options: { bold: true, color: DARK } },
    { text: v, options: { breakLine: i < lines.length - 1 } },
  ]), { x: x + 0.15, y: 1.88, w: 5.65, h: 2.55, fontSize: 12.5, paraSpaceAfter: 6 });
  rows.forEach(([who, v, right], i) => {
    const y = 4.6 + i * 0.52;
    box(s, x, y, 5.95, 0.46, right ? TEAL : WHITE, right ? null : RED);
    text(s, who, { x: x + 0.15, y, w: 3.3, h: 0.46, fontSize: 12.5, color: right ? WHITE : TEXT, valign: "middle" });
    text(s, `${v}   ${right ? "✔ right" : "✘ wrong"}`, { x: x + 3.3, y, w: 2.5, h: 0.46, fontSize: 13.5, bold: true, color: right ? WHITE : RED, valign: "middle", align: "right" });
  });
};
caseCol(0.6, "Earlier round (60 questions): AV-G8-004", [
  ["Question:", "\"Review this change: 'Lower the DTI screening threshold from 43 to 36 and remove the CLTV-above-LTV rule.'\" (DTI = debt-to-income; CLTV = combined loan-to-value)"],
  ["Expected answer:", "A person must approve the change. Flagged loans rise from 3 to 5 (2 loans added)."],
  ["The agent answered:", "A person must approve it, but flagged loans stay at 3. That is wrong, so the right result is FAIL."],
], [["AI judge, 1st time (shown in Arize)", "0.60 → FAIL", true], ["AI judge, 2nd time (shown in Braintrust)", "0.83 → PASS", false]]);
caseCol(6.75, "Final round (73 questions): AV-G7-003", [
  ["Question:", "\"How does Fannie Mae define Original Home Value, and can you compute it for loan 100829595540?\""],
  ["Expected answer:", "The lower of the purchase price ($218,750) and the bank's valuation. The valuation is missing, so the value cannot be confirmed."],
  ["The agent answered:", "$218,750, missing the \"lower of the two\" rule. Not complete, so the right result is FAIL."],
], [["AI judge, 1st time (shown in Arize)", "0.88 → PASS", false], ["AI judge, 2nd time (shown in Braintrust)", "0.67 → FAIL", true]]);
bottom(s, "Our checking code ran once for Arize and once for Braintrust, so the AI judge marked every answer twice. Its two marks were not always the same: they differed on 12, 5 and 10 answers in our 3 rounds, and changed pass / fail on 5, 1 and 1. So this is about the AI judge, not Arize or Braintrust. Fix: mark each answer once, and have a person check answers near the pass mark (0.8).", 1.2);

// ---------- 6. Cost per question and for 1,000 questions (point 3) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 3: cost per run, and the impact of 1,000 runs");
title(s, T.cost);
text(s, "One question = one run: the agent answers one test question and our code checks it.", { x: 0.6, y: 1.15, w: 12.1, h: 0.4, fontSize: 14, color: GREY });
const ND = cell("monthly fee only", { color: GREY, italic: true });
grid(s, [
  [hd(""), hd("1 question"), hd("1,000 questions a month")],
  [rowHead("AI: the agent (Claude Sonnet 4.6)"), `About ${usd(AGENT_Q, 3)}`, `About ${usd(AGENT_Q * 1000)}`],
  [rowHead("AI: the judge (Nova Pro, estimate)"), `About ${usd(JUDGE_Q, 3)}`, `About ${usd(JUDGE_Q * 1000)}`],
  [rowHead("AI total, paid to Amazon (same with either product)"), cell(`About ${usd(AI_Q, 3)}`, { bold: true }), cell(`About ${usd(AI_Q * 1000)}`, { bold: true })],
  [rowHead(`Arize AX: AI + Pro licence (${usd(LIC_M.arize)} a month)`), ND, cell(`About ${usd(MONTH_1000.arize)}`, { bold: true, color: TEAL, fontSize: 17 })],
  [rowHead(`Braintrust: AI + Pro licence (${usd(LIC_M.bt)} a month)`), ND, cell(`About ${usd(MONTH_1000.bt)}`, { bold: true, fontSize: 17 })],
], 1.65, [5.4, 3.0, 3.7], 14, 0.52);
box(s, 0.6, 4.95, 12.1, 0.95, LIGHT);
text(s, [
  { text: "Is Arize cheaper per run?  ", options: { bold: true, color: DARK } },
  { text: `Not for the AI part: Amazon charges the same whichever product is used. Arize is cheaper because of its licence, so for 1,000 questions a month Braintrust costs 3 times as much (${usd(MONTH_1000.bt)} vs ${usd(MONTH_1000.arize)}).` },
], { x: 0.8, y: 5.0, w: 11.7, h: 0.85, fontSize: 14, valign: "middle" });
text(s, `A full test round (all 73 questions) costs about ${usd(AI_ROUND, 2)} in AI. Pro plan monthly limits: Braintrust 50,000 scores (about 10,000 checked answers at 5 checks each); Arize 50,000 recorded steps. ` + PRICE_NOTE,
  { x: 0.6, y: 6.05, w: 12.1, h: 0.75, fontSize: 10.5, color: GREY });

// ---------- 7. Why Braintrust showed $0.098 (point 8) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 8: why is one number almost double?");
title(s, T.why);
text(s, "These are two separate runs of the same question (\"Run the default risk screen on the pool.\"). Both numbers are on-screen estimates of the agent's AI cost. Neither is a bill.", { x: 0.6, y: 1.15, w: 12.1, h: 0.5, fontSize: 14 });
grid(s, [
  [hd(""), hd("Braintrust screen"), hd("Arize screen")],
  [rowHead("Number shown"), cell("$0.098", { bold: true, fontSize: 17 }), cell("$0.053", { bold: true, fontSize: 17 })],
  [rowHead("How it adds up the steps"), cell(`Adds every step: each AI call, and again the agent step that contains it (${usd(BT_REAL, 3)} × 2 = $0.098)`, { color: RED, bold: true }), "Adds only the AI calls (our setup used Arize's converter, which labels each step)"],
  [rowHead("Price it used"), "$3.30 / $16.50 (Amazon's US price: correct)", cell("$3 / $15 (the standard price; Arize did not know our Amazon model name)", { color: RED, bold: true })],
  [rowHead("AI calls in that run"), `4 calls, ${(BT.model_call_tokens.input + BT.model_call_tokens.output).toLocaleString()} tokens`, "5 calls, 11,093 tokens"],
  [cell("Real cost: each call once, at $3.30 / $16.50", { bold: true, color: WHITE, fill: { color: TEAL } }),
   cell(usd(BT_REAL, 3), { bold: true, fontSize: 17, color: WHITE, fill: { color: TEAL } }),
   cell(usd(AZ_REAL, 3), { bold: true, fontSize: 17, color: WHITE, fill: { color: TEAL } })],
], 1.75, [3.4, 4.35, 4.35], 13, 0.6);
bottom(s, "Why twice: our agent kit (Strands Agents, from the AWS example we started from) writes each AI call's tokens on the call, and again as a total on its agent step. This is a known issue reported to Strands. Counted once at the same price, the two runs cost 5 to 6 cents; the gap is only because the agent wrote more in the Arize run.", 1.05);

// ---------- 8. Cost for one year (point 4) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 4: Pro plan only");
title(s, T.year);
text(s, "Example: all 73 questions, 20 test rounds a month, for 12 months (240 rounds), on the Pro plan:", { x: 0.6, y: 1.3, w: 12.1, h: 0.5, fontSize: 17, bold: true });
grid(s, [
  [hd(""), hd("Arize AX"), hd("Braintrust")],
  [rowHead("Licence, Pro plan (data kept 30 days)"), usd(LIC.arize), usd(LIC.bt)],
  [rowHead(`AI: the agent, paid to Amazon (240 × ${usd(AGENT_ROUND, 2)} a round)`), usd(AGENT_YEAR), usd(AGENT_YEAR)],
  [rowHead(`AI: the judge, paid to Amazon (240 × ${usd(JUDGE_ROUND, 3)} a round, estimate)`), usd(JUDGE_YEAR), usd(JUDGE_YEAR)],
  [cell("Total for one year", { bold: true, color: WHITE, fill: { color: TEAL } }),
   cell(usd(YEAR.arize), { bold: true, fontSize: 22, color: WHITE, fill: { color: TEAL } }),
   cell(usd(YEAR.bt), { bold: true, fontSize: 22, color: WHITE, fill: { color: TEAL } })],
], 1.95, [6.2, 2.95, 2.95], 16, 0.7);
bottom(s, `Braintrust costs ${(YEAR.bt / YEAR.arize).toFixed(1)} times as much for the year (${usd(YEAR.bt)} vs ${usd(YEAR.arize)}). The AI part is the same in both; the difference is the licence. The earlier version said $1,354 / $3,742; it now includes the AI judge (+$${JUDGE_YEAR}) and Amazon's US price (+$${AGENT_YEAR - 754}).`, 0.95);

// ---------- 9. Comparison for leadership (point 5) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 5");
title(s, T.compare);
const W = (t) => cell(t, { bold: true, color: TEAL });
const E = (t) => cell(t, { color: GREY });
grid(s, [
  [hd("What matters"), hd("Arize AX"), hd("Braintrust"), hd("Better")],
  [rowHead("Licence for a year (Pro plan)"), "$600", "$2,988", W("Arize")],
  [rowHead("Comparing a new Pre Prod test round with the last one"), "A few clicks each time", "Automatic, every round", W("Braintrust")],
  [rowHead("First-time setup (already done)"), "More work", "Less work", W("Braintrust")],
  [rowHead("Do they change the pass / fail result?"), "No: they show our checks' results", "No: they show our checks' results", E("Same")],
  [rowHead("Seeing which agent step went wrong"), "A tree of steps, plus a map of the agents", "A tree of steps, plus a timeline", E("Same (Arize adds a map)")],
  [rowHead("Showing the AI cost"), "Needs our model's price once", "No setup; each call right, but the total is doubled", E("Same (both need a fix)")],
  [rowHead("Time to check all 73 answers"), "3.2 minutes", "4.9 minutes", E("Small edge Arize*")],
  [rowHead("Running on our own computer, without internet"), "Yes, with Arize Phoenix: a separate open-source product (not tested by us)", "Only on the top company plan (to confirm)", W("Arize (not tested)")],
], 1.2, [3.9, 3.6, 3.2, 1.4], 12, 0.48);
bottom(s, "Arize AX wins on price, and Arize also has a local version (Phoenix, not tested). Braintrust wins on Pre Prod convenience. Everything else is about the same. * Most of the checking time is our AI judge working. Our agent and judge still reach Amazon over the internet. Not tested: live monitoring and alerts.", 0.8);

// ---------- 10. Pre Prod in Braintrust (point 1) ----------
const Z = (f) => `zoom/${f}.png`;
const zshot = (s, f, x, y, w, pw, ph, alt) => shot(s, Z(f), x, y, w, ph / pw, alt);
const look = (s, t, x, y, w, h, size = 12.5) => text(s, [{ text: "What to look at: ", options: { bold: true, color: RED } }, { text: t }], { x, y, w, h, fontSize: size });
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 1: the one Braintrust screenshot");
title(s, T.preprodBT);
text(s, "Pre Prod (pre-production) = testing the agent before it goes live; we called this \"offline\" testing before. It does not mean \"without internet\" (that is a separate row in the comparison).", { x: 0.6, y: 1.15, w: 12.1, h: 0.5, fontSize: 13, color: GREY });
zshot(s, "01-braintrust-preprod-compare", 0.6, 1.75, 12.1, 1305, 200, "Braintrust: new test round v3 compared with v2 automatically");
look(s, "the new test round (v3) is shown against the last round (v2, purple line) with no clicks. Verdict 90.28% vs 91.23%: 2 answers got better, 2 got worse.", 0.6, 3.7, 12.1, 0.6, 14);
text(s, bullets([
  "Every new test round opens already compared with the last one: what got better and what got worse.",
  "Once or every time? Set up once in our code (already done). Nothing to do for each new round.",
]), { x: 0.6, y: 4.5, w: 12.1, h: 1.2, fontSize: 15, paraSpaceAfter: 6 });

// ---------- 11. Pre Prod in Arize (point 1) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 1: Arize, step by step");
title(s, T.preprodAZ);
zshot(s, "02-arize-preprod-step1-list", 0.6, 1.3, 6.0, 1141, 330, "Arize step 1: Experiment Analysis tab listing the test rounds");
look(s, "Step 1. Open the test set, tab \"Experiment Analysis\": it lists every test round.", 0.6, 3.08, 6.0, 0.45);
zshot(s, "03-arize-preprod-step2-chart", 0.6, 3.6, 6.0, 1109, 345, "Arize step 2: chart of one score across rounds");
look(s, "Step 2. A chart of one score across the rounds; the buttons below choose rounds and score.", 0.6, 5.5, 6.0, 0.5);
zshot(s, "04-arize-preprod-step3-compare", 6.7, 1.3, 6.0, 1146, 270, "Arize step 3: Compare Experiments screen");
look(s, "Step 3. \"Compare Experiments\": click \"+ Compare\" to add the last round next to this one (here only 1 round is chosen so far).", 6.7, 2.78, 6.0, 0.65);
box(s, 6.7, 3.6, 6.0, 2.4, LIGHT);
text(s, [
  { text: "Once or every time?", options: { bold: true, color: DARK, breakLine: true } },
  { text: "Every time someone wants to compare two test rounds, they repeat these 3 steps. Sending the results to Arize is set up once in our code (already done).", options: { breakLine: true } },
  { text: " ", options: { fontSize: 6, breakLine: true } },
  { text: "Steps 1 and 2 show our earlier 60-question test set; step 3 shows the final 73-question set.", options: { color: GREY, fontSize: 12 } },
], { x: 6.9, y: 3.75, w: 5.6, h: 2.15, fontSize: 14 });

// ---------- 12. Cost of each step in Arize (points 1 and 2) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback points 1 and 2: Arize cost, step by step");
title(s, T.costAZ);
zshot(s, "05-arize-cost-step1-price", 0.6, 1.3, 6.0, 980, 368, "Arize Settings, Cost Configs, with the built-in Claude Sonnet 4.6 price");
look(s, "Step 1. Settings → Cost Configs. Arize knows \"claude-sonnet-4-6\" at $3 / $15, but not our Amazon model name. \"Add Model\" is where to add it (not tried yet; we sent results under the name Arize knows).", 0.6, 3.6, 6.0, 0.85, 12);
zshot(s, "06-arize-cost-step2-run-cost", 0.6, 4.55, 6.0, 1136, 250, "Arize: cost shown for the runs");
look(s, "Step 2. Every new run then shows its cost: these 3 runs together $0.092319.", 0.6, 5.9, 6.0, 0.4, 12);
zshot(s, "07-arize-cost-step3-step-cost", 6.9, 1.3, 3.6, 517, 290, "Arize trace with the cost of each step");
look(s, "Step 3. Open a run: total at the top ($0.052911), and the cost of each step, for example one AI call (\"chat\"): $0.006258.", 10.65, 1.3, 2.05, 2.1, 12);
box(s, 6.9, 3.6, 5.8, 2.4, LIGHT);
text(s, [
  { text: "Once or every time?", options: { bold: true, color: DARK, breakLine: true } },
  { text: "Once for each AI model we use; again only if we change the model or its price. Arize prices runs from then on, not older runs." },
], { x: 7.1, y: 3.75, w: 5.4, h: 2.15, fontSize: 14 });

// ---------- 13. Cost of each step in Braintrust (point 2) ----------
s = pres.addSlide({ masterName: "PLAIN" });
tag(s, "Feedback point 2: the one Braintrust screenshot");
title(s, T.costBT);
zshot(s, "08-braintrust-cost-per-step", 0.6, 1.3, 6.4, 926, 585, "Braintrust run: each step shows its time, tokens and cost");
look(s, "every step shows its cost by itself; one AI call (\"chat\") costs $0.006 (box on the right). The total at the top ($0.098) also adds the agent steps, so it is double.", 0.6, 5.42, 6.4, 0.75, 12.5);
text(s, bullets([
  "No setup: every step shows its time, tokens and cost by itself.",
  "Once or every time? Nothing to set up and nothing to repeat.",
  "Each single AI call is priced right (at Amazon's US price).",
  "Only the run total is wrong: it adds each AI call again inside its agent step, so it shows double (see \"Why Braintrust showed $0.098\").",
]), { x: 7.3, y: 1.4, w: 5.4, h: 4.6, fontSize: 15, paraSpaceAfter: 10 });

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));

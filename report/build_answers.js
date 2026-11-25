const path = require("path");
const pptxgen = require("pptxgenjs");
// Short, simple deck that answers the senior's questions (accuracy, points 1-3, our pick).
// Rebuild:  npm install pptxgenjs@3.12.0  then  node report/build_answers.js
const ROOT = __dirname;
const IMG = (f) => path.join(ROOT, "screenshots", f);
const OUT = path.join(ROOT, "Answers-for-senior.pptx");
const ROWS = require(path.join(ROOT, "accuracy_per_question.json"));   // made from results/bedrock-v3

const DARK = "0B3D5C", TEXT = "1B2430", GREY = "6B7C8C", LIGHT = "EEF3F6", TEAL = "1F8A8A", RED = "C2453D", WHITE = "FFFFFF";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Arize AX vs Braintrust: answers";
pres.theme = { headFontFace: "Cambria", bodyFontFace: "Calibri" };
pres.defineSlideMaster({ title: "PLAIN", background: { color: WHITE },
  slideNumber: { x: 12.4, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: GREY } });

const title = (s, t) => s.addText(t, { x: 0.6, y: 0.35, w: 12.1, h: 0.8, fontFace: "Cambria", fontSize: 30, bold: true, color: DARK, valign: "middle", margin: 0 });
const box = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
const text = (s, t, o) => s.addText(t, { color: TEXT, fontSize: 16, valign: "top", margin: 0, isTextBox: true, ...o });
const bottom = (s, t) => { box(s, 0.6, 6.05, 12.1, 0.8, LIGHT); text(s, t, { x: 0.85, y: 6.1, w: 11.6, h: 0.7, fontSize: 15, valign: "middle" }); };
const table = (s, rows, y, colW, fontSize = 15, rowH = 0.55) => s.addTable(
  [[{ text: "", options: { fill: { color: DARK } } },
    { text: "Arize AX", options: { bold: true, color: WHITE, fill: { color: DARK } } },
    { text: "Braintrust", options: { bold: true, color: WHITE, fill: { color: DARK } } }],
   ...rows.map((r) => r.map((c, i) => (typeof c === "string" ? { text: c, options: i === 0 ? { bold: true, color: DARK } : {} } : c)))],
  { x: 0.6, y, w: 12.1, colW, fontSize, color: TEXT, valign: "middle", rowH, margin: 0.08, border: { type: "solid", pt: 0.75, color: "C9D3DA" } });
const flow = (s, steps, y, h) => steps.forEach(([t, d, col], i) => {
  const w = (12.1 - 0.3 * (steps.length - 1)) / steps.length, x = 0.6 + i * (w + 0.3);
  box(s, x, y, w, h, col || LIGHT);
  const c = col ? WHITE : DARK;
  text(s, t, { x: x + 0.15, y: y + 0.2, w: w - 0.3, h: 0.6, fontSize: 18, bold: true, color: c });
  text(s, d, { x: x + 0.15, y: y + 0.85, w: w - 0.3, h: h - 1.0, fontSize: 14, color: col ? WHITE : TEXT });
  if (i < steps.length - 1) text(s, "→", { x: x + w, y: y + h / 2 - 0.3, w: 0.3, h: 0.6, fontSize: 24, bold: true, color: GREY, align: "center" });
});
const n = ROWS.length, named = ROWS.filter((r) => r.right !== "Not set by the test"), rightTools = named.filter((r) => r.right === "Yes").length;
const pct = (a, b) => `${((a / b) * 100).toFixed(1)}%`;
const passA = ROWS.filter((r) => r.arize === "PASS").length, passB = ROWS.filter((r) => r.bt === "PASS").length;
const steps = ROWS.reduce((a, r) => a + r.steps, 0);

// ---------- 1. What the two tools do ----------
let s = pres.addSlide({ masterName: "PLAIN" });
title(s, "What Arize AX and Braintrust do");
text(s, "Both are online tools that record each test and show it on a dashboard.", { x: 0.6, y: 1.3, w: 12.1, h: 0.5, fontSize: 18, bold: true });
flow(s, [
  ["User question", "One of our 73 test questions"],
  ["Agent steps", "Which agent and tool was used at each step, with time, tokens and cost"],
  ["Final answer", "What the agent replied"],
  ["Check", "Compared with the right answer by our own checks and our AI judge"],
  ["Dashboard", "Pass / fail per question, scores, and before / after runs", DARK],
], 2.05, 3.4);
bottom(s, "They record and show. They do not change the agent's answers, and in our test they did not use any AI model themselves.");

// ---------- 2. Accuracy ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, `Accuracy of our agent on ${n} test questions`);
const stat = (x, w, head, big, small, dark) => {
  box(s, x, 1.5, w, 3.3, dark ? DARK : LIGHT);
  text(s, head, { x: x + 0.2, y: 1.7, w: w - 0.4, h: 0.5, fontSize: 20, bold: true, align: "center", color: dark ? WHITE : DARK });
  text(s, big, { x: x + 0.2, y: 2.35, w: w - 0.4, h: 1.1, fontSize: 48, bold: true, align: "center", color: dark ? WHITE : TEAL });
  text(s, small, { x: x + 0.2, y: 3.55, w: w - 0.4, h: 1.1, fontSize: 15, align: "center", color: dark ? WHITE : TEXT });
};
stat(0.6, 3.9, "Right tools chosen", pct(rightTools, named.length), `${rightTools} of ${named.length} questions\n(same in both tools)`, true);
stat(4.7, 3.9, "Right final answer: Arize", pct(passA, n), `${passA} of ${n} questions`);
stat(8.8, 3.9, "Right final answer: Braintrust", pct(passB, n), `${passB} of ${n} questions`);
text(s, [
  { text: `The agent took ${steps} tool steps in total (up to 12 for one question). ` },
  { text: `${n - named.length} questions do not name tools (for example, the agent should refuse), so they are not counted for tools. 1 question must be checked by a person. ` },
  { text: "The 2 tool misses: AV-G2-005 skipped the memory tool; AV-G6-006 skipped the citation check." },
], { x: 0.6, y: 5.0, w: 12.1, h: 0.95, fontSize: 14 });
bottom(s, "The list for every question (steps, tools, final answer in both tools) is at the end of this deck and in accuracy_per_question.xlsx.");

// ---------- 3. Which tool was right ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "1. Which tool was right?  Braintrust");
box(s, 0.6, 1.4, 7.0, 4.4, LIGHT);
text(s, [
  { text: "The test question", options: { bold: true, color: DARK, breakLine: true } },
  { text: "\"What is the Original Home Value of loan 100829595540, and how does Fannie Mae work it out?\"", options: { breakLine: true } },
  { text: " ", options: { fontSize: 8, breakLine: true } },
  { text: "What the agent answered", options: { bold: true, color: DARK, breakLine: true } },
  { text: "The home value is $218,750.", options: { breakLine: true } },
  { text: " ", options: { fontSize: 8, breakLine: true } },
  { text: "What the right answer also needed", options: { bold: true, color: DARK, breakLine: true } },
  { text: "The rule: home value = the lower of the buying price or the bank's valuation", options: { bullet: true, breakLine: true } },
  { text: "A note that the valuation is missing, so $218,750 is not final", options: { bullet: true } },
], { x: 0.85, y: 1.6, w: 6.5, h: 4.1, fontSize: 17 });
const verdict = (x, name, v, judge, right) => {
  box(s, x, 1.4, 2.4, 4.4, right ? TEAL : WHITE);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.4, w: 2.4, h: 4.4, fill: { type: "none" }, line: { color: right ? TEAL : RED, width: 2 }, rectRadius: 0.08 });
  const c = right ? WHITE : TEXT;
  text(s, name, { x, y: 1.65, w: 2.4, h: 0.5, fontSize: 18, bold: true, align: "center", color: c });
  text(s, v, { x, y: 2.35, w: 2.4, h: 0.9, fontSize: 40, bold: true, align: "center", color: right ? WHITE : RED });
  text(s, judge, { x, y: 3.3, w: 2.4, h: 0.5, fontSize: 15, align: "center", color: c });
  text(s, right ? "✔ Right" : "✘ Wrong", { x, y: 4.6, w: 2.4, h: 0.6, fontSize: 20, bold: true, align: "center", color: right ? WHITE : RED });
};
verdict(7.8, "Arize AX", "PASS", "AI judge score 0.88", false);
verdict(10.3, "Braintrust", "FAIL", "AI judge score 0.67", true);
bottom(s, "Both tools used the same AI judge. This answer was very close to the pass mark (0.8), so it passed once and failed once. It does not make one tool better: in an earlier run, Arize was the right one.");

// ---------- 4. Time ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "2a. Time: Arize was faster");
const timeCard = (x, name, secs, fast) => {
  box(s, x, 1.6, 5.8, 3.6, fast ? DARK : LIGHT);
  text(s, name, { x, y: 1.9, w: 5.8, h: 0.6, fontSize: 24, bold: true, align: "center", color: fast ? WHITE : DARK });
  text(s, secs, { x, y: 2.7, w: 5.8, h: 1.2, fontSize: 60, bold: true, align: "center", color: fast ? WHITE : TEAL });
  text(s, "seconds to check 60 test questions", { x, y: 4.1, w: 5.8, h: 0.6, fontSize: 18, align: "center", color: fast ? WHITE : TEXT });
};
timeCard(0.6, "Arize AX", "108–121", true);
timeCard(6.9, "Braintrust", "164–186", false);
bottom(s, "Same answers and the same checks in both. Arize was about 1 minute faster each time.");

// ---------- 5. Seeing the agent's steps ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "2b. Seeing the agent's steps: Arize is easier to understand");
const obs = (x, name, img, ratio, points) => {
  text(s, name, { x, y: 1.25, w: 5.9, h: 0.45, fontSize: 20, bold: true, color: DARK });
  const h = 3.0, w = h * ratio;
  s.addImage({ path: IMG(img), x: x + 2.6 - w / 2, y: 1.8, w, h, altText: name + " screenshot" });
  text(s, points.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < points.length - 1 } })),
    { x: x + 0.1, y: 4.95, w: 5.8, h: 1.0, fontSize: 15, paraSpaceAfter: 3 });
};
obs(0.6, "Arize AX", "crops/arize-tree.jpg", 1024 / 1140,
  ["Shows each step in order: main agent → helper agent → tool", "Time, tokens and cost on each step", "Also draws a map of all the steps"]);
obs(6.9, "Braintrust", "crops/bt-thread.jpg", 1114 / 1070,
  ["Shows the run like a chat: question → tools used → answer", "Time, tokens and cost for the whole run only", "No map"]);
bottom(s, "Arize's screens make it easy to see which step went wrong. Braintrust is fine for reading one answer.");

// ---------- 6. Without internet ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "2c. Can it work without internet (on our own computer)?");
const local = (x, name, verdictTxt, lines, good) => {
  box(s, x, 1.45, 5.9, 4.35, LIGHT);
  text(s, name, { x: x + 0.3, y: 1.65, w: 5.3, h: 0.5, fontSize: 22, bold: true, color: DARK });
  text(s, verdictTxt, { x: x + 0.3, y: 2.25, w: 5.3, h: 0.7, fontSize: 30, bold: true, color: good ? TEAL : RED });
  text(s, lines.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < lines.length - 1 } })),
    { x: x + 0.3, y: 3.1, w: 5.3, h: 2.6, fontSize: 16, paraSpaceAfter: 6 });
};
local(0.6, "Braintrust", "No: online only", ["Everything runs on Braintrust's website", "Own servers only with the big company plan (price on request)"], false);
local(6.8, "Arize", "Yes, with Phoenix", ["Arize AX (what we tested) is online", "Arize Phoenix is Arize's free, open-source version that runs on our own computer (we did not test it)", "Own servers for AX with the big company plan"], true);
bottom(s, "In both, the AI models (our agent and the AI judge) still need internet, unless we also run an AI model on our own computer.");

// ---------- 7. Cost per question ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "2d. Cost: both show the cost of each question");
text(s, "Arize AX", { x: 0.6, y: 1.25, w: 5.9, h: 0.45, fontSize: 20, bold: true, color: DARK });
s.addImage({ path: IMG("crops/arize-cost.jpg"), x: 0.6, y: 1.8, w: 5.6, h: 5.6 * 570 / 1024, altText: "Arize trace header with Cost $0.052911" });
text(s, [
  { text: "$0.053 for one question", options: { bold: true, fontSize: 22, color: TEAL, breakLine: true } },
  { text: "Also shows the cost of each step." },
], { x: 0.6, y: 5.0, w: 5.8, h: 0.95, fontSize: 15 });
text(s, "Braintrust", { x: 6.9, y: 1.25, w: 5.9, h: 0.45, fontSize: 20, bold: true, color: DARK });
s.addImage({ path: IMG("crops/bt-cost.jpg"), x: 7.9, y: 1.8, w: 3.1 * 858 / 830, h: 3.1, altText: "Braintrust metrics with Estimated cost $0.098" });
text(s, [
  { text: "$0.098 for one question", options: { bold: true, fontSize: 22, color: TEAL, breakLine: true } },
  { text: "Shown for the whole run. (From an earlier run of the same question.)" },
], { x: 6.9, y: 5.0, w: 5.8, h: 0.95, fontSize: 15 });
bottom(s, "This is the cost of the AI model (paid to Amazon). Arize and Braintrust do not charge it. All 73 questions cost about $3.14.");

// ---------- 8. Licence cost ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "3a. Licence cost: what we pay Arize and Braintrust");
table(s, [
  ["Free plan", "$0", "$0"],
  ["Team plan (Pro)", { text: "$50 a month = $600 a year", options: { bold: true, color: TEAL } }, { text: "$249 a month = $2,988 a year", options: { bold: true, color: TEAL } }],
  ["Big company plan", "Ask Arize for a price", "Ask Braintrust for a price"],
  ["Free plan limit", "25,000 recorded steps a month, data kept 15 days", "10,000 scores a month, data kept 14 days"],
  ["If we go over the limit", "Move to a bigger plan", "Pay extra: $3–$4 per GB, $1.50–$2.50 per 1,000 scores"],
], 1.4, [3.2, 4.45, 4.45], 16, 0.65);
bottom(s, "Our whole test fit in both free plans, so we paid $0. Prices from arize.com/pricing and braintrust.dev/pricing (19 Nov 2026).");

// ---------- 9. Maintenance cost ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "3b. Maintenance cost: what it takes to keep it running");
table(s, [
  ["Servers to look after", "None: it is an online service", "None: it is an online service"],
  ["Software updates", "Done by Arize", "Done by Braintrust"],
  ["Keep data longer than 30 days", "Big company plan", "$0.50 per GB a month"],
  ["Run on our own servers", "Big company plan, or the free Phoenix version", "Big company plan only"],
  ["Ongoing cost of each test run", "AI model: about $3.14 for 73 questions", "AI model: about $3.14 for 73 questions"],
], 1.4, [3.2, 4.45, 4.45], 16, 0.65);
bottom(s, "On the online plans, neither tool needs servers or staff from us. If we run it on our own servers, we also pay for the servers and the people to look after them.");

// ---------- 10. One-year example ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "3c. Cost for one year: example");
text(s, "If we run all 73 test questions 20 times a month:", { x: 0.6, y: 1.3, w: 12.1, h: 0.5, fontSize: 18, bold: true });
table(s, [
  ["Licence, free plan (data kept about 2 weeks)", "$0", "$0"],
  ["Licence, Pro plan (data kept 30 days)", "$600", "$2,988"],
  ["AI model, paid to Amazon (20 × 12 × $3.14)", "$754", "$754"],
  [{ text: "Total for one year with the Pro plan", options: { bold: true, color: WHITE, fill: { color: TEAL } } },
   { text: "$1,354", options: { bold: true, fontSize: 22, color: WHITE, fill: { color: TEAL } } },
   { text: "$3,742", options: { bold: true, fontSize: 22, color: WHITE, fill: { color: TEAL } } }],
], 1.95, [5.6, 3.25, 3.25], 17, 0.75);
bottom(s, "20 runs a month fits both free plans, but the free plans keep data for only about 2 weeks. The AI judge cost is not included.");

// ---------- 11. Our pick ----------
s = pres.addSlide({ masterName: "PLAIN" });
title(s, "Our pick: Arize AX");
const why = [
  ["Same checking", "Both tools gave the same result on 72 of 73 questions"],
  ["Cheaper", "$600 a year vs $2,988 a year (Pro plan)"],
  ["Faster", "About 1 minute faster to check 60 questions"],
  ["Easier to understand", "Shows each agent step, so we can see which step went wrong"],
  ["Can run locally", "Free Phoenix version runs on our own computer"],
];
why.forEach(([h, d], i) => {
  const y = 1.45 + i * 0.88;
  box(s, 0.6, y, 12.1, 0.75, i % 2 ? WHITE : LIGHT);
  text(s, "✔ " + h, { x: 0.85, y, w: 3.6, h: 0.75, fontSize: 19, bold: true, color: TEAL, valign: "middle" });
  text(s, d, { x: 4.5, y, w: 8.0, h: 0.75, fontSize: 17, valign: "middle" });
});
bottom(s, "What we give up: Braintrust shows cost by itself and was a bit quicker to set up. That is a one-time effort we have already done for Arize.");

// ---------- 12+. Every question ----------
const per = 25;
for (let p = 0; p < Math.ceil(n / per); p++) {
  s = pres.addSlide({ masterName: "PLAIN" });
  title(s, `Every question: tools and final answer (${p * per + 1}–${Math.min(n, (p + 1) * per)} of ${n})`);
  const mark = (v) => ({ text: v, options: { bold: v !== "PASS" && v !== "Yes", color: v === "FAIL" || v === "No" ? RED : v === "PASS" || v === "Yes" ? TEAL : GREY } });
  const body = ROWS.slice(p * per, (p + 1) * per).map((r) => [
    String(r.n), r.id, r.q.length > 95 ? r.q.slice(0, 92) + "..." : r.q, String(r.steps),
    mark(r.right === "Not set by the test" ? "Not named" : r.right), mark(r.arize), mark(r.bt)]);
  const hd = ["No.", "Question ID", "Test question", "Steps", "Right tools?", "Arize", "Braintrust"]
    .map((t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: DARK } } }));
  s.addTable([hd, ...body], { x: 0.6, y: 1.25, w: 12.1, colW: [0.5, 1.35, 6.6, 0.65, 1.1, 0.9, 1.0], fontSize: 9, rowH: 0.205,
    color: TEXT, valign: "middle", margin: 0.03, border: { type: "solid", pt: 0.5, color: "C9D3DA" } });
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));

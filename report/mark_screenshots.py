"""Zoom into the important part of each screenshot, draw red boxes, and save two versions:
zoom/<name>.png (for the slides) and for-senior/<name>.png (same, with the explanation printed underneath)."""
import json, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC = Path(sys.argv[1])            # report/screenshots
ZOOM, SENIOR = SRC / "zoom", SRC / "for-senior"
ZOOM.mkdir(exist_ok=True); SENIOR.mkdir(exist_ok=True)
RED = (230, 30, 30)
FONT = ImageFont.truetype("C:/Windows/Fonts/calibri.ttf", 22)
BOLD = ImageFont.truetype("C:/Windows/Fonts/calibrib.ttf", 22)

SHOTS = [  # name, source file, crop box, red boxes (source pixels), caption
 ("01-braintrust-preprod-compare", "26-v3-braintrust-v3-vs-v2.jpg", (40, 0, 1345, 200),
  [(55, 55, 300, 108), (805, 126, 995, 180), (985, 8, 1132, 36)],
  "Braintrust, Pre Prod: the new test round (v3) opens already compared with the last round (v2, purple line). Verdict 90.28% vs 91.23%: 2 answers better, 2 worse. No clicks needed."),
 ("02-arize-preprod-step1-list", "22-v2-arize-experiments-list.jpg", (225, 110, 1366, 440),
  [(355, 124, 530, 160), (228, 222, 1310, 433)],
  "Arize, Pre Prod, step 1: open the test set, tab \"Experiment Analysis\". It lists every test round (here 4 rounds of the earlier 60-question set)."),
 ("03-arize-preprod-step2-chart", "21-v2-arize-experiment-analysis.jpg", (236, 215, 1345, 560),
  [(248, 224, 950, 262), (553, 512, 1025, 550)],
  "Arize, Pre Prod, step 2: a chart of one score (ai_judge) across the test rounds; the buttons at the bottom choose the rounds and the score. Round #4 was best (96.4%)."),
 ("04-arize-preprod-step3-compare", "28-v3-arize-case-evaluators.jpg", (220, 60, 1366, 330),
  [(236, 72, 440, 103), (1210, 70, 1350, 103)],
  "Arize, Pre Prod, step 3: \"Compare Experiments\". Click \"+ Compare\" to add the last round next to this one; here only 1 round is chosen so far."),
 ("05-arize-cost-step1-price", "33-arize-cost-configs.jpg", (305, 110, 1285, 478),
  [(1141, 129, 1268, 164), (305, 340, 1222, 472)],
  "Arize, cost, step 1: Settings > Cost Configs. Arize knows \"claude-sonnet-4-6\" at $3 / $15 per million tokens. Our Amazon model name is not in the list; \"Add Model\" is where to add it (not tried yet)."),
 ("06-arize-cost-step2-run-cost", "29-arize-cost-overview.jpg", (230, 60, 1366, 310),
  [(1078, 210, 1350, 305)],
  "Arize, cost, step 2: once Arize knows the price, every run shows its cost. These 3 runs together: 19,550 tokens, $0.092319."),
 ("07-arize-cost-step3-step-cost", "31-arize-cost-per-call.jpg", (343, 10, 860, 300),
  [(570, 58, 702, 82), (345, 245, 842, 293)],
  "Arize, cost, step 3: open a run. The total is at the top ($0.052911); each step shows its own cost, for example one AI call (\"chat\"): $0.006258."),
 ("08-braintrust-cost-per-step", "32-braintrust-cost-per-step.jpg", (440, 0, 1366, 585),
  [(450, 18, 508, 44), (720, 358, 952, 396), (980, 456, 1180, 484)],
  "Braintrust, cost: no setup. Every step shows its cost; one AI call (\"chat\") = $0.006 (right). The total at the top ($0.098) also adds the agent steps, so it is double."),
 ("09-braintrust-counted-twice", "34-braintrust-double-count.jpg", (55, 52, 1345, 525),
  [(420, 56, 492, 78), (114, 175, 362, 214), (141, 365, 452, 403), (127, 479, 316, 518),
   (1128, 292, 1212, 339), (577, 342, 1052, 389)],
  "Braintrust, counted twice: the helper agent step (top left, and right) carries its own 3,909 tokens (3,157 in + 752 out). These are the same tokens as the two AI model calls inside it: 1,397 (the \"chat\" row) + 2,512 (the call inside the second loop row) = 3,909 tokens, costing $0.005 + $0.018 = $0.023. Braintrust adds both, so this step shows $0.023 + $0.023 = $0.046. The same happens for the main agent, so the whole question shows $0.098 (top) instead of the real $0.049."),
]

sizes = {}
for name, src, crop, boxes, caption in SHOTS:
    im = Image.open(SRC / src).convert("RGB").crop(crop)
    d = ImageDraw.Draw(im)
    for x0, y0, x1, y1 in boxes:
        d.rectangle((x0 - crop[0], y0 - crop[1], x1 - crop[0], y1 - crop[1]), outline=RED, width=4)
    im.save(ZOOM / f"{name}.png")
    sizes[name] = im.size
    # version for sending: explanation printed underneath
    head, body = caption.split(": ", 1)
    chars = max(40, im.width // 11)
    lines = [(head, BOLD)] + [(ln, FONT) for ln in textwrap.wrap(body[0].upper() + body[1:], chars)]
    strip_h = 20 + 30 * len(lines)
    out = Image.new("RGB", (im.width, im.height + strip_h), "white")
    out.paste(im, (0, 0))
    dd = ImageDraw.Draw(out)
    for i, (ln, f) in enumerate(lines):
        dd.text((14, im.height + 10 + 30 * i), ln, fill=(20, 30, 45), font=f)
    out.save(SENIOR / f"{name}.png")
(ZOOM / "sizes.json").write_text(json.dumps(sizes, indent=1))
print(json.dumps(sizes))

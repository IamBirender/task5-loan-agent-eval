"""STEP 4c (optional) - Let Arize AX price our real Claude traces, so it shows tokens AND dollars like Braintrust.

Why: Arize has a built-in price for "claude-sonnet-4-6" ($3 in / $15 out per million tokens), but our traces
came from Amazon Bedrock with the name "us.anthropic.claude-sonnet-4-6", which Arize does not recognise, so
it showed "Cost --". Arize prices a span only when it arrives, so this script:
  1. downloads the last N agent traces from the Arize project "loan-agents" (all steps, real token counts),
  2. sends exact copies to the project "loan-agents-claude-cost" with the model name "claude-sonnet-4-6".
Nothing else changes: same steps, same tokens, same durations, same inputs and answers. The Bedrock name is
kept in the attribute "original_model_id". No AI model is called, so this costs nothing.
Usage:  python step4c_arize_cost_view.py          # the last 3 Claude traces
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")  # Windows: avoids gRPC DNS errors when talking to arize.com
import pandas as pd                                                       # noqa: E402
from arize import ArizeClient                                             # noqa: E402
from arize.otel import register                                           # noqa: E402
from opentelemetry.trace import set_span_in_context                       # noqa: E402

from loan_agents import models  # noqa: E402,F401  (loads .env)

BEDROCK, ARIZE_NAME = "us.anthropic.claude-sonnet-4-6", "claude-sonnet-4-6"
ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=3, help="how many of the latest Claude traces to copy")
ap.add_argument("--only", default="", help="copy only the trace whose question contains this text (to re-send one)")
args = ap.parse_args()
SPACE = os.environ["ARIZE_SPACE_ID"]

# 1. Download the real traces
now = datetime.now(timezone.utc)
df = ArizeClient(api_key=os.environ["ARIZE_API_KEY"]).spans.export_to_df(
    space_id=SPACE, project_name="loan-agents", start_time=now - timedelta(days=30), end_time=now)
claude = df[df["attributes.llm.model_name"] == BEDROCK]
first = claude.groupby("context.trace_id")["start_time"].min().sort_values()
keep = list(first.index[-args.n:])
if args.only:
    roots = df[df["parent_id"].isna() & df["context.trace_id"].isin(keep)]
    keep = list(roots[roots["attributes.input.value"].str.contains(args.only, case=False, na=False)]["context.trace_id"])
df = df[df["context.trace_id"].isin(keep)].sort_values("start_time")


def flat(prefix, v, out):
    """Turn the exported nested values back into flat span attributes (OpenInference style)."""
    if hasattr(v, "tolist") and not isinstance(v, str):
        v = v.tolist()
    if isinstance(v, dict) and prefix == "metadata":
        out[prefix] = json.dumps(v, default=str)
    elif isinstance(v, dict):
        for k, x in v.items():
            flat(f"{prefix}.{k}", x, out)
    elif isinstance(v, list) and v and isinstance(v[0], dict):
        for i, x in enumerate(v):
            flat(f"{prefix}.{i}", x, out)
    elif isinstance(v, list):
        if v:
            out[prefix] = [x if isinstance(x, (str, int, float, bool)) else json.dumps(x, default=str) for x in v]
    elif isinstance(v, float) and v == v and "token_count" in prefix:   # Arize reads token counts only as whole numbers
        out[prefix] = int(v)
    elif isinstance(v, (str, bool, int, float)) and not (isinstance(v, float) and v != v):   # v != v means NaN
        out[prefix] = v


# 2. Send exact copies, shifted to now, with the model name Arize knows
tp = register(space_id=SPACE, api_key=os.environ["ARIZE_API_KEY"], project_name="loan-agents-claude-cost",
              set_global_tracer_provider=False, verbose=False, batch=False)   # one step at a time: reliable for big steps
tracer = tp.get_tracer("loan-agents-claude-cost")
utc = lambda x: x.tz_localize("UTC") if x.tzinfo is None else x            # noqa: E731
shift = now - timedelta(minutes=1) - utc(df["end_time"].max())   # copies end 1 minute ago (Arize drops future times)
ns = lambda x: int((utc(x) + shift).timestamp() * 1e9)                    # noqa: E731
spans, ends = {}, {}
for _, row in df.iterrows():
    attrs = {}
    for col, v in row.items():
        if col.startswith("attributes.") and not col.startswith("attributes.llm.cost"):
            flat(col[len("attributes."):], v, attrs)
    if attrs.get("llm.model_name") == BEDROCK:
        attrs["llm.model_name"], attrs["llm.provider"], attrs["original_model_id"] = ARIZE_NAME, "anthropic", BEDROCK
    parent = spans.get(row["parent_id"])
    spans[row["context.span_id"]] = s = tracer.start_span(
        row["name"], context=set_span_in_context(parent) if parent else None, start_time=ns(row["start_time"]), attributes=attrs)
    ends[row["context.span_id"]] = ns(row["end_time"])
for sid, s in spans.items():
    s.end(end_time=ends[sid])
tp.force_flush(60_000)
print(f"Copied {len(keep)} traces ({len(spans)} steps) to the Arize project 'loan-agents-claude-cost'.")
print("Open Arize -> Traces -> loan-agents-claude-cost: the Cost tile and each trace header now show dollars.")

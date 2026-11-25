"""STEP 4b (optional) - Send a few live agent traces to Arize AX so Arize shows tokens AND cost per trace.

Braintrust works out the cost by itself. Arize needs a price per model first, and it prices a trace only
when the trace arrives (old traces stay at "Cost --"). So:
  1. In Arize: Settings -> Cost Configs -> add the agent model and its price (README, "Arize cost view").
  2. Wait 10 minutes (Arize caches the prices), then run this script.
It does not grade anything and does not change any saved results.
Usage:  python step4b_arize_cost_traces.py         # 3 traces (the same first 3 cases as step 4)
        python step4b_arize_cost_traces.py --n 1
"""
import argparse
import os

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")  # Windows: avoids gRPC DNS errors when talking to arize.com
from arize.otel import register                                                      # noqa: E402
from openinference.instrumentation.strands_agents import StrandsAgentsToOpenInferenceProcessor  # noqa: E402

from loan_agents import models, runner                                               # noqa: E402
from scoring import cases                                                            # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=3, help="how many cases to trace")
args = ap.parse_args()

tracer = register(space_id=os.environ["ARIZE_SPACE_ID"], api_key=os.environ["ARIZE_API_KEY"],
                  project_name="loan-agents", span_processors=[StrandsAgentsToOpenInferenceProcessor()])
print(f"Model name to put in the Arize cost config: {models.agent_model_name()}")
for c in cases.load()[: args.n]:
    r = runner.run_case(c)
    print(f"traced {c['id']}: {r['tokens']} tokens, our own estimate ${r['est_cost_usd']}")
tracer.force_flush()
print("Open Arize -> Traces -> loan-agents. The Cost tile and each trace header should now show dollars.")

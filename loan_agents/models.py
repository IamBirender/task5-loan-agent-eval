"""Which AI model the agents and the judge use. One setting switches the whole run.

  MODEL_PROVIDER=groq       local test run  -> Groq free tier, model openai/gpt-oss-120b (no card needed)
  MODEL_PROVIDER=ollama     local test run  -> Ollama cloud (needs paid usage credits since late October 2026)
  MODEL_PROVIDER=bedrock    full run        -> Claude on Amazon Bedrock, e.g. in the AWS Builder Center sandbox
                                               (default us.anthropic.claude-sonnet-4-6; judge: JUDGE_PROVIDER=bedrock, Amazon Nova Pro)
  MODEL_PROVIDER=anthropic  full run        -> Claude through an Anthropic API key (default claude-opus-5-5)
  MODEL_PROVIDER=dryrun     wiring test     -> no model is called (checks the Arize / Braintrust connections for free)

The judge is always a DIFFERENT model from the agents, so no model grades its own answers.
  JUDGE_PROVIDER=groq (default) with JUDGE_MODEL=qwen/qwen3.8-27b, JUDGE_PROVIDER=bedrock (Amazon Nova Pro),
  JUDGE_PROVIDER=anthropic (claude-sonnet-5-5, when the agents run on claude-opus-5-5) or JUDGE_PROVIDER=ollama.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent.parent
load_dotenv(HERE / ".env")          # this folder's .env first
load_dotenv(HERE.parent / ".env")   # then the project root .env (does not overwrite)

PROVIDER = os.getenv("MODEL_PROVIDER", "groq").lower()
JUDGE_PROVIDER = os.getenv("JUDGE_PROVIDER", "groq").lower()

# Services that speak the OpenAI format: base address, key, default agent model, default judge model
OPENAI_STYLE = {
    "groq": ("https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY", ""), "openai/gpt-oss-120b", "qwen/qwen3.8-27b"),
    "ollama": ("https://ollama.com/v1", os.getenv("OLLAMA_API_KEY") or os.getenv("Ollam_api_key", ""), "gpt-oss:120b", "nemotron-3-super"),
}
# Amazon Bedrock (AWS Builder Center sandbox): Claude for the agents, a non-Claude model (Amazon Nova) for the judge
BEDROCK_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_DEFAULTS = (os.getenv("BEDROCK_MODEL", "us.anthropic.claude-sonnet-4-6"), "us.amazon.nova-pro-v1:0")

AGENT_MODEL = os.getenv("AGENT_MODEL") or {"anthropic": os.getenv("CLAUDE_MODEL", "claude-opus-5-5"),
                                           "bedrock": BEDROCK_DEFAULTS[0], "dryrun": "none (dry run)"}.get(
    PROVIDER, OPENAI_STYLE.get(PROVIDER, ("", "", "unknown", ""))[2])
AGENT_VERSION = os.getenv("AGENT_VERSION", "v3")   # v1 first sandbox run, v2 after the review fixes, v3 + G9-G20 cases
JUDGE_MODEL = os.getenv("JUDGE_MODEL") or {"bedrock": BEDROCK_DEFAULTS[1], "anthropic": "claude-sonnet-5-5"}.get(
    JUDGE_PROVIDER) or OPENAI_STYLE[JUDGE_PROVIDER][3]


RUN_AGENTS: list = []   # every agent created during one test case (to add up their token usage)
# Estimated list prices, US$ per million tokens (input, output). Used only for the G17 cost estimate.
PRICES = {"claude-sonnet-4-6": (3.0, 15.0), "claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0),
          "gpt-oss-120b": (0.15, 0.6)}


def track(agent):
    RUN_AGENTS.append(agent)
    return agent


def usage_and_cost() -> dict:
    """Tokens used by every agent in the current case, and the estimated cost at list price."""
    tin = sum(a.event_loop_metrics.accumulated_usage.get("inputTokens", 0) for a in RUN_AGENTS)
    tout = sum(a.event_loop_metrics.accumulated_usage.get("outputTokens", 0) for a in RUN_AGENTS)
    price = next((v for k, v in PRICES.items() if k in AGENT_MODEL), None)   # works with prefixes / version suffixes
    cost = round((tin * price[0] + tout * price[1]) / 1e6, 4) if price else None
    return {"input_tokens": tin, "output_tokens": tout, "tokens": tin + tout, "est_cost_usd": cost}


def agent_model_name() -> str:
    return AGENT_MODEL


def agent_model():
    """The model object every agent (and the text-to-SQL helper) runs on."""
    if PROVIDER == "anthropic":
        from strands.models.anthropic import AnthropicModel
        return AnthropicModel(client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]}, model_id=AGENT_MODEL, max_tokens=16000)
    if PROVIDER == "bedrock":   # AWS credentials come from the machine (e.g. the Builder Center Code Editor role)
        from strands.models import BedrockModel
        return BedrockModel(model_id=AGENT_MODEL, region_name=BEDROCK_REGION, max_tokens=16000)
    from strands.models.openai import OpenAIModel
    base_url, key, _, _ = OPENAI_STYLE[PROVIDER]
    return OpenAIModel(client_args={"base_url": base_url, "api_key": key}, model_id=AGENT_MODEL, params={"temperature": 0})


def judge_complete(prompt: str) -> str:
    """Send one prompt to the judge model and return its text reply. Both Arize and Braintrust use it."""
    if JUDGE_PROVIDER == "bedrock":
        import boto3
        reply = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION).converse(
            modelId=JUDGE_MODEL, messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 2000, "temperature": 0})   # temperature 0: same answer -> same score
        return "".join(b.get("text", "") for b in reply["output"]["message"]["content"])
    if JUDGE_PROVIDER == "anthropic":   # a different Claude model from the agents (default claude-sonnet-5-5)
        import anthropic
        reply = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]).messages.create(
            model=JUDGE_MODEL, max_tokens=4000, messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in reply.content if b.type == "text")
    import time
    from openai import OpenAI, RateLimitError
    base_url, key, _, _ = OPENAI_STYLE[JUDGE_PROVIDER]
    for wait in (15, 30, 60, 60, 0):   # free tiers allow few tokens per minute: wait and try again
        try:
            reply = OpenAI(base_url=base_url, api_key=key, max_retries=0).chat.completions.create(
                model=JUDGE_MODEL, temperature=0, messages=[{"role": "user", "content": prompt}])
            return reply.choices[0].message.content or ""
        except RateLimitError:
            if not wait:
                raise
            time.sleep(wait)

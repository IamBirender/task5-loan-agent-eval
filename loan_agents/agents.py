"""Loan edition of the AWS repo's agent team: one Supervisor + four specialists (the "agents-as-tools" pattern,
copied from the repo's src/mna/agents/supervisor.py). New agents are built for every test case, so no memory
leaks from one case into the next.
"""
from pathlib import Path

from strands import Agent, tool

from . import data, models
from .tools import ALL, CALLS

PROMPTS = Path(__file__).resolve().parent / "prompts"
SPECIALIST_TOOLS = {
    "pool_screening": ["text_to_sql", "kb_retrieve"],
    "credit_performance": ["loan_performance", "credit_performance", "kb_retrieve"],
    "cohort_comparison": ["cohort_comparison", "memory_read", "kb_retrieve"],
    "compliance_validation": ["citation_check", "data_validation", "loan_performance", "credit_performance", "text_to_sql", "kb_retrieve"],
}
# Names used in the test cases ("evaluatedAgent") -> our agent names
CASE_AGENT = {"Supervisor Agent": "supervisor", "Pool Screening Agent": "pool_screening",
              "Credit Performance Agent": "credit_performance", "Cohort Comparison Agent": "cohort_comparison",
              "Compliance Validation Agent": "compliance_validation"}


def _prompt(name: str) -> str:
    """The agent's instructions, with the size of the loan pool in use (it differs per case set)."""
    p = data.pool_profile()
    return ((PROMPTS / f"{name}.txt").read_text(encoding="utf-8")
            .replace("{{RECORDS}}", str(p["records"])).replace("{{LAST_PERIOD}}", p["last_period"]))


def _specialist(name: str) -> Agent:
    return models.track(Agent(name=name, model=models.agent_model(), system_prompt=_prompt(name),
                 tools=[ALL[t] for t in SPECIALIST_TOOLS[name]], callback_handler=None))


def _as_tool(name: str, agent: Agent):
    """Wrap a specialist so the Supervisor can call it like a tool (same as the repo's fallback shim)."""
    def ask(request: str) -> str:
        CALLS.append({"tool": f"agent:{name}", "args": {"request": request[:500]}, "output": ""})
        return str(agent(request))
    ask.__name__ = f"ask_{name}_agent"
    ask.__doc__ = (f"Send a request to the {name.replace('_', ' ')} specialist agent and get its answer. "
                   "Pass the user's exact wording.\n\nArgs:\n    request: the task for the specialist")
    return tool(ask)


def build(agent_name: str) -> Agent:
    """Return a fresh agent by name: 'supervisor' or one of the four specialists."""
    if agent_name != "supervisor":
        return _specialist(agent_name)
    specialists = [_as_tool(n, _specialist(n)) for n in SPECIALIST_TOOLS]
    return models.track(Agent(name="supervisor", model=models.agent_model(),
                 system_prompt=_prompt("supervisor"),
                 tools=specialists + [ALL["kb_retrieve"]], callback_handler=None))

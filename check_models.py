"""Quick check (about 10 seconds): can this machine reach the agent model and the judge model? Run it before step 3.
Usage:  python check_models.py
"""
from strands import Agent

from loan_agents import models

print(f"agent model: {models.PROVIDER} / {models.agent_model_name()}")
print("   reply:", str(Agent(model=models.agent_model(), callback_handler=None)("Reply with the single word OK.")).strip()[:60])
print(f"judge model: {models.JUDGE_PROVIDER} / {models.JUDGE_MODEL}")
print("   reply:", models.judge_complete("Reply with the single word OK.").strip()[:60])
print("Both models answered. You can run the steps.")

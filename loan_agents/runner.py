"""Run one test case through the right agent and return what happened: answer, tool calls, time, tokens, cost, errors.
Multi-turn cases (G11) send each turn to the same agent, so it keeps the conversation. Fault cases (G18) make one tool fail."""
import time

from . import agents, data, models, tools


def run_case(case: dict) -> dict:
    tools.CALLS.clear()
    models.RUN_AGENTS.clear()
    tools.FAULT = case.get("fault")
    before = data.fingerprint()
    t0, answers, error = time.time(), [], ""
    try:
        if models.PROVIDER == "dryrun":   # free wiring test: no model is called
            answers = [f"(dry run - no AI model was called for {case['id']})"]
        else:
            agent = agents.build(agents.CASE_AGENT[case["agent"]])
            for turn in case.get("turns") or [case["input"]]:
                answers.append(str(agent(turn)))
    except Exception as e:  # keep going; the error is saved and the case can be re-run later
        error = f"{type(e).__name__}: {e}"[:500]
    finally:
        tools.FAULT = None
    intact = data.fingerprint() == before
    return {"id": case["id"], "agent": case["agent"], "model": models.agent_model_name(), "provider": models.PROVIDER,
            "seconds": round(time.time() - t0, 1), "answer": answers[-1] if answers else "",
            "turn_answers": answers if len(answers) > 1 else None, **models.usage_and_cost(),
            "tool_calls": list(tools.CALLS), "tables_intact": bool(intact), "error": error}

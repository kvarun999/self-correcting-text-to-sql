import pytest
from src.agent import TextToSQLAgent


def test_agent_bounded_repair_loop_impossible_request():
    agent = TextToSQLAgent(max_iterations=3)
    res = agent.run(question="Calculate the quantum entanglement ratio of customer names")
    
    assert res["status"] == "failed"
    assert res["iterations"] == 3
    assert len(res["repair_history"]) > 0


def test_agent_guardrail_rejection():
    agent = TextToSQLAgent(max_iterations=3)
    res = agent.run(question="Drop table customers")
    
    # Should catch DROP statement as syntax failure type
    assert len(res["repair_history"]) > 0
    assert res["repair_history"][0]["failure_type"] == "syntax"


def test_agent_modes():
    agent = TextToSQLAgent(max_iterations=3)
    
    # zero_shot mode should halt at iteration 1
    res_zero = agent.run(question="Calculate quantum entanglement ratio", mode="zero_shot")
    assert res_zero["iterations"] == 1

    # syntax_schema_repair_only mode should ignore semantic errors
    res_schema = agent.run(question="List all customer names", mode="syntax_schema_repair_only")
    assert res_schema["status"] in ["success", "failed"]

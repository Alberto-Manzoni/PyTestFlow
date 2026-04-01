import pytest
from pytestflow.core import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core.sequence import TestSequence
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.string_check import string_check_step
from pytestflow.steps.action_step import action_step

# --- Setup and Cleanup Steps ---
@action_step(name="setup_marker", store_as="setup_marker")
def setup_marker():
    return "setup_executed"

@action_step(name="cleanup_marker", store_as="cleanup_marker")
def cleanup_marker():
    return "cleanup_executed"

# --- Main Steps ---
@numeric_limit_step(name="num_limit_pass", limit=100, mode="le")
def num_limit_pass():
    return 42

@numeric_limit_step(name="num_limit_fail", limit=10, mode="le")
def num_limit_fail():
    return 99

@string_check_step(name="string_check", expected="expected", match="exact")
def string_check():
    return "expected"


# --- Test: Full Sequence Run ---
def test_testsequence_full_run():
    ts = TestSequence(
        name="TestSequenceFull",
        setup_steps=[setup_marker],
        main_steps=[num_limit_pass, num_limit_fail, string_check],
        cleanup_steps=[cleanup_marker],
    )

    result = ts.run(return_state=True)
    
    assert isinstance(result, PyTestflowFailed)  # num_limit_fail should fail
    assert len(result.children) == 5

    names = [name for name, _ in result.children]
    assert names == [
        "setup_marker", "num_limit_pass", "num_limit_fail", "string_check", "cleanup_marker"
    ]

    assert ptf_context.locals["setup_marker"] == "setup_executed"
    assert ptf_context.locals["cleanup_marker"] == "cleanup_executed"

# --- Test: Partial Step Run (string_check only) ---
def test_testsequence_partial_run():
    ts = TestSequence(
        name="TestSequencePartial",
        setup_steps=[setup_marker],
        main_steps=[num_limit_pass, num_limit_fail, string_check],
        cleanup_steps=[cleanup_marker],
    )

    result = ts.run_step("string_check",return_state=True)

    assert isinstance(result, PyTestflowPassed)  # string_check should pass
    assert len(result.children) == 3

    names = [name for name, _ in result.children]
    assert names == ["setup_marker", "string_check", "cleanup_marker"]

    assert ptf_context.locals["setup_marker"] == "setup_executed"
    assert ptf_context.locals["cleanup_marker"] == "cleanup_executed"

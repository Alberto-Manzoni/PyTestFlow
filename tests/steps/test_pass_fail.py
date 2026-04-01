import pytest
from pytestflow.steps.pass_fail import pass_fail_step
import time
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed

@pass_fail_step(name="pass_case")
def pass_case():
    time.sleep(0.001)  # Simulate some processing time
    return True

@pass_fail_step(name="fail_case")
def fail_case():
    time.sleep(0.001)  # Simulate some processing time
    return False

def test_pass_fail_pass():
    result = pass_case()
    assert isinstance(result, PyTestflowPassed)
    assert result.ptf_result["step_status"] == "passed"

def test_pass_fail_fail():
    result = fail_case()
    assert isinstance(result, PyTestflowFailed)
    assert result.ptf_result["step_status"] == "failed"

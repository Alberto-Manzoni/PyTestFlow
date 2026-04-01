import pytest
from pytestflow.steps.string_check import string_check_step
import time
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed

@string_check_step(expected="hello", match="exact", name="str_pass")
def str_pass():
    time.sleep(0.001)  # Simulate some processing time
    return "hello"

@string_check_step(expected="hello", match="exact", name="str_fail")
def str_fail():
    time.sleep(0.001)  # Simulate some processing time
    return "hi"

def test_string_check_pass():
    result = str_pass()
    assert isinstance(result, PyTestflowPassed)
    assert result.ptf_result["step_status"] == "passed"

def test_string_check_fail():
    result = str_fail()
    assert isinstance(result, PyTestflowFailed)
    assert result.ptf_result["step_status"]

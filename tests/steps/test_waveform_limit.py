import pytest
from pytestflow.steps.waveform_limit import waveform_limit_step
import time
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed

lower = [(0, 1), (1, 1), (2, 1)]
upper = [(0, 3), (1, 3), (2, 3)]

@waveform_limit_step(lower_mask=lower, upper_mask=upper, mode="between", name="waveform_pass")
def waveform_pass():
    time.sleep(0.001)  # Simulate some processing time
    return {"x": [0, 1, 2], "y": [2.0, 2.5, 2.8]}

@waveform_limit_step(lower_mask=lower, upper_mask=upper, mode="between", name="waveform_fail")
def waveform_fail():
    time.sleep(0.001)  # Simulate some processing time
    return {"x": [0, 1, 2], "y": [0.5, 2.5, 3.5]}

def test_waveform_limit_pass():
    result = waveform_pass()
    assert isinstance(result, PyTestflowPassed)
    assert result.ptf_result["step_status"] == "passed"

def test_waveform_limit_fail():
    result = waveform_fail()
    assert isinstance(result, PyTestflowFailed)

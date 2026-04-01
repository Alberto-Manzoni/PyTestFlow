import pytest
import pandas as pd
from pytestflow.steps.df_numeric_limits import df_numeric_limits_step
import time
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed

limits = pd.DataFrame([
    {"name": "v1", "limit": 5.0, "mode": "le"},
    {"name": "v2", "limit": 3.0, "mode": "ge"},
])

@df_numeric_limits_step(limits_df=limits, name="df_pass")
def df_pass():
    time.sleep(0.001)  # Simulate some processing time
    return {"v1": 4.5, "v2": 3.5}

@df_numeric_limits_step(limits_df=limits, name="df_fail")
def df_fail():
    time.sleep(0.001)  # Simulate some processing time
    return {"v1": 6.0, "v2": 2.0}

def test_df_numeric_limits_pass():
    result = df_pass()
    time.sleep(0.001)  # Simulate some processing time
    assert isinstance(result, PyTestflowPassed)
    assert result.ptf_result["step_status"] == "passed"

def test_df_numeric_limits_fail():
    result = df_fail()
    time.sleep(0.001)  # Simulate some processing time
    assert isinstance(result, PyTestflowFailed)
    assert result.ptf_result["step_status"] == "failed"

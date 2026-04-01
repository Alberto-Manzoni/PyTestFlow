import pytest
from pytestflow.core.sequence import Sequence
from pytestflow.steps.pass_fail import pass_fail_step
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.df_numeric_limits import df_numeric_limits_step
from pytestflow.steps.string_check import string_check_step
from pytestflow.steps.waveform_limit import waveform_limit_step
from pytestflow.steps.action_step import action_step
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core import ptf_context  # Import the context to verify locals
import pandas as pd
import time

# --- Define Decorated Steps ---

# Pass/Fail Steps
@pass_fail_step(name="pass_fail_pass")
def pass_fail_pass():
    return True

@pass_fail_step(name="pass_fail_fail")
def pass_fail_fail():
    return False

# Numeric Limit Steps
@numeric_limit_step(name="numeric_limit_pass", limit=100, mode="le")
def numeric_limit_pass():
    return 42  # Within the limit

@numeric_limit_step(name="numeric_limit_fail",limit=50,mode="le")
def numeric_limit_fail():
    return 999  # Exceeds the limit

# DF Numeric Limit Steps
limits = pd.DataFrame([
    {"name": "v1", "limit": 5.0, "mode": "le"},
    {"name": "v2", "limit": 3.0, "mode": "ge"},
])

@df_numeric_limits_step(limits_df=limits, name="df_numeric_limit_pass")
def df_numeric_limit_pass():
    return {"v1": 4.5, "v2": 3.5}  # All values within the limit

@df_numeric_limits_step(limits_df=limits, name="df_numeric_limit_fail")
def df_numeric_limit_fail():
    return {"v1": 6.0, "v2": 2.0}  # One value exceeds the limit

# String Check Steps
@string_check_step(name="string_check_pass", expected="valid_string",match='exact')
def string_check_pass():
    return "valid_string"

@string_check_step(name="string_check_fail",expected="valid_string",match='exact')
def string_check_fail():
    return "invalid_string"

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

# Action Step with `store_as`
@action_step(name="action_store_as", store_as="stored_value")
def action_store_as():
    return "stored_string"

# --- Test Sequence with All Step Types ---
def test_sequence_with_all_step_types():
    seq = Sequence(
        name="TestSequenceAllStepTypes",
        steps=[
            pass_fail_pass,
            pass_fail_fail,
            numeric_limit_pass,
            numeric_limit_fail,
            df_numeric_limit_pass,
            df_numeric_limit_fail,
            string_check_pass,
            string_check_fail,
            waveform_pass,
            waveform_fail,
            action_store_as,
        ],
    )
    result = seq.run(parameters={}, return_state=True)  # Run the sequence
            
    # Verify the sequence result
    assert isinstance(result, PyTestflowFailed)  # Sequence should fail because some steps fail
    assert len(result.children) == 11  # Eleven steps in the sequence

    # Verify individual step results
    assert result.children[0][1].ptf_result["step_status"] == "passed"  # pass_fail_pass
    assert result.children[1][1].ptf_result["step_status"] == "failed"  # pass_fail_fail
    assert result.children[2][1].ptf_result["step_status"] == "passed"  # numeric_limit_pass
    assert result.children[3][1].ptf_result["step_status"] == "failed"  # numeric_limit_fail
    assert result.children[4][1].ptf_result["step_status"] == "passed"  # df_numeric_limit_pass
    assert result.children[5][1].ptf_result["step_status"] == "failed"  # df_numeric_limit_fail
    assert result.children[6][1].ptf_result["step_status"] == "passed"  # string_check_pass
    assert result.children[7][1].ptf_result["step_status"] == "failed"  # string_check_fail
    assert result.children[8][1].ptf_result["step_status"] == "passed"  # waveform_limit_pass
    assert result.children[9][1].ptf_result["step_status"] == "failed"  # waveform_limit_fail
    assert result.children[10][1].ptf_result["step_status"] == "done"   # action_store_as

    # Verify the value stored in ptf_context.locals
    assert ptf_context.locals["stored_value"] == "stored_string"

import pytest
import time
from datetime import datetime

from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed


@numeric_limit_step(limit=10, mode="ge", name="numeric_pass")
def numeric_pass():
    time.sleep(0.002)  # simulate some work
    return 15


@numeric_limit_step(limit=20, mode="ge", name="numeric_fail")
def numeric_fail():
    time.sleep(0.002)
    return 15


def test_numeric_limit_pass():
    result = numeric_pass()
    assert isinstance(result, PyTestflowPassed)
    assert result.ptf_result["step_status"] == "passed"

    # --- metadata checks ---
    meta = result.ptf_result
    # start_time should be a valid ISO datetime
    dt = datetime.fromisoformat(meta["start_time"])
    assert isinstance(dt, datetime)

    # duration should be > 0
    assert meta["duration_s"] > 0
    # and very small (since we only slept a few ms)
    assert meta["duration_s"] < 1.0


def test_numeric_limit_fail():
    result = numeric_fail()
    assert isinstance(result, PyTestflowFailed)
    assert result.ptf_result["step_status"] == "failed"

    # --- metadata checks ---
    meta = result.ptf_result
    dt = datetime.fromisoformat(meta["start_time"])
    assert isinstance(dt, datetime)
    assert meta["duration_s"] > 0
    assert meta["duration_s"] < 1.0

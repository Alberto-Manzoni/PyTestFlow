# tests/steps/test_pytestflow_states.py

import pytest
from pytestflow.core.pytestflow_states import (
    PyTestflowState,
    PyTestflowPassed,
    PyTestflowFailed,
    PyTestflowDone,
    PyTestflowError,
)


def test_base_state_sets_result_correctly():
    ptf_result = {"output": 123, "step_status": "done"}
    state = PyTestflowState(ptf_result=ptf_result, type="COMPLETED")
    assert state.data == 123
    assert state.result() == 123


def test_base_state_output_takes_precedence_over_result():
    ptf_result = {"output": 456}
    state = PyTestflowState(ptf_result=ptf_result, result=999, type="COMPLETED")
    # output from ptf_result must always win over raw result
    assert state.data == 456


def test_child_states_assignment_and_summary():
    parent = PyTestflowState(ptf_result={"step_status": "done"}, type="COMPLETED")
    child = PyTestflowPassed(ptf_result={"output": 42})
    parent.add_child("child_step", child)

    summary = parent.summarize()

    assert summary["status"] == "done"
    assert summary["children"] == ["child_step"]


@pytest.mark.parametrize("StateClass,name,step_status", [
    (PyTestflowPassed, "Passed", "passed"),
    (PyTestflowFailed, "Failed", "failed"),
    (PyTestflowDone,   "Done",   "done"),
    (PyTestflowError,  "Error",  "error"),
])
def test_subclass_metadata(StateClass, name, step_status):
    state = StateClass(ptf_result={"output": 999})
    # TestStand semantics are kept in ptf_result
    assert state.name == name
    assert state.type.value == "COMPLETED"   # always COMPLETED for Prefect
    assert state.ptf_result["step_status"] == step_status
    assert state.data == 999


def test_state_handles_missing_output():
    ptf_result = {"step_status": "done"}
    state = PyTestflowState(ptf_result=ptf_result, type="COMPLETED")
    assert state.data is None
    assert state.ptf_result["step_status"] == "done"


def test_state_allows_none_ptf_result():
    state = PyTestflowState(ptf_result=None, type="COMPLETED")
    assert isinstance(state.ptf_result, dict)
    assert state.data is None
# tests/core/test_states.py

import pytest
from pytestflow.core.pytestflow_states import (
    PyTestflowState,
    PyTestflowPassed,
    PyTestflowFailed,
    PyTestflowDone,
    PyTestflowError,
)


def test_base_state_sets_result_correctly():
    ptf_result = {"output": 123, "step_status": "done"}
    state = PyTestflowState(ptf_result=ptf_result, type="COMPLETED")
    assert state.data == 123
    assert state.result() == 123


def test_base_state_output_takes_precedence_over_result():
    ptf_result = {"output": 456}
    state = PyTestflowState(ptf_result=ptf_result, result=999, type="COMPLETED")
    assert state.data == 456  # output from ptf_result must always win


def test_child_states_assignment_and_summary():
    parent = PyTestflowState(ptf_result={"step_status": "done"}, type="COMPLETED")
    child = PyTestflowPassed(ptf_result={"output": 42, "step_status": "passed"})
    parent.add_child("child_step", child)

    summary = parent.summarize()

    assert summary["status"] == "done"
    assert summary["children"] == ["child_step"]


@pytest.mark.parametrize("StateClass,name,expected_status,prefect_type", [
    (PyTestflowPassed, "Passed", "passed", "COMPLETED"),
    (PyTestflowFailed, "Failed", "failed", "COMPLETED"),
    (PyTestflowDone,   "Done",   "done",   "COMPLETED"),
    (PyTestflowError,  "Error",  "error",  "CRASHED"),
])
def test_subclass_metadata(StateClass, name, expected_status, prefect_type):
    # Explicitly pass step_status so we don’t rely on subclass injecting it
    state = StateClass(ptf_result={"output": 999, "step_status": expected_status})
    assert state.name == name
    assert state.type.value == prefect_type
    assert state.ptf_result["step_status"] == expected_status
    assert state.data == 999


def test_state_handles_missing_output():
    ptf_result = {"step_status": "done"}
    state = PyTestflowState(ptf_result=ptf_result, type="COMPLETED")
    assert state.data is None
    assert state.ptf_result["step_status"] == "done"


def test_state_allows_none_ptf_result():
    state = PyTestflowState(ptf_result=None, type="COMPLETED")
    assert isinstance(state.ptf_result, dict)
    assert state.data is None

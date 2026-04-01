import pytest

from pytestflow.core.pytestflow_states import (
    PyTestflowDone,
    PyTestflowError,
    PyTestflowFailed,
    PyTestflowPassed,
)
from pytestflow.core.sequence import Sequence, TestSequence
from pytestflow.steps.action_step import action_step


def test_sequence_wraps_step_exception_as_error_state():
    @action_step(name="ok_step")
    def ok_step():
        return "ok"

    @action_step(name="boom_step")
    def boom_step():
        raise RuntimeError("boom")

    seq = Sequence(name="exception_sequence", steps=[ok_step, boom_step])
    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowFailed)
    assert len(result.children) == 2
    assert isinstance(result.children[0][1], PyTestflowDone)
    assert isinstance(result.children[1][1], PyTestflowError)
    assert result.children[1][1].ptf_result["step_status"] == "error"
    assert "boom" in result.children[1][1].ptf_result["error"]


@pytest.mark.parametrize(
    "status, expected_state, expected_step_status, expected_sequence_state",
    [
        ("passed", PyTestflowPassed, "forced_pass", PyTestflowPassed),
        ("failed", PyTestflowFailed, "forced_fail", PyTestflowFailed),
        ("done", PyTestflowDone, "done", PyTestflowPassed),
        ("skipped", PyTestflowDone, "skipped", PyTestflowPassed),
    ],
)
def test_force_step_status_maps_supported_statuses(
    status, expected_state, expected_step_status, expected_sequence_state
):
    seq = Sequence(name="forced_status_sequence")
    seq.force_step_status("forced_step", status)

    result = seq.run(return_state=True)

    assert isinstance(result, expected_sequence_state)
    assert len(result.children) == 1
    step_name, step_state = result.children[0]
    assert step_name == "forced_step_forced"
    assert isinstance(step_state, expected_state)
    assert step_state.ptf_result["step_status"] == expected_step_status


def test_force_step_status_unsupported_status_is_captured_as_error():
    seq = Sequence(name="forced_invalid_status_sequence")
    seq.force_step_status("forced_step", "invalid_status")

    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowFailed)
    assert len(result.children) == 1
    _, step_state = result.children[0]
    assert isinstance(step_state, PyTestflowError)
    assert step_state.ptf_result["step_status"] == "error"
    assert "Unsupported status: invalid_status" in step_state.ptf_result["error"]


def test_testsequence_run_step_missing_step_raises():
    @action_step(name="setup_marker")
    def setup_marker():
        return "setup"

    @action_step(name="known_step")
    def known_step():
        return "main"

    @action_step(name="cleanup_marker")
    def cleanup_marker():
        return "cleanup"

    ts = TestSequence(
        name="missing_step_sequence",
        setup_steps=[setup_marker],
        main_steps=[known_step],
        cleanup_steps=[cleanup_marker],
    )

    with pytest.raises(ValueError, match="Step 'unknown_step' not found"):
        ts.run_step("unknown_step", return_state=True)

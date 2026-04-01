import pytest
pytest tests/sequences/test_flow_control_sequence.py::test_sequence_jump_by_step_name_skips_intermediate_step -q

from pytestflow.core.context import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowError, PyTestflowFailed, PyTestflowPassed
from pytestflow.core.sequence import Sequence, TestSequence
from pytestflow.steps.action_step import action_step
from pytestflow.steps.flow_control import flow_control_step


@pytest.fixture(autouse=True)
def clear_context():
    ptf_context.locals.clear()
    ptf_context.globals.clear()
    yield
    ptf_context.locals.clear()
    ptf_context.globals.clear()


def test_sequence_jump_by_step_name_skips_intermediate_step():
    @flow_control_step(name="gate")
    def gate():
        ptf_context.locals["_ptf_next_step"] = "final_step"
        return "jump"

    @action_step(name="middle_step", store_as="middle_ran")
    def middle_step():
        return True

    @action_step(name="final_step", store_as="final_ran")
    def final_step():
        return True

    seq = Sequence(name="jump_sequence", steps=[gate, middle_step, final_step])
    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert [name for name, _ in result.children] == ["gate", "final_step"]
    assert "middle_ran" not in ptf_context.locals
    assert ptf_context.locals["final_ran"] is True


def test_sequence_end_directive_stops_execution():
    @flow_control_step(name="gate")
    def gate():
        ptf_context.locals["_ptf_next_step"] = "end"
        return "stop"

    @action_step(name="never_runs", store_as="never_runs")
    def never_runs():
        return True

    seq = Sequence(name="end_sequence", steps=[gate, never_runs])
    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert [name for name, _ in result.children] == ["gate"]
    assert "never_runs" not in ptf_context.locals


def test_sequence_invalid_jump_target_adds_flow_control_error():
    @flow_control_step(name="gate")
    def gate():
        ptf_context.locals["_ptf_next_step"] = "missing_step"
        return "bad_jump"

    @action_step(name="never_runs")
    def never_runs():
        return True

    seq = Sequence(name="invalid_jump_sequence", steps=[gate, never_runs])
    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowFailed)
    assert [name for name, _ in result.children] == ["gate", "__flow_control__"]
    assert isinstance(result.children[1][1], PyTestflowError)
    assert "Invalid _ptf_next_step" in result.children[1][1].ptf_result["error"]


def test_testsequence_jump_can_skip_main_and_continue_to_cleanup():
    @flow_control_step(name="setup_gate")
    def setup_gate():
        ptf_context.locals["_ptf_next_step"] = "cleanup_marker"
        return "skip_main"

    @action_step(name="main_step", store_as="main_ran")
    def main_step():
        return True

    @action_step(name="cleanup_marker", store_as="cleanup_ran")
    def cleanup_marker():
        return True

    ts = TestSequence(
        name="testsequence_jump",
        setup_steps=[setup_gate],
        main_steps=[main_step],
        cleanup_steps=[cleanup_marker],
    )
    result = ts.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert [name for name, _ in result.children] == ["setup_gate", "cleanup_marker"]
    assert "main_ran" not in ptf_context.locals
    assert ptf_context.locals["cleanup_ran"] is True

import pytest

from pytestflow.core.context import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowPassed
from bootstrap_templates.process_models.sequential_model import SequentialProcessModel
from pytestflow.steps.action_step import action_step
from pytestflow.steps.flow_control import flow_control_step


@pytest.fixture(autouse=True)
def clear_context():
    ptf_context.locals.clear()
    ptf_context.globals.clear()
    yield
    ptf_context.locals.clear()
    ptf_context.globals.clear()


@flow_control_step(name="pre_uut_cancel")
def pre_uut_cancel():
    return {"button": "cancel"}


@flow_control_step(name="pre_uut_run")
def pre_uut_run():
    return {"button": "run"}


@action_step(name="main_sequence_step", store_as="main_ran")
def main_sequence_step():
    return True


@action_step(name="post_uut_step", store_as="post_ran")
def post_uut_step():
    return True


def test_sequential_model_cancel_ends_before_main():
    model = SequentialProcessModel(
        name="pm_cancel",
        callbacks={
            "pre_uut": pre_uut_cancel,
            "main_sequence": main_sequence_step,
            "post_uut": post_uut_step,
            "report": None,
            "database_logging": None,
        },
        cancel_action="end",
    )

    result = model.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert [name for name, _ in result.children] == ["pre_uut_cancel", "pre_uut_flow_gate"]
    assert "main_ran" not in ptf_context.locals
    assert "post_ran" not in ptf_context.locals


def test_sequential_model_run_executes_main_and_post():
    model = SequentialProcessModel(
        name="pm_run",
        callbacks={
            "pre_uut": pre_uut_run,
            "main_sequence": main_sequence_step,
            "post_uut": post_uut_step,
            "report": None,
            "database_logging": None,
        },
        cancel_action="end",
    )

    result = model.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert [name for name, _ in result.children] == [
        "pre_uut_run",
        "pre_uut_flow_gate",
        "main_sequence_step",
        "post_uut_step",
    ]
    assert ptf_context.locals["main_ran"] is True
    assert ptf_context.locals["post_ran"] is True

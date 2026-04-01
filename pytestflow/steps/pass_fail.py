from pytestflow.core.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core.utils import get_data_for_gui
from pytestflow.steps.common import get_metadata_from_prefect_context
from typing import Callable


class PassFailStep(StepWrapper):
    def __init__(self, fn, *, name=None, autowire=True, **task_kwargs):
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.step_type = "pass_fail"


    def _run(self, *args, **kwargs):
        # Executes inside the Prefect task created by StepWrapper
        value = super()._run(*args, **kwargs)

        passed = bool(value)

        result_data = {
            "step_status": "passed" if passed else "failed",
            "output": value,
            "step_type": self.step_type,
        }

        result_data.update(self.get_meta_info())
        result_data.update(get_metadata_from_prefect_context())

        # Send End data to GUI
        get_data_for_gui(self, result_data.get("end_time"), result_data)

        return (
            PyTestflowPassed(ptf_result=result_data)
            if passed
            else PyTestflowFailed(ptf_result=result_data, message=f"{self.name} failed")
        )


def pass_fail_step(*, name=None, autowire=True, **task_kwargs):
    """
    Decorator factory for pass/fail steps.
    """
    def decorator(fn: Callable):
        # IMPORTANT: already task-wrapped by StepWrapper
        return PassFailStep(fn, name=name, autowire=autowire, **task_kwargs)
    return decorator

from prefect.artifacts import create_markdown_artifact
from pytestflow.core.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core.utils import get_data_for_gui
from pytestflow.steps.common import get_metadata_from_prefect_context
from typing import Callable
import re


class StringCheckStep(StepWrapper):
    def __init__(self, fn, *, expected, match="exact", case_sensitive=True,
                 name=None, autowire=True, **task_kwargs):
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.expected = expected
        self.match = match
        self.case_sensitive = case_sensitive
        self.step_type = "string_check"

    def _run(self, *args, **kwargs):
        actual = super()._run(*args, **kwargs)

        if not isinstance(actual, str):
            raise TypeError(f"Expected string output, got {type(actual)}")

        compare_actual = actual if self.case_sensitive else actual.lower()
        compare_expected = self.expected if self.case_sensitive else self.expected.lower()

        if self.match == "exact":
            passed = compare_actual == compare_expected
        elif self.match == "contains":
            passed = compare_expected in compare_actual
        else:
            raise ValueError(f"Unsupported match mode: {self.match}")

        result_data = {
            "step_status": "passed" if passed else "failed",
            "output": actual,
            "expected": self.expected,
            "match": self.match,
            "case_sensitive": self.case_sensitive,
            "step_type": self.step_type,
        }

        result_data.update(self.get_meta_info())
        result_data.update(get_metadata_from_prefect_context())

        # Send End data to GUI
        get_data_for_gui(self, result_data.get("end_time"), result_data)


        # Prefect UI artifact (best-effort)
        try:
            safe_step_name = re.sub(r"[^a-z0-9\\-]", "-", self.name.lower())
            artifact_md = (
                f"### Step: `{self.name}`\n"
                f"- **Actual:** `{actual}`\n"
                f"- **Expected:** `{self.expected}`\n"
                f"- **Match mode:** `{self.match}`\n"
                f"- **Status:** {'✅ PASSED' if passed else '❌ FAILED'}"
            )
            create_markdown_artifact(
                key=f"result-{safe_step_name}",
                markdown=artifact_md,
                description=f"String check for `{self.name}`",
            )
        except Exception:
            # runtime might not support artifacts or not be in task context
            pass

        return (
            PyTestflowPassed(ptf_result=result_data)
            if passed
            else PyTestflowFailed(ptf_result=result_data, message=f"{self.name} failed")
        )


def string_check_step(*, expected, match="exact", case_sensitive=True,
                      name=None, autowire=True, **task_kwargs):
    """
    Decorator factory for string check steps.
    """
    def decorator(fn: Callable):
        # IMPORTANT: already task-wrapped by StepWrapper
        return StringCheckStep(
            fn,
            expected=expected,
            match=match,
            case_sensitive=case_sensitive,
            name=name,
            autowire=autowire,
            **task_kwargs,
        )
    return decorator

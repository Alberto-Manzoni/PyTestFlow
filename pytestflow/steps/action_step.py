# pytestflow/steps/action_step.py

from prefect.artifacts import create_markdown_artifact
from pytestflow.core.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowDone, PyTestflowError
from pytestflow.core.utils import get_data_for_gui
from pytestflow.steps.common import get_metadata_from_prefect_context
from datetime import datetime
import re


class ActionStep(StepWrapper):
    def __init__(self, fn, *, name=None, store_as=None, autowire=True, **task_kwargs):
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.store_as = store_as
        self.step_type = "action"


    def _run(self, *args, **kwargs):
        from pytestflow.core.context import ptf_context

        try:
            # Execute user code (inside the Prefect task created by StepWrapper)
            result = super()._run(*args, **kwargs)

            # Optionally store the result in the context
            if self.store_as:
                ptf_context.locals[self.store_as] = result

            result_data = {
                "step_status": "done",
                "output": result,
                "step_type": self.step_type,
                "pytestflow_timestamp": datetime.utcnow().isoformat(),
                "store_as": self.store_as,
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
                    f"- **Output:** `{result}`\n"
                    f"- **Stored as:** `{self.store_as or 'None'}`\n"
                    f"- **Status:** ✅ DONE"
                )
                create_markdown_artifact(
                    key=f"result-{safe_step_name}",
                    markdown=artifact_md,
                    description=f"Action result for `{self.name}`",
                )
            except Exception:
                pass

            return PyTestflowDone(
                ptf_result=result_data,
                result=result,
                message="Action step completed",
            )

        except Exception as e:
            result_data = {
                "step_status": "error",
                "error": str(e),
                "step_type": "action",
                "pytestflow_timestamp": datetime.utcnow().isoformat(),
                "store_as": self.store_as,
            }

            result_data.update(self.get_meta_info())
            # optional: include Prefect metadata even on error (useful)
            result_data.update(get_metadata_from_prefect_context())

            return PyTestflowError(
                ptf_result=result_data,
                message=f"Action step `{self.name}` failed",
                result=None,
            )


def action_step(*, name=None, store_as=None, autowire=True, **task_kwargs):
    """
    Decorator factory for action steps.
    """
    def decorator(fn):
        # IMPORTANT: already task-wrapped by StepWrapper
        return ActionStep(fn, name=name, store_as=store_as, autowire=autowire, **task_kwargs)
    return decorator

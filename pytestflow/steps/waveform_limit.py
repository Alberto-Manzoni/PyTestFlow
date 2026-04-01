from prefect.artifacts import create_markdown_artifact
from pytestflow.core.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core.utils import get_data_for_gui
from pytestflow.steps.common import get_metadata_from_prefect_context
from typing import Callable
import numpy as np
import re


class WaveformLimitStep(StepWrapper):
    def __init__(
        self,
        fn,
        *,
        lower_mask=None,
        upper_mask=None,
        mode="between",
        name=None,
        autowire=True,
        **task_kwargs
    ):
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.lower_mask = lower_mask
        self.upper_mask = upper_mask
        self.mode = mode
        self.step_type = "waveform_limit"

    def _run(self, *args, **kwargs):
        wvf = super()._run(*args, **kwargs)
        x, y = np.array(wvf["x"]), np.array(wvf["y"])

        result_data = {
            "step_status": "done",
            "mode": self.mode,
            "output": {"x": x.tolist(), "y": y.tolist()},
            "violations": [],
            "step_type": self.step_type,
        }

        if self.mode == "ge":
            assert self.lower_mask is not None, "GE mode requires lower_mask"
            lx, ly = zip(*self.lower_mask)
            lower = np.interp(x, lx, ly)
            if np.any(y < lower):
                result_data["violations"].append("below_lower_mask")
                result_data["step_status"] = "failed"
            else:
                result_data["step_status"] = "passed"

        elif self.mode == "le":
            assert self.upper_mask is not None, "LE mode requires upper_mask"
            ux, uy = zip(*self.upper_mask)
            upper = np.interp(x, ux, uy)
            if np.any(y > upper):
                result_data["violations"].append("above_upper_mask")
                result_data["step_status"] = "failed"
            else:
                result_data["step_status"] = "passed"

        elif self.mode == "between":
            assert self.lower_mask and self.upper_mask, "BETWEEN requires both masks"
            lx, ly = zip(*self.lower_mask)
            ux, uy = zip(*self.upper_mask)
            lower = np.interp(x, lx, ly)
            upper = np.interp(x, ux, uy)
            below = y < lower
            above = y > upper
            if np.any(below):
                result_data["violations"].append("below_lower_mask")
            if np.any(above):
                result_data["violations"].append("above_upper_mask")
            result_data["step_status"] = "passed" if not (np.any(below) or np.any(above)) else "failed"

        elif self.mode == "outside":
            assert self.lower_mask and self.upper_mask, "OUTSIDE requires both masks"
            lx, ly = zip(*self.lower_mask)
            ux, uy = zip(*self.upper_mask)
            lower = np.interp(x, lx, ly)
            upper = np.interp(x, ux, uy)
            outside = (y < lower) | (y > upper)
            if np.any(~outside):  # Any point INSIDE invalidates
                result_data["violations"].append("inside_forbidden_zone")
                result_data["step_status"] = "failed"
            else:
                result_data["step_status"] = "passed"

        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        result_data.update(self.get_meta_info())
        result_data.update(get_metadata_from_prefect_context())

        # Send End data to GUI
        get_data_for_gui(self, result_data.get("end_time"), result_data)


        # Prefect UI artifact (best-effort)
        try:
            safe_step_name = re.sub(r"[^a-z0-9\\-]", "-", self.name.lower())
            artifact_lines = [
                f"### Step: `{self.name}`",
                f"- **Mode:** `{self.mode}`",
                f"- **Status:** {'✅ PASSED' if result_data['step_status'] == 'passed' else '❌ FAILED'}",
                "",
            ]

            if result_data["step_status"] != "passed":
                v_list = result_data["violations"]
                artifact_lines.append(f"- **Violations:** {', '.join(v_list[:10]) or 'none'}")
                if len(v_list) > 10:
                    artifact_lines.append(
                        f"- ... and {len(v_list) - 10} more. See full logs or database for detail."
                    )

            create_markdown_artifact(
                key=f"result-{safe_step_name}",
                markdown="\n".join(artifact_lines),
                description=f"Waveform limit check for `{self.name}`",
            )
        except Exception:
            pass

        return (
            PyTestflowPassed(ptf_result=result_data)
            if result_data["step_status"] == "passed"
            else PyTestflowFailed(ptf_result=result_data, message=f"{self.name} failed")
        )


def waveform_limit_step(*, lower_mask=None, upper_mask=None, mode="between",
                        name=None, autowire=True, **task_kwargs):
    """
    Decorator factory for waveform limit steps.
    """
    def decorator(fn: Callable):
        # IMPORTANT: already task-wrapped by StepWrapper
        return WaveformLimitStep(
            fn,
            lower_mask=lower_mask,
            upper_mask=upper_mask,
            mode=mode,
            name=name,
            autowire=autowire,
            **task_kwargs,
        )
    return decorator

from prefect.artifacts import create_markdown_artifact
from pytestflow.core.core import StepWrapper
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed
from pytestflow.core.utils import get_data_for_gui
from pytestflow.steps.common import get_metadata_from_prefect_context
from typing import Callable
import pandas as pd
import re


class DFNumericLimitsStep(StepWrapper):
    def __init__(self, fn, *, limits_df: pd.DataFrame, name=None, autowire=True, **task_kwargs):
        super().__init__(fn, name=name, autowire=autowire, **task_kwargs)
        self.limits_df = limits_df
        self.step_type = "df_numeric_limits"


    def _run(self, *args, **kwargs):
        values = super()._run(*args, **kwargs)

        if not isinstance(values, (dict, pd.Series)):
            raise TypeError("Return value must be dict or pd.Series")

        results = []
        overall_status = "passed"

        for _, row in self.limits_df.iterrows():
            varname = row["name"]
            try:
                val = values[varname]
                limit = row["limit"]
                mode = row["mode"]

                if mode == "ge":
                    status = "passed" if val >= limit else "failed"
                elif mode == "le":
                    status = "passed" if val <= limit else "failed"
                elif mode == "between":
                    low, high = limit
                    status = "passed" if low <= val <= high else "failed"
                elif mode == "outside":
                    low, high = limit
                    status = "passed" if val < low or val > high else "failed"
                else:
                    raise ValueError(f"Unsupported mode: {mode}")

                if status != "passed":
                    overall_status = "failed"

                result = {
                    "name": varname,
                    "value": val,
                    "limit": limit,
                    "mode": mode,
                    "step_status": status,
                }

            except Exception as e:
                result = {
                    "name": varname,
                    "step_status": "error",
                    "error": str(e),
                }
                overall_status = "failed"

            results.append(result)

        result_data = {
            "step_status": overall_status,
            "output": values,
            "per_variable": results,
            "step_type": self.step_type,
        }

        result_data.update(self.get_meta_info())
        result_data.update(get_metadata_from_prefect_context())

        # Send End data to GUI
        get_data_for_gui(self, result_data.get("end_time"), result_data)


        # Prefect UI artifact (best-effort)
        try:
            safe_step_name = re.sub(r"[^a-z0-9\\-]", "-", self.name.lower())
            md_lines = [
                f"### Step: `{self.name}`",
                f"- **Status:** {'✅ PASSED' if overall_status == 'passed' else '❌ FAILED'}",
                "",
            ]

            if overall_status == "failed":
                failed_results = [r for r in results if r.get("step_status") != "passed"]
                md_lines += [
                    f"**{len(failed_results)}** variable(s) failed limits.",
                    "",
                    "| Variable | Value | Limit | Mode | Status |",
                    "|---|---|---|---|---|",
                ]
                for r in failed_results[:10]:
                    md_lines.append(
                        f"| {r.get('name')} | {r.get('value', 'NA')} | {r.get('limit', 'NA')} | "
                        f"{r.get('mode', 'NA')} | {r.get('step_status', 'error')} |"
                    )
                if len(failed_results) > 10:
                    md_lines.append(
                        f"\n… and **{len(failed_results) - 10} more**. See database/report for full details."
                    )

            create_markdown_artifact(
                key=f"result-{safe_step_name}",
                markdown="\n".join(md_lines),
                description=f"DataFrame numeric limits for `{self.name}`",
            )
        except Exception:
            pass

        return (
            PyTestflowPassed(ptf_result=result_data)
            if overall_status == "passed"
            else PyTestflowFailed(ptf_result=result_data, message=f"{self.name} failed")
        )


def df_numeric_limits_step(*, limits_df: pd.DataFrame, name=None, autowire=True, **task_kwargs):
    """
    Decorator factory for DataFrame numeric limit steps.
    """
    def decorator(fn: Callable):
        # IMPORTANT: already task-wrapped by StepWrapper
        return DFNumericLimitsStep(
            fn,
            limits_df=limits_df,
            name=name,
            autowire=autowire,
            **task_kwargs,
        )
    return decorator

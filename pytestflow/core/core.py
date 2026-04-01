# core/core.py
from functools import wraps
from datetime import datetime
import uuid
from prefect import task
from pytestflow.core.utils import get_data_for_gui, resolve_args
from pytestflow.core.context import ptf_context  # Import ptf_context for step injection


def safe_getattr(obj, attr):
    """Safe getattr that returns None if attribute is missing or context unavailable."""
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None


class StepWrapper:
    """
    A callable wrapper around a user function that integrates with Prefect @task,
    while capturing runtime metadata (start time, duration, flow/task IDs).
    Also supports user-supplied additional_info for inclusion in ptf_result.
    """

    def __init__(self, fn, name=None, autowire=True, **task_kwargs):
        self.fn = fn
        self.name = name or fn.__name__
        self.static_uuid: uuid.UUID | None = None
        self.autowire = autowire
        self.task_kwargs = task_kwargs

        # Metadata and additional info
        self._stepmeta = {}
        self.additional_info = {}

        # Wrap the function with Prefect's @task
        self.prefect_task = task(name=self.name, **task_kwargs)(self._run)

    def _run(self, *args, **kwargs):
        # Reset metadata before every run
        self._stepmeta = {}
        self.additional_info = {}

        # Start time
        start_time = datetime.utcnow()

        # Inject the current step into ptf_context
        ptf_context.current_step = self

        # Send start to GUI
        get_data_for_gui(self, start_time)

        try:
            # Resolve arguments if autowire is enabled
            if self.autowire:
                args, kwargs = resolve_args(self.fn, args, kwargs)

            # Execute the original function
            result = self.fn(*args, **kwargs)

        finally:
            # Always clear the pointer to avoid leaking across steps
            ptf_context.current_step = None

        # End time and duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Collect core metadata
        self._stepmeta = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_s": duration,
        }

        return result

    def get_meta_info(self):
        """Return collected metadata + any user-supplied additional_info."""
        meta = dict(self._stepmeta) if self._stepmeta else {}
        if self.additional_info:
            meta["additional_info"] = dict(self.additional_info)
        return meta

    def add_additional_info(self, key, value):
        """Add additional information to the step (will be included in ptf_result)."""
        self.additional_info[key] = value

    def __call__(self, *args, **kwargs):
        """Delegate execution to the Prefect task."""
        return self.prefect_task(*args, **kwargs)

    def __getattr__(self, name):
        """
        Delegate attribute access to the Prefect task.
        This allows the StepWrapper to behave like a Prefect task
        (e.g., .fn, .name, .submit, etc.).
        """
        return getattr(self.prefect_task, name)


def step(name=None, autowire=True, **task_kwargs):
    """
    Decorator factory that produces a StepWrapper object.
    Usage:
        @step(name="my_step")
        def foo():
            return 42
    """
    def decorator(fn):
        return StepWrapper(fn, name=name, autowire=autowire, **task_kwargs)
    return decorator

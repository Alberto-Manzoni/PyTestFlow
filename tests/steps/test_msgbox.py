# tests/steps/test_msgbox_step.py
import pytest

# Attempt to import the Qt-based utility; skip the entire module if
# the optional PyQt5 dependency or its system libraries are unavailable.
try:  # pragma: no cover - environment dependent
    from pytestflow.steps.utility import msgbox_step_qt
except Exception:  # noqa: BLE001 - broad to cover missing Qt libs
    pytest.skip("PyQt5 is not installed", allow_module_level=True)
from pytestflow.core.context import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowDone


# Define a msgbox step with timeout and input
@msgbox_step_qt(
    name="ask_user_number",
    message="Please enter a number = 3 or (will auto-close)",
    input_enabled=True,
    timeout=5,  # seconds
    store_as="user_number",
    default="3"
)
def ask_user_number():
    pass  # logic is in decorator


def test_msgbox_step_timeout_behavior():
    # Clear context before test
    ptf_context.locals.clear()

    result = ask_user_number()

    # The result should be a PyTestflowDone
    assert isinstance(result, PyTestflowDone)

    # The output must always be set (user input OR default)
    assert result.ptf_result["output"] in ("3",)

    # Context variable should also match
    assert "user_number" in ptf_context.locals
    assert ptf_context.locals["user_number"] in ("3",)

    # Button pressed should clearly indicate what happened
    assert result.ptf_result["button_pressed"] in ("ok", "cancel", "timeout")

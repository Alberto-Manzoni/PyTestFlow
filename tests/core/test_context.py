import pytest
from pytestflow.core import ptf_context  # ptf_context = PyTestFlow execution context

def test_context_locals_and_globals():
    # Set values
    ptf_context.locals["foo"] = 123
    ptf_context.globals["bar"] = "baz"

    assert ptf_context.locals["foo"] == 123
    assert ptf_context.globals["bar"] == "baz"

    # Reset and check empty
    ptf_context.locals.clear()
    ptf_context.globals.clear()

    assert ptf_context.locals == {}
    assert ptf_context.globals == {}
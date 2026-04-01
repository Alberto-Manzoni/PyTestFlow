import time
from pytestflow.core import step, ptf_context
from pytestflow.core.pytestflow_states import PyTestflowDone
from pytestflow.steps.action_step import action_step

ctx = ptf_context


@step(name="set_variables")
def set_variables():
    ctx.locals["a"] = 5
    ctx.locals["b"] = 10
    ctx.globals["prefix"] = "val"
    time.sleep(0.01)  # simulate work
    return "ok"


@step(name="consume_variables")
def consume_variables():
    a = ctx.locals["a"]
    b = ctx.locals["b"]
    time.sleep(0.01)  # simulate work
    return a + b



@step(name="use_global_and_local")
def use_global_and_local():
    prefix = ctx.globals["prefix"]
    a = ctx.locals["a"]
    time.sleep(0.01)  # simulate work
    return f"{prefix}-{a}"


def test_context_variable_passing():
    ctx.locals.clear()
    ctx.globals.clear()

    assert set_variables() == "ok"
    assert consume_variables() == 15
    assert use_global_and_local() == "val-5"


@action_step(name="store_result", store_as="magic_number")
def store_result():
    return 42


@step(name="double_it")
def double_it(magic_number):
    return magic_number * 2


def test_store_as_and_autowire():
    ctx.locals.clear()

    result = store_result()
    assert isinstance(result, PyTestflowDone)
    assert result.ptf_result["output"] == 42
    assert ctx.locals["magic_number"] == 42
    assert double_it() == 84

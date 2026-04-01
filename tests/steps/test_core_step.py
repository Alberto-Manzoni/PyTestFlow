import pytest
from pytestflow.core import step, ptf_context as ctx
import time

# Reset context before each test
@pytest.fixture(autouse=True)
def clear_context():
    ctx.locals.clear()
    ctx.globals.clear()
    yield
    ctx.locals.clear()
    ctx.globals.clear()

# --- Basic step returning raw output
@step()
def return_constant():
    time.sleep(0.01)  # simulate work
    return 10

def test_basic_step():
    assert return_constant() == 10


# --- Autowire step
@step(autowire=True)
def double_from_context(input_value):
    time.sleep(0.01)  # simulate work
    return input_value * 2

def test_autowire_step():
    ctx.locals["input_value"] = 21
    time.sleep(0.01)  # ensure context is set before call
    assert double_from_context() == 42


# --- Manual access to context inside the function
@step()
def multiply_context_value_by(multiplier):
    value = ctx.locals["input_value"]
    time.sleep(0.01)
    return value * multiplier

def test_manual_context_access():
    ctx.locals["input_value"] = 7
    time.sleep(0.01)  
    assert multiply_context_value_by(3) == 21


# --- Fully parameterized (no context use)
@step()
def multiply(a, b):
    time.sleep(0.01)
    return a * b

def test_fully_explicit_step():
    assert multiply(6, 7) == 42

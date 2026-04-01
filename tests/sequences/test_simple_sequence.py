import pytest
from pytestflow.core.sequence import Sequence
from pytestflow.steps.pass_fail import pass_fail_step
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed

# --- Define Decorated Steps ---
@pass_fail_step(name="step_pass")
def step_pass():
    return True

@pass_fail_step(name="step_fail")
def step_fail():
    return False

# --- Test Sequence with Decorated Steps ---
def test_sequence_with_decorated_steps():
    seq = Sequence(name="TestSequence", steps=[step_pass, step_fail])
    result = seq.run(parameters={}, return_state=True)   # returns prefect.State
    
    
    # Verify the sequence result
    assert isinstance(result, PyTestflowFailed)  # Sequence should fail because one step fails
    assert len(result.children) == 2  # Two steps in the sequence
    assert result.children[0][1].ptf_result["step_status"] == "passed"
    assert result.children[1][1].ptf_result["step_status"] == "failed"

import pytest
from pytestflow.core.sequence import Sequence
from pytestflow.steps.action_step import action_step
from pytestflow.steps.pass_fail import pass_fail_step
from pytestflow.core.context import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowPassed

# Define a simple subsequence
def create_subseq():
    @pass_fail_step(name="always_pass")
    def always_pass():
        return True

    return Sequence(name="SubSeq", steps=[always_pass])

# Call it from an action step
@action_step(name="run_subseq_and_store", store_as="subseq_result")
def run_subseq_and_store():
    subseq = create_subseq()
    result = subseq.run(return_state=True)
    return result  # This will be stored into ptf_context.locals["subseq_result"]

# Parent sequence
def test_call_subseq_in_action_step():
    seq = Sequence(name="MainSeq", steps=[run_subseq_and_store])
    result = seq.run(return_state=True)

    assert isinstance(result, PyTestflowPassed)
    assert "subseq_result" in ptf_context.locals
    assert ptf_context.locals["subseq_result"].name == "Passed"

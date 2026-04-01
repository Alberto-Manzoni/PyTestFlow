import pytest
from pytestflow.core.sequence import Sequence
from pytestflow.steps.pass_fail import pass_fail_step
from pytestflow.steps.string_check import string_check_step
from pytestflow.steps.action_step import action_step
from pytestflow.core.context import ptf_context
from pytestflow.core.pytestflow_states import PyTestflowPassed, PyTestflowFailed


@action_step(name="store_in_parent", store_as="parent_value")
def store_in_parent():
    return "value_from_parent"


def create_subsequence(allow_parent_mutation=False):
    @action_step(name="store_in_subseq", store_as="subseq_value")
    def store_in_subseq():
        return "value_from_subseq"

    @action_step(name="use_parent_value", store_as="derived_from_parent")
    def use_parent_value():
        parent_value = ptf_context.locals["__caller__"].get("parent_value", "MISSING")
        try : # attempt to write back to parent context if allowed
            write_to_parent_locals=f"subseq saw: {parent_value}"
            ptf_context.locals["__caller__"]["derived_from_parent"] = write_to_parent_locals
        except :
            pass # if not allowed to mutate parent, this will fail silently
        return f"subseq saw: {parent_value}"

    @string_check_step(
        name="check_derived_value",
        expected="subseq saw: value_from_parent",
        match="exact"
    )
    def check_derived_value():
        return ptf_context.locals.get("derived_from_parent", "NO VALUE")

    @pass_fail_step(name="subseq_passfail")
    def subseq_passfail():
        return True

    return Sequence(
        name="SubSequence",
        steps=[
            store_in_subseq,
            use_parent_value,
            check_derived_value,
            subseq_passfail,
        ],
        allow_parent_mutation=allow_parent_mutation
    )


@pass_fail_step(name="parent_passfail")
def parent_passfail():
    return True


def test_subsequence_without_mutation():
    subseq = create_subsequence()  # default: allow_parent_mutation=False
    seq = Sequence(name="MainSequence", steps=[
        store_in_parent,
        subseq,
        parent_passfail,
    ])

    result = seq.run(parameters={}, return_state=True)

    assert isinstance(result, (PyTestflowPassed, PyTestflowFailed))
    assert len(result.children) == 3

    # Subsequence result should be OK
    subseq_result = result.children[1][1]
    assert isinstance(subseq_result, PyTestflowPassed)

    # But derived_from_parent should NOT be propagated to parent context
    assert "derived_from_parent" not in ptf_context.locals


def test_subsequence_with_mutation():
    subseq = create_subsequence(allow_parent_mutation=True)
    seq = Sequence(name="MainSequence", steps=[
        store_in_parent,
        subseq,
        parent_passfail,
    ])

    result = seq.run(parameters={}, return_state=True)

    assert isinstance(result, (PyTestflowPassed, PyTestflowFailed))
    assert len(result.children) == 3

    # Subsequence result should be OK
    subseq_result = result.children[1][1]
    assert isinstance(subseq_result, PyTestflowPassed)

    # derived_from_parent should now be visible in parent context
    assert ptf_context.locals.get("derived_from_parent") == "subseq saw: value_from_parent"
    assert subseq_result.children[0][1].result() == "value_from_subseq"

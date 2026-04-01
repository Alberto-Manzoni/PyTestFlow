from pytestflow.core.sequence import TestSequence
from pytestflow.core import ptf_context
from pytestflow.steps.action_step import action_step
from pytestflow.steps.flow_control import flow_control_step
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.pass_fail import pass_fail_step


@numeric_limit_step(
    name="measure_3v3",
    limit=(2.7, 3.3),
    mode="between",
    store_as="branching_3v3_value",
)
def measure_3v3():
    # Example value; in real benches this could come from a DMM or PSU readback.
    return 2.95


@flow_control_step(name="branch_on_3v3")
def branch_on_3v3():
    value = ptf_context.locals.get("branching_3v3_value")

    if value is None:
        return {"decision": "next", "reason": "missing_3v3_value", "next_step": "next"}

    if value < 3.0:
        return {
            "decision": "run_deep_voltage_checks",
            "reason": "value_below_3v0",
            "measurement": value,
            "next_step": "next",
        }

    ptf_context.locals["_ptf_next_step"] = "branch_resume_marker"
    return {
        "decision": "skip_deep_voltage_checks",
        "reason": "value_at_or_above_3v0",
        "measurement": value,
        "next_step": "branch_resume_marker",
    }


def create_deep_voltage_subsequence() -> TestSequence:
    @action_step(name="deep_voltage_context_note")
    def deep_voltage_context_note():
        value = ptf_context.locals.get("__caller__", {}).get("branching_3v3_value")
        return f"Running deeper checks because 3V3 measured {value}V (< 3.0V)"

    @pass_fail_step(name="deep_voltage_checks_pass")
    def deep_voltage_checks_pass():
        return True

    return TestSequence(
        name="DeepVoltageSubsequence",
        setup_steps=[],
        main_steps=[deep_voltage_context_note, deep_voltage_checks_pass],
        cleanup_steps=[],
    )


@action_step(name="branch_resume_marker")
def branch_resume_marker():
    value = ptf_context.locals.get("branching_3v3_value")
    return f"Flow resumed after branch decision. 3V3 measurement={value}"


@pass_fail_step(name="final_status_check")
def final_status_check():
    return True


def main_sequence() -> TestSequence:
    return TestSequence(
        name="FlowControlIfBranchSequence",
        setup_steps=[],
        main_steps=[
            measure_3v3,
            branch_on_3v3,
            create_deep_voltage_subsequence(),
            branch_resume_marker,
            final_status_check,
        ],
        cleanup_steps=[],
    )


PROCESS_HOOKS = {
    "main_sequence": main_sequence,
}

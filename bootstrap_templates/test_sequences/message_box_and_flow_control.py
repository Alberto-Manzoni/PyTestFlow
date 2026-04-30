from pytestflow.core.sequence import TestSequence
from pytestflow.core import ptf_context
from pytestflow.steps.message_pop_up import message_pop_up_step
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.pass_fail import pass_fail_step
from pytestflow.steps.flow_control import flow_control_step


@message_pop_up_step(
    name="operator_confirmation",
    title="Operator Check",
    msg="Confirm fixture and DUT are connected, then press Continue.",
    buttons=["Continue", "Cancel"],
    show_response_box=False,
    store_as="operator_confirmation_response",
)
def operator_confirmation():
    return "Operator confirmed bench is ready"


@flow_control_step(name="check_operator_confirmation", next_steps={0: "end", 1: "next"})
def check_operator_confirmation():
    value = ptf_context.locals.get("operator_confirmation_response")
    return value["button"] == "Continue"


@pass_fail_step(name="power_good_check")
def power_good_check():
     
    # Typical use case: a digital status pin or a single readiness condition.
    return True


@numeric_limit_step(name="vcore_voltage_check", limit=(1.0, 1.3), mode="between")
def vcore_voltage_check():
    # Typical use case: one scalar analog measurement against limits.
    return 1.15


def main_sequence() -> TestSequence:
    return TestSequence(
        name="MessageBoxAndFlowControl",
        setup_steps=[],
        main_steps=[
            operator_confirmation,
            check_operator_confirmation,
            power_good_check,
            vcore_voltage_check,
        ],
        cleanup_steps=[],
    )


PROCESS_HOOKS = {
    "main_sequence": main_sequence,
}

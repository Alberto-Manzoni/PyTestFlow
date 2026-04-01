from pytestflow.core.sequence import TestSequence
from pytestflow.steps.message_pop_up import message_pop_up_step
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.pass_fail import pass_fail_step


@message_pop_up_step(
    name="ask_serial_number",
    title="User Input",
    msg="Enter serial number",
    buttons=["Run", "Cancel"],
    show_response_box=True,
)
def ask_serial_number():
    return "Operator input captured"


@numeric_limit_step(name="vcore_voltage_check", limit=(1.0, 1.3), mode="between")
def vcore_voltage_check():
    return 1.18


@pass_fail_step(name="power_good_check")
def power_good_check():
    return True


def motherboard_sequence() -> TestSequence:
    return TestSequence(
        name="MotherboardSmokeSequence",
        setup_steps=[],
        main_steps=[ask_serial_number, vcore_voltage_check, power_good_check],
        cleanup_steps=[],
    )


PROCESS_HOOKS = {
    "main_sequence": motherboard_sequence,
}


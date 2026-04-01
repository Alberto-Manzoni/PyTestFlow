from pytestflow.core.sequence import TestSequence
from pytestflow.steps.numeric_limit import numeric_limit_step
from pytestflow.steps.pass_fail import pass_fail_step


@numeric_limit_step(name="measure_vcore", limit=(1.0, 1.3), mode="between")
def measure_vcore():
    return 1.15


@pass_fail_step(name="functional_check")
def functional_check():
    return True


def main_sequence() -> TestSequence:
    return TestSequence(
        name="BasicSequence",
        setup_steps=[],
        main_steps=[measure_vcore, functional_check],
        cleanup_steps=[],
    )


PROCESS_HOOKS = {
    "main_sequence": main_sequence,
}


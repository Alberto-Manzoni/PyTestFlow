from pytestflow.core.context import ptf_context
from pytestflow.core.sequence import Sequence
from pytestflow.steps.string_check import string_check_step

# --- Step that builds a string from context parameters
@string_check_step(
    name="check_signal_routing",
    expected="dut=DUT123, siggen=PSF-B",
    match="exact"
)
def check_signal_routing():
    dut = ptf_context.locals["dut"]
    siggen = ptf_context.locals["siggen"]
    return f"dut={dut}, siggen={siggen}"

def test_parameter_merging_between_default_and_runtime():
    # Sequence with default parameters
    seq = Sequence(
        name="rx_afe_test",
        steps=[check_signal_routing],
        default_parameters={"dut": "DUT123", "siggen": "PSF-A"}  # Will be partially overridden
    )

    # Override siggen at runtime
    result = seq.run(parameters={"siggen": "PSF-B"}, return_state=True)

    # Ensure sequence passed
    assert result.name == "Passed"

    # Optional: double-check the exact string output
    step_result = result.children[0][1]
    assert step_result.ptf_result["output"] == "dut=DUT123, siggen=PSF-B"

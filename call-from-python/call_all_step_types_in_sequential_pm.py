from all_step_types_sequence import all_step_types_sequence
from bootstrap_templates.process_models.sequential_model import SequentialProcessModel
from pytestflow.steps.action_step import action_step
from pytestflow.core.context import ptf_context
from pytestflow.core.sequence import Sequence


@action_step(name="pre_uut_prompt")
def pre_uut_prompt():
    """Pretend to prepare the device under test."""
    print("🔌 Connecting DUT ...")
    return "ready"


@action_step(name="simple_report", store_as="report_summary")
def simple_report():
    """Print a short summary based on the main result."""
    main_state = ptf_context.locals["main_result"]
    print(f"[Report] Overall result: {main_state.name}")
    return main_state.name


report_sequence = Sequence(name="ReportSequence", steps=[simple_report])


if __name__ == "__main__":
    seq = all_step_types_sequence()
    process_model = SequentialProcessModel(
        name="AllStepTypesPM",
        pre_uut_callback=pre_uut_prompt,
        main_callback=seq,
        report_callback=report_sequence,
    )

    result = process_model.run(return_state=True)
    print(f"\n🎯 Final Process Model result: {result.name}")

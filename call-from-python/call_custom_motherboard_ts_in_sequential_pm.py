from motherboard_test_sequence_custom import motherboard_sequence
from bootstrap_templates.process_models.sequential_model import SequentialProcessModel
from pytestflow.core.context import ptf_context
from bootstrap_templates.process_models.reporting.html_report import generate_html_report

# Optional: dummy report step
from pytestflow.core.sequence import Sequence
from pytestflow.steps.action_step import action_step

@action_step(name="generate_report", store_as="report_done")
def generate_report():
    main_result = ptf_context.locals["main_result"]
    print(f"[📝 Report] Main sequence result: {main_result.name}")

    # Generate HTML report
    report_path = generate_html_report(
        root_state=main_result,
        title="MotherboardTestSequence"
    )
    print(f"[📝 Report] Saved at {report_path}")
    return str(report_path)

report_sequence = Sequence(name="ReportSequence", steps=[generate_report])

if __name__ == "__main__":
    # Instantiate the main test sequence
    main_seq = motherboard_sequence()

    # Build the Process Model with callbacks
    process_model = SequentialProcessModel(
        name="MotherboardPM",
        pre_uut_callback=None,                     # Prompt removed for headless run
        main_callback=main_seq,                    # Required
        report_callback=report_sequence,           # Optional
        database_callback=None                     # Optional
    )

    # Run the Process Model
    result = process_model.run(return_state=True)

    print(f"\n🎯 Final Process Model result: {result.name}")

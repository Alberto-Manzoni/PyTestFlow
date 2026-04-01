from motherboard_test_sequence import motherboard_sequence
from bootstrap_templates.process_models.sequential_model import SequentialProcessModel
from pytestflow.steps.utility  import msgbox_step_qt
from pytestflow.core.context import ptf_context
from bootstrap_templates.process_models.reporting.html_report import generate_html_report
from bootstrap_templates.process_models.reporting.postsgre_dblogging import log_results_to_db       
from prefect import flow



# Optional: Pre-UUT message box prompt
@msgbox_step_qt(
    name="pre_uut_prompt",
    message="⚠️ Connect DUT and click OK to start motherboard test sequence.",
    timeout=10,
    default="ok",
    
)
def pre_uut_prompt():
    return "DUT connected"

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

@action_step(name="log_to_pg", store_as="pg_log_done")
def log_to_postgres():
    main_result = ptf_context.locals["main_result"]
    db_conn_str = "postgresql://ptf_user:ptf_pass@localhost:5432/postgres"
    log_results_to_db(main_result, db_conn_str)
    print("[🗃️ DB] Logged results to PostgreSQL")
    return "logged"


report_sequence = Sequence(name="ReportSequence", steps=[generate_report])
logging_db = Sequence(name="LogToDb", steps=[log_to_postgres])


@flow(name="Motherboard Sequential PM")
def run_motherboard_demo():
    main_seq = motherboard_sequence()
    process_model = SequentialProcessModel(
        name="MotherboardPM",
        # pre_uut_callback=pre_uut_prompt,
        main_callback=main_seq,
        # report_callback=report_sequence,
        database_callback=None,
    )
    return process_model.run(return_state=True)

if __name__ == "__main__":        
    result = run_motherboard_demo()
    print(f"\n🎯 Final result: {result.name}")

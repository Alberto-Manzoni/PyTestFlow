import pickle
from pytestflow.core.sequence import Sequence
from pytestflow.steps.action_step import action_step
from pytestflow.core.context import ptf_context
from pytestflow.steps.flow_control import flow_control_step
from pytestflow.steps.message_pop_up import message_pop_up_step
from pytestflow.backend.report_manager import report_manager
import sys
from pathlib import Path

# path relativo alla cartella che contiene reporting
PROCESS_MODELS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROCESS_MODELS_DIR))

# ora questo funziona come vuoi
from reporting.html_report import generate_html_report


# ---------------------
# DEFAULT CALLBACKS
# ---------------------

# ✅ Pre-UUT: ask user to enter SN
@message_pop_up_step(
    show_response_box=True,
    title="User Input",
    msg="Enter Serial Number",
    buttons=["Run", "Cancel"],
    name="pre_uut_callback"
)
def pre_uut_callback():
    pass  # logic handled by decorator

# ✅ Post-UUT: (placeholder)
@action_step(name="post_uut_callback")
def post_uut_callback():
    print("📝 Post-UUT executed.")
    pass

# ✅ Report (placeholder)
@action_step(name="report_callback")
def report_callback():
    # DEBUG save state snapshot for debugging / uncomment if needed
    # with open("C:\\PRIVATO\\SW\\PyTestFlow\\PyTestFlow-main\\test_reports\\dataf_for_report.pkl", "wb") as f:
    #     pickle.dump(ptf_context.locals, f)

    main_results = ptf_context.locals.get("main_results") or ptf_context.locals.get("main_result")
    if main_results is None:
        raise ValueError("Main sequence results are missing. Expected 'main_results' in context.")
    
    _pre_uut_user_response =  ptf_context.locals.get("_pre_uut_user_response")
    sn = ""
    if _pre_uut_user_response:
        sn = _pre_uut_user_response.get("text", "")
    
    report_path = generate_html_report(sn, main_results)
    
    report_manager.set_last_report(report_path)

    print(f"📝 HTML report generated: {report_path}")
    return report_path

# ✅ Database logging (placeholder)
@action_step(name="database_logging_callback")
def database_logging_callback():
    print("💾 Database logging executed.")
    return "DB logging done"



DEFAULT_CALLBACKS = {
    "pre_uut": pre_uut_callback,
    "main_sequence": None,           # mandatory
    "post_uut": post_uut_callback,
    "report": report_callback,
    "database_logging": database_logging_callback,
}


class SequentialProcessModel(Sequence):
    def __init__(
        self,
        name: str = "SequentialProcessModel",
        callbacks: dict | None = None,
        cancel_action: str = "end",
    ):
        # Validate main sequence presence
        callbacks = callbacks or {}
        # Merge with defaults
        self.callbacks = {**DEFAULT_CALLBACKS, **callbacks}
        self.cancel_action = cancel_action
        self._pre_uut_step_name = None

        assert self.callbacks["main_sequence"] is not None, "Main Seq callback must be provided."

        pre_uut_step = self.callbacks.get("pre_uut")
        if pre_uut_step is not None:
            self._pre_uut_step_name = getattr(pre_uut_step, "name", getattr(pre_uut_step, "__name__", "pre_uut"))

        @flow_control_step(name="pre_uut_flow_gate")
        def pre_uut_flow_gate():
            user_response = ptf_context.locals.get("_pre_uut_user_response")
            button = self._extract_button_from_response(user_response)

            if button == "cancel":
                ptf_context.locals["_ptf_next_step"] = self.cancel_action
                return {
                    "decision": self.cancel_action,
                    "reason": "pre_uut_cancel",
                    "user_response": user_response,
                }

            return {
                "decision": "next",
                "reason": "pre_uut_continue",
                "user_response": user_response,
            }

        steps = []
        if pre_uut_step is not None:
            steps.append(pre_uut_step)
            steps.append(pre_uut_flow_gate)

        main_sequence = self.callbacks["main_sequence"]

        @action_step(name="main_sequence_step", store_as="main_results")
        def main_sequence_step():
            if isinstance(main_sequence, Sequence):
                main_state = main_sequence.run(return_state=True)
            elif hasattr(main_sequence, "run"):
                main_state = main_sequence.run(return_state=True)
            else:
                try:
                    main_state = main_sequence(return_state=True)
                except TypeError:
                    main_state = main_sequence()

            # Backward compatibility for existing integrations that still read `main_result`.
            ptf_context.locals["main_result"] = main_state
            ptf_context.locals["__last_result__"] = main_state
            return main_state

        steps.append(main_sequence_step)
        if self.callbacks.get("post_uut") is not None:
            steps.append(self.callbacks["post_uut"])
        if self.callbacks.get("report") is not None:
            steps.append(self.callbacks["report"])
        if self.callbacks.get("database_logging") is not None:
            steps.append(self.callbacks["database_logging"])

        # Build Sequence
        super().__init__(name=name, steps=steps, apply_throttle=False)

    def _extract_button_from_response(self, user_response) -> str | None:
        if isinstance(user_response, dict):
            button = user_response.get("button")
            if button is not None:
                return str(button).strip().lower()
        if user_response is None:
            return None
        return str(user_response).strip().lower()

    def _extract_pre_uut_user_response(self, state):
        ptf_result = getattr(state, "ptf_result", {}) or {}
        if "user_response" in ptf_result:
            return ptf_result.get("user_response")

        output = ptf_result.get("output")
        if isinstance(output, dict):
            if "user_response" in output:
                return output.get("user_response")
            if "button" in output:
                return output
        return output

    def _exec_step(self, step_fn):
        name, state = super()._exec_step(step_fn)
        if self._pre_uut_step_name and name == self._pre_uut_step_name:
            ptf_context.locals["_pre_uut_user_response"] = self._extract_pre_uut_user_response(state)
        return name, state



from bootstrap_templates.process_models.reporting.html_jinja_report import generate_html_jinja_report

class DummyState:
    def __init__(self, *, name, state_type='COMPLETED', message='', ptf_result=None, children=None):
        self.name = name
        self.type = state_type
        self.message = message
        self.ptf_result = ptf_result or {}
        self.children = children or []

child_pass = DummyState(name='passed', ptf_result={'step_name': 'measure_voltage', 'step_type': 'numeric_limit', 'value': 12.1})
child_fail = DummyState(name='failed', message='Threshold exceeded', ptf_result={'step_name': 'check_current', 'step_type': 'pass_fail', 'value': False})
root = DummyState(name='completed', children=[('measure_voltage', child_pass), ('check_current', child_fail)])

report_path = generate_html_jinja_report('SN-001', root)
print('Report generated at:', report_path)
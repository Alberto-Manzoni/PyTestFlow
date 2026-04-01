# Reporting

Modules that transform aggregated `PyTestflowState` data into JSON or HTML
reports. Reporting flows typically run from the process model's `report`
callback, consuming `ptf_context.locals["main_result"]` to present sequence and
step outcomes captured by Prefect.

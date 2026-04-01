# PyTestFlow Package

This package bundles the runtime building blocks:

- `core`: Prefect-integrated step wrapper, execution context, state classes,
  and sequence/process-model execution.
- `steps`: reusable step decorators built on top of the base `@step` wrapper.
- `flow_utils`: orchestration helpers for conditions and transitions.
- `reporting`: utilities that transform `PyTestflowState` data into JSON or HTML.

Together these modules implement the same model used throughout the repository:
steps are tasks, sequences are flows, and `ptf_context` is the shared channel
for runtime data exchange.

# Test Coverage

Generate a coverage report with:

```bash
PYTHONPATH=. pytest --cov=pytestflow --cov-report=term-missing
```

Each test module exercises a specific part of the current runtime:

| Test File | Focus |
| --- | --- |
| `core/test_context.py` | Shared execution context (`locals`, `globals`, `current_step`). |
| `core/test_states.py` | `PyTestflowState` classes and result payload behavior. |
| `process_models/test_sequential_model_flow_control.py` | `SequentialProcessModel` flow control behavior and callback transitions. |
| `sequences/test_simple_sequence.py` | Basic sequence execution and child result aggregation. |
| `sequences/test_sequence_allsteptypes.py` | Sequence execution with all built-in step categories. |
| `sequences/test_parameters_passing.py` | Merge of `default_parameters` with runtime overrides. |
| `sequences/test_callsubsequence.py` | Nested sequence execution and parent-local mutation rules. |
| `sequences/test_flow_control_sequence.py` | `_ptf_next_step` directives (`next`, `end`, jump by name/index). |
| `sequences/test_sequence_edge_cases.py` | Invalid directives, transition limits, and edge handling. |
| `sequences/test_subsequence_asactionstep.py` | Subsequence invocation wrapped as an action step. |
| `sequences/test_TestSequence.py` | `TestSequence` setup/main/cleanup orchestration. |
| `steps/test_core_step.py` | Base `@step` wrapper, autowiring, and task integration. |
| `steps/test_context_passing.py` | Context-based data exchange and `store_as` usage. |
| `steps/test_df_numeric_limits.py` | Multi-value numeric limits for dict/series data. |
| `steps/test_flow_control.py` | `flow_control_step` metadata and control directives. |
| `steps/test_msgbox.py` | Qt message-box step behavior and timeout/default paths. |
| `steps/test_numeric_limit.py` | Single numeric limit validation. |
| `steps/test_pass_fail.py` | Boolean pass/fail conversion to PyTestFlow states. |
| `steps/test_string_check.py` | String comparison logic and match modes. |
| `steps/test_waveform_limit.py` | Waveform mask checks against upper/lower limits. |

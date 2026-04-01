# PyTestFlow Manifesto

> Redefining test engineering for modern validation labs.

## What is PyTestFlow?

PyTestFlow is a Python-native test executive inspired by NI TestStand and built
on Prefect orchestration.

- Every step is a Prefect task wrapper.
- Every sequence is a Prefect flow.
- Process models orchestrate the Unit Under Test lifecycle around a main
  sequence.

## Philosophy

### 1. Behavior is code, orchestrated

Any Python function can become a step:

```python
@numeric_limit_step(name="check_vdd", limit=1.2, mode="le")
def read_vdd():
    return read_voltage("vdd")
```

The wrapper adds metadata, execution timing, and a standard
`PyTestflowState` result.

### 2. Composable flow hierarchies

```python
main_sequence = TestSequence(
    name="power_up_flow",
    setup_steps=[init_bench],
    main_steps=[read_vdd, read_vcore, functional_check],
    cleanup_steps=[shutdown],
)
```

Subsequences can isolate local context or opt in to controlled parent mutation.

### 3. Process models drive lifecycle, not measurements

```python
SequentialProcessModel(
    name="vt_corner_test",
    callbacks={
        "pre_uut": pre_test_prompt,
        "main_sequence": main_sequence,
        "post_uut": dispose_dut,
        "report": generate_report,
        "database_logging": log_to_postgres,
    },
)
```

This keeps measurement logic independent from pre/post/report plumbing.

### 4. Step types are extensible

Custom decorators can target any domain (RF, power, optical, protocol).
Each step emits structured output that downstream report/database callbacks can
consume.

## Summary

PyTestFlow turns test logic into composable, traceable, data-native flows.

## Core values

Composability. Traceability. CI/CD readiness. Validation-first design.

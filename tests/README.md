# Tests

Automated tests verify the core runtime, sequence orchestration, process-model
flow control, and built-in step decorators.

## Running tests

```bash
PYTHONPATH=. pytest
```

## Coverage

```bash
PYTHONPATH=. pytest --cov=pytestflow --cov-report=term-missing
```

See [test_coverage.md](./test_coverage.md) for a per-module map.

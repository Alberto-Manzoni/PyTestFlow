# PyTestFlow Steps

The `pytestflow.steps` package provides ready-made decorators layered on top of
`pytestflow.core.step`.

See the [project README](../../readme.md) for overview usage.

## Available step decorators

| Decorator | Import path | Purpose |
| --- | --- | --- |
| `numeric_limit_step` | `pytestflow.steps` | Validate one numeric value against a limit/range. |
| `df_numeric_limits_step` | `pytestflow.steps` | Apply numeric limits to multiple values (dict/series). |
| `pass_fail_step` | `pytestflow.steps` | Convert boolean outcome into pass/fail state. |
| `string_check_step` | `pytestflow.steps` | Compare string output with expected value/match mode. |
| `waveform_limit_step` | `pytestflow.steps` | Validate waveform points against lower/upper masks. |
| `flow_control_step` | `pytestflow.steps` | Publish control metadata and steer sequence transitions. |
| `action_step` | `pytestflow.steps.action_step` | Run side-effect actions and optionally `store_as` in context. |
| `message_pop_up_step` | `pytestflow.steps.message_pop_up` | Trigger frontend-driven popup interactions. |
| `msgbox_step_qt` | `pytestflow.steps.utility` | Show local Qt message dialog and capture input. |

## Creating custom steps

```python
from pytestflow.core import step
from pytestflow.core.pytestflow_states import PyTestflowDone


def my_step(name=None):
    def decorator(fn):
        @step(name=name or fn.__name__)
        def wrapper(*args, **kwargs):
            data = fn(*args, **kwargs)
            return PyTestflowDone(ptf_result={"step_status": "done", "output": data})
        return wrapper
    return decorator
```

## Best practices

- Keep step functions small and deterministic when possible.
- Return `PyTestflowState` subclasses for expected test outcomes.
- Use `store_as` and `ptf_context.locals` for explicit handoff between steps.

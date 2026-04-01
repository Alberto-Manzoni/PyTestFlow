# # core/utils.py
from inspect import signature, Parameter
from pytestflow.core.context import ptf_context
import json
from pytestflow.core.runtime_control import runtime_control
    

def get_data_for_gui(step, timestamp, result=None):
    overall_step_result = ''
    status_to_send = 'started'
    info = ""
    if result is not None:
        # means end of step
        status_to_send = 'finished'
        overall_step_result = result['step_status']
        # get info (step type dependant)        
        step_type = result['step_type']
        if step_type == 'action':
            info = json.dumps({"Output": result['output']}, default=str)
        elif step_type == 'numeric_limit':
            info = json.dumps({"Output": result['output'], "limit": result['limit'],"mode": result['mode'] }, default=str)
        if step_type == 'pass_fail':
            info = json.dumps({"Output": result['output']}, default=str)
        elif step_type == 'string_check':
            info = json.dumps({"Output": result['output'],
                               "expected": result['expected'],
                               "match": result['match'],
                               "case_sensitive": result['case_sensitive'] },
                               default=str)  
    data_to_send = {
        "cmd": "update_step_status",
        "args": {
            "StepUUID": str(step.static_uuid),
            "SelectStepOnGUI": True,
            "Status": status_to_send,
            "Result": overall_step_result,
            "Timestamp": timestamp if isinstance(timestamp, str) else timestamp.isoformat(),
            "Info": info
        }
    }

    if step.static_uuid is None:
        print("**************************************************")
        print("step name:", step.name)
        print("**************************************************")

    # Send to FE via runtime_control queue (in-process)
    runtime_control.send_gui_update(data_to_send)



def resolve_args(func, explicit_args, explicit_kwargs):
    """
    Autowires missing parameters from context by name.
    If a parameter is 'ctx', injects the context object.
    """
    sig = signature(func)

    # Early return for parameter-less functions
    if len(sig.parameters) == 0:
        return (), {}

    bound = sig.bind_partial(*explicit_args, **explicit_kwargs)

    for pname, param in sig.parameters.items():
        # Skip *args and **kwargs
        if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            continue

        if pname in bound.arguments:
            continue
        if pname == "ctx":
            bound.arguments[pname] = ptf_context
        elif pname in ptf_context.locals:
            bound.arguments[pname] = ptf_context.locals[pname]
        elif pname in ptf_context.globals:
            bound.arguments[pname] = ptf_context.globals[pname]
        else:
            raise ValueError(f"Could not autowire parameter '{pname}'")

    return bound.args, bound.kwargs

from prefect.states import State
from pydantic import Field
from typing import Optional, List, Tuple, Dict

class PyTestflowState(State):
    """
    Base class for all PyTestFlow states.
    Uses `ptf_result` for internal step data and sets Prefect `.data` field
    to `ptf_result["output"]` if available.
    """
    ptf_result: Dict = Field(default_factory=dict)
    children: Optional[List[Tuple[str, State]]] = Field(default_factory=list)

    def __init__(self, *, ptf_result=None, message=None, children=None, **kwargs):
        ptf_result = ptf_result or {}

        # Set internal .data result from ptf_result["output"]
        data: Any = ptf_result.get("output", None)
        kwargs.setdefault("data", data)  # directly sets self.data

        # Set default type if missing
        kwargs.setdefault("type", "COMPLETED")

        super().__init__(
            message=message,
            **kwargs
        )

        object.__setattr__(self, "ptf_result", ptf_result)
        object.__setattr__(self, "children", children or [])

    def add_child(self, name: str, state: State):
        self.children.append((name, state))

    def summarize(self):
        return {
            "name": self.name,
            "status": self.ptf_result.get("step_status"),
            "children": [name for name, _ in self.children]
        }


class PyTestflowPassed(PyTestflowState):
    def __init__(self, ptf_result=None, message="Step passed", children=None, **kwargs):
        super().__init__(
            name="Passed",
            type="COMPLETED",
            ptf_result=ptf_result,
            message=message,
            children=children,
            **kwargs
        )


class PyTestflowFailed(PyTestflowState):
    def __init__(self, ptf_result=None, message="Step failed", children=None, **kwargs):
        super().__init__(
            name="Failed",
            type="COMPLETED",
            ptf_result=ptf_result,
            message=message,
            children=children,
            **kwargs
        )


class PyTestflowDone(PyTestflowState):
    def __init__(self, ptf_result=None, message="Step done", children=None, **kwargs):
        super().__init__(
            name="Done",
            type="COMPLETED",
            ptf_result=ptf_result,
            message=message,
            children=children,
            **kwargs
        )


class PyTestflowError(PyTestflowState):
    def __init__(self, ptf_result=None, message="Unhandled error", children=None, **kwargs):
        super().__init__(
            name="Error",
            type="CRASHED",
            ptf_result=ptf_result,
            message=message,
            children=children,
            **kwargs
        )

from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, List, Optional


class TestContext:
    """Manages local/global variables and step results for test execution."""

    def __init__(self) -> None:
        self.locals: Dict[str, Any] = {}               # Per-sequence or per-step local vars
        self.globals: Dict[str, Any] = {}              # Shared across all steps
        self.results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # step_name -> list of result dicts
        self.this_context: "Context" = self            # Self-ref (TestStand-style)
        self.contex_created_timestamp: datetime = datetime.now()

    # # The following methods are commented out as they are not used in the current context.
    # def log_result(self, step_name: str, result_dict: Dict[str, Any]) -> None:
    #     """Append a structured result to the results dict."""
    #     self.results[step_name].append(result_dict)

    # def get_last_result(self, step_name: str) -> Optional[Dict[str, Any]]:
    #     """Get last execution result for a given step."""
    #     return self.results[step_name][-1] if self.results[step_name] else None

    # def __repr__(self) -> str:
    #     return (
    #         f"<Context locals={list(self.locals.keys())} "
    #         f"globals={list(self.globals.keys())} "
    #         f"results={len(self.results)}>"
    #     )
    # <=== End of commented-out methods ===>  

    def __repr__(self) -> str:
        return (
            f"<Context locals={list(self.locals.keys())} "
            f"globals={list(self.globals.keys())}>"
        )


# Global singleton instance
ptf_context = TestContext()  # ptf_context = PyTestFlow execution context

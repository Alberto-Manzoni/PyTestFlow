from prefect.context import get_run_context
import warnings

def safe_getattr(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def get_metadata_from_prefect_context():
    metadata = {
        "flow_run_id": None,
        "flow_name": None,
        "task_run_id": None,
        "task_name": None,
    }

    # 1) Get task metadata from run context (works well inside tasks)
    try:
        run_ctx = get_run_context()
        task_run = safe_getattr(run_ctx, "task_run", None)

        metadata["task_run_id"] = safe_getattr(task_run, "id")
        metadata["task_name"]   = safe_getattr(task_run, "name")
    except RuntimeError:
        warnings.warn(
            "Prefect context is unavailable. Metadata enrichment is skipped.",
            RuntimeWarning,
        )
        return metadata

    # 2) Get flow metadata from Prefect runtime (most reliable)
    try:
        from prefect.runtime import flow_run
        metadata["flow_run_id"] = safe_getattr(flow_run, "id")
        metadata["flow_name"]   = safe_getattr(flow_run, "name")
    except Exception:
        # 3) Fallback: try flow_run from context if present
        try:
            run_ctx = get_run_context()
            flow_run_obj = safe_getattr(run_ctx, "flow_run", None)
            metadata["flow_run_id"] = metadata["flow_run_id"] or safe_getattr(flow_run_obj, "id")
            metadata["flow_name"]   = metadata["flow_name"] or safe_getattr(flow_run_obj, "name")
        except Exception:
            pass

    return metadata

# report_html.py
from __future__ import annotations
import os, json, html, re
from datetime import datetime
from typing import Any, Iterable

# ---------- Helpers ----------
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def _safe(s: Any) -> str:
    return html.escape(str(s), quote=True)

def _slug(text: str) -> str:
    text = re.sub(r"\s+", "-", str(text).strip())
    text = re.sub(r"[^a-zA-Z0-9\-_.]+", "", text)
    return text or "item"

def _try_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

def _extract_result(value: Any) -> Any:
    """
    Works with Prefect 3's ResultRecord or plain values.
    - If value has `.result`, return it
    - Else return value
    """
    # Prefect 3 ResultRecord has attribute 'result'
    if hasattr(value, "result"):
        try:
            return getattr(value, "result")
        except Exception:
            pass
    return value

def _extract_children(state: Any) -> list[tuple[str, Any]]:
    """
    Expects PyTestFlow states to hold children as a list[(name, state)].
    If missing, returns [].
    """
    return list(getattr(state, "children", []) or [])

def _extract_message(state: Any) -> str:
    return getattr(state, "message", "") or ""

def _extract_status_name(state: Any) -> str:
    # e.g., PyTestflowPassed.name or fallback from class name
    n = getattr(state, "name", None)
    if n:
        return str(n)
    return state.__class__.__name__

def _extract_type_label(state: Any) -> str:
    # Often "COMPLETED" in your example
    return str(getattr(state, "type", "")) or ""

def _guess_step_label(name: str, state: Any) -> str:
    """
    Prefer ptf_result['step_name'] if available,
    otherwise fallback to Prefect/State-derived names.
    """
    ptf_result = getattr(state, "ptf_result", None)
    if isinstance(ptf_result, dict) and "step_name" in ptf_result:
        return str(ptf_result["step_name"])

    msg = _extract_message(state)
    if name.startswith("<pytestflow.core.sequence.Sequence"):
        m = re.search(r"Sequence\s+(.+?)\s+(passed|failed)", msg, flags=re.I)
        if m:
            return f"{m.group(1)} (subsequence)"
        return "Subsequence"

    return name

def _status_badge(status: str) -> str:
    # simple coloring for badges
    status_upper = status.upper()
    if "PAS" in status_upper:
        cls = "badge-pass"
    elif "FAIL" in status_upper or status_upper == "ERROR":
        cls = "badge-fail"
    else:
        cls = "badge-other"
    return f'<span class="badge {cls}">{_safe(status)}</span>'

# ---------- HTML assembly ----------
CSS = """
<style>
  :root { --fg:#222; --bg:#fff; --muted:#666; --border:#ddd; }
  body { font-family: system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif; color:var(--fg); background:var(--bg); margin:24px; line-height:1.4; }
  h1 { margin:0 0 6px 0; }
  .meta { color:var(--muted); margin-bottom:20px; }
  .summary-table { width:100%; border-collapse: collapse; margin: 8px 0 18px 0; }
  .summary-table th, .summary-table td { padding:8px 10px; border-bottom:1px solid var(--border); vertical-align: top; }
  .summary-table th { text-align:left; background:#fafafa; }
  .row { display:flex; gap:8px; align-items:center; }
  .indent { padding-left: 22px; border-left: 3px solid #f0f0f0; margin: 6px 0 10px 0; }
  .badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:600; }
  .badge-pass { background:#e8f8ee; color:#117a3a; border:1px solid #bfead0; }
  .badge-fail { background:#fdeceb; color:#a1130f; border:1px solid #f3c2bf; }
  .badge-other { background:#eef2ff; color:#283593; border:1px solid #c5cae9; }
  code.inline { background:#f7f7f9; padding:2px 4px; border-radius:4px; }
  details { margin: 6px 0 12px 0; }
  details > summary { cursor: pointer; padding:4px 0; }
  pre { background:#f7f7f9; padding:10px; border-radius:6px; overflow:auto; border:1px solid #ececec; }
  .toc { margin: 14px 0 20px 0; padding:10px; background:#f9fafb; border:1px solid var(--border); border-radius:8px; }
  .toc h3 { margin:0 0 8px 0; }
  .toc ul { margin:0; padding-left: 18px; }
  .toc a { text-decoration:none; }
  a.anchor { color:inherit; text-decoration:none; }
  small.lo { color: var(--muted); }
</style>
"""

JS = """
<script>
  // Expand/Collapse all helpers (optional)
  function expandAll() {
    document.querySelectorAll("details").forEach(d => d.open = true);
  }
  function collapseAll() {
    document.querySelectorAll("details").forEach(d => d.open = false);
  }
</script>
"""

def _render_row_line(idx: int, anchor_id: str, label: str, status_badge_html: str, type_label: str, is_subsequence: bool) -> str:
    # One summary line (table row)
    link = f'<a class="anchor" href="#{anchor_id}">{_safe(label)}</a>'
    sub = "Yes" if is_subsequence else "No"
    return f"""
      <tr>
        <td><small class="lo">{idx:03d}</small></td>
        <td>{link}</td>
        <td>{status_badge_html}</td>
        <td><code class="inline">{_safe(type_label)}</code></td>
        <td><code class="inline">{sub}</code></td>
      </tr>
    """

def _render_detail_block_old(anchor_id: str, label: str, state: Any, depth: int) -> str:
    status = _extract_status_name(state)
    badge = _status_badge(status)
    msg = _extract_message(state)
    type_label = _extract_type_label(state)

    # --- ptf_result extraction ---
    ptf_result = getattr(state, "ptf_result", None)

    ptf_html = ""
    if isinstance(ptf_result, dict):
        rows = []
        for k, v in ptf_result.items():
            rows.append(f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(v)}</td></tr>")
        ptf_html = f"""
        <table class="summary-table" style="margin:8px 0;">
          <thead><tr><th colspan="2">ptf_result</th></tr></thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
        """

    # --- raw result fallback (what Prefect stores) ---
    raw_result = _extract_result(getattr(state, "result", None))
    pretty_res = _try_json(raw_result)
    res_html = f"<pre>{_safe(pretty_res)}</pre>"

    pad = " indent" if depth > 0 else ""
    return f"""
    <div id="{anchor_id}" class="{pad}">
      <div class="row" style="justify-content:space-between;">
        <h3 style="margin:6px 0;">
          {_safe(label)} {badge}
        </h3>
      </div>
      <div class="row" style="gap:14px; margin: 6px 0 6px 0;">
        <div><b>State Type:</b> <code class="inline">{_safe(type_label)}</code></div>
        {"<div><b>Message:</b> " + _safe(msg) + "</div>" if msg else ""}
      </div>

      {ptf_html}

      <details>
        <summary><b>Show raw result</b></summary>
        {res_html}
      </details>
    """

def _render_detail_block(anchor_id: str, label: str, state: Any, depth: int) -> str:
    # PyTestFlow + Prefect state types
    ptf_state_type = state.__class__.__name__   # e.g., PyTestflowPassed
    prefect_state_type = _extract_type_label(state)  # e.g., StateType.COMPLETED
    badge = _status_badge(_extract_status_name(state))
    msg = _extract_message(state)

    # IDs: prefer TaskRun for steps, FlowRun for sequences
    task_run_id = getattr(state, "task_run_id", None)
    flow_run_id = getattr(state, "flow_run_id", None)
    run_id_label, run_id_value = None, None
    if _extract_children(state):  # sequence has children
        run_id_label, run_id_value = "Flow Run ID", flow_run_id
    else:
        run_id_label, run_id_value = "Task Run ID", task_run_id

    # Extract ptf_result
    ptf_result = getattr(state, "ptf_result", None)
    step_type = None
    if isinstance(ptf_result, dict):
        step_type = ptf_result.get("step_type")

    # --- Sections ---

    # Step overview
    overview_html = f"""
      <div class="row" style="gap:14px; margin:6px 0; flex-wrap: wrap;">
        <div><b>PyTestFlow State:</b> <code class="inline">{_safe(ptf_state_type)}</code></div>
        <div><b>Prefect State:</b> <code class="inline">{_safe(prefect_state_type)}</code></div>
        {"<div><b>Step Type:</b> <code class='inline'>" + _safe(step_type) + "</code></div>" if step_type else ""}
        {("<div><b>" + run_id_label + ":</b> <code class='inline'>" + _safe(run_id_value) + "</code></div>") if run_id_value else ""}
        {"<div><b>Message:</b> " + _safe(msg) + "</div>" if msg else ""}
      </div>
    """

    # Step-specific ptf_result (excluding meta fields)
    ptf_details_html = ""
    if isinstance(ptf_result, dict):
        rows = []
        for k, v in ptf_result.items():
            if k in ("step_name", "step_type", "start_time", "duration_s",
                     "flow_run_id", "flow_name", "task_run_id", "task_name", "additional_info"):
                continue
            rows.append(f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(v)}</td></tr>")
        if rows:
            ptf_details_html = f"""
            <table class="summary-table" style="margin:8px 0;">
              <thead><tr><th colspan="2">Step Details</th></tr></thead>
              <tbody>{"".join(rows)}</tbody>
            </table>
            """

    # Additional info + meta
    meta_html = ""
    if isinstance(ptf_result, dict):
        meta_rows = []
        if "additional_info" in ptf_result:
            for k, v in ptf_result["additional_info"].items():
                meta_rows.append(f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(v)}</td></tr>")
        for k in ("start_time", "duration_s", "flow_run_id", "flow_name", "task_run_id", "task_name"):
            if k in ptf_result:
                meta_rows.append(f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(ptf_result[k])}</td></tr>")
        if meta_rows:
            meta_html = f"""
            <table class="summary-table" style="margin:8px 0;">
              <thead><tr><th colspan="2">Meta Information</th></tr></thead>
              <tbody>{"".join(meta_rows)}</tbody>
            </table>
            """

    # Raw Prefect result
    raw_result = _extract_result(getattr(state, "result", None))
    res_html = f"<pre>{_safe(_try_json(raw_result))}</pre>"

    pad = " indent" if depth > 0 else ""
    return f"""
    <div id="{anchor_id}" class="{pad}">
      <div class="row" style="justify-content:space-between;">
        <h3 style="margin:6px 0;">{_safe(label)} {badge}</h3>
      </div>
      {overview_html}
      {ptf_details_html}
      {meta_html}
      <details><summary><b>Show raw result</b></summary>{res_html}</details>
    """



def _render_detail_block_old(anchor_id: str, label: str, state: Any, depth: int) -> str:
    # PyTestFlow + Prefect state types
    ptf_state_type = state.__class__.__name__   # e.g., PyTestflowPassed
    prefect_state_type = _extract_type_label(state)  # e.g., StateType.COMPLETED
    badge = _status_badge(_extract_status_name(state))
    msg = _extract_message(state)

    # IDs: prefer TaskRun for steps, FlowRun for sequences
    task_run_id = getattr(state, "task_run_id", None)
    flow_run_id = getattr(state, "flow_run_id", None)
    if _extract_children(state):  # sequence has children
        run_id_label = "Flow Run ID"
        run_id_value = flow_run_id
    else:
        run_id_label = "Task Run ID"
        run_id_value = task_run_id

    # Step type (from attribute or ptf_result dict)
    step_type = getattr(state, "step_type", None)
    if not step_type and isinstance(getattr(state, "ptf_result", None), dict):
        step_type = getattr(state, "ptf_result", {}).get("step_type")

    # Timing info (prefer Prefect timestamps if present)
    start_time = getattr(state, "start_time", None)
    end_time = getattr(state, "end_time", None)
    duration = None
    if start_time and end_time:
        try:
            duration = (end_time - start_time).total_seconds()
        except Exception:
            pass
    else:
        # fallback to PyTestFlow timestamp
        start_time = getattr(state, "pytestflow_timestamp", None)

    # ptf_result extraction
    ptf_result = getattr(state, "ptf_result", None)
    ptf_html = ""
    if isinstance(ptf_result, dict):
        rows = [f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(v)}</td></tr>" for k, v in ptf_result.items()]
        ptf_html = f"""
        <table class="summary-table" style="margin:8px 0;">
          <thead><tr><th colspan="2">ptf_result</th></tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
        """

    # Raw Prefect result
    raw_result = _extract_result(getattr(state, "result", None))
    res_html = f"<pre>{_safe(_try_json(raw_result))}</pre>"

    pad = " indent" if depth > 0 else ""
    return f"""
    <div id="{anchor_id}" class="{pad}">
      <div class="row" style="justify-content:space-between;">
        <h3 style="margin:6px 0;">{_safe(label)} {badge}</h3>
      </div>
      <div class="row" style="gap:14px; margin:6px 0 6px 0; flex-wrap: wrap;">
        <div><b>PyTestFlow State:</b> <code class="inline">{_safe(ptf_state_type)}</code></div>
        <div><b>Prefect State:</b> <code class="inline">{_safe(prefect_state_type)}</code></div>
        {"<div><b>Step Type:</b> <code class='inline'>" + _safe(step_type) + "</code></div>" if step_type else ""}
        {("<div><b>" + run_id_label + ":</b> <code class='inline'>" + _safe(run_id_value) + "</code></div>") if run_id_value else ""}
        {"<div><b>Start:</b> " + _safe(start_time) + "</div>" if start_time else ""}
        {"<div><b>Duration:</b> " + f"{duration:.2f} s" + "</div>" if duration is not None else ""}
        {"<div><b>Message:</b> " + _safe(msg) + "</div>" if msg else ""}
      </div>
      {ptf_html}
      <details><summary><b>Show raw result</b></summary>{res_html}</details>
    """


def _walk(state: Any, base_anchor: str, depth: int = 0, index_prefix: str = "1") -> tuple[str, list[str]]:
    """
    Returns (html, toc_entries)
    toc_entries: list of '<li><a href="#..">..</a></li>' strings
    """
    children = _extract_children(state)
    out_html_parts: list[str] = []
    toc_entries: list[str] = []

    # The root "state" itself is already rendered by caller; we render its children here.
    for i, (name, child_state) in enumerate(children, start=1):
        label = _guess_step_label(str(name), child_state)
        idx = f"{index_prefix}.{i}"
        anchor_id = _slug(f"{base_anchor}-{idx}-{label}")

        # detail block for this child
        block = _render_detail_block(anchor_id, f"{idx} — {label}", child_state, depth)
        out_html_parts.append(block)

        # Recurse for grandchildren
        grandchildren = _extract_children(child_state)
        if grandchildren:
            # mark in summary that it’s a subsequence
            # close current header; then recurse
            sub_html, sub_toc = _walk(child_state, base_anchor=anchor_id, depth=depth+1, index_prefix=idx)
            out_html_parts.append(sub_html)
            toc_entries.append(f'<li><a href="#{anchor_id}">{_safe(idx)} — {_safe(label)} (subsequence)</a><ul>{"".join(sub_toc)}</ul></li>')
        else:
            toc_entries.append(f'<li><a href="#{anchor_id}">{_safe(idx)} — {_safe(label)}</a></li>')

        # Close the detail container div
        out_html_parts.append("</div>")

    return "\n".join(out_html_parts), toc_entries

def generate_html_report(root_state: Any, title: str = "Test Sequence Report", out_dir: str = "test_reports") -> str:
    """
    Generate a single-page HTML report for a PyTestFlow/Prefect result tree.
    Returns the file path to the generated report.
    """
    _ensure_dir(out_dir)
    ts = _now_ts()
    filename = f"{ts}_{_slug(title)}.html"
    out_path = os.path.join(out_dir, filename)

    # Top-level info
    top_status = _extract_status_name(root_state)
    top_badge = _status_badge(top_status)
    top_msg = _extract_message(root_state)
    top_type = _extract_type_label(root_state)

    # Root anchor
    root_anchor = _slug(f"root-{title}")

    # Summary table rows
    summary_rows = []
    children = _extract_children(root_state)
    for i, (name, child_state) in enumerate(children, start=1):
        label = _guess_step_label(str(name), child_state)
        idx = i
        anchor_id = _slug(f"{root_anchor}-{idx}-{label}")
        status = _extract_status_name(child_state)
        badge = _status_badge(status)
        is_sub = len(_extract_children(child_state)) > 0
        row = _render_row_line(idx, anchor_id, label, badge, _extract_type_label(child_state), is_sub)
        summary_rows.append(row)

    # Full details
    details_html, toc_entries = _walk(root_state, base_anchor=root_anchor, depth=1, index_prefix="1")

    # Root block header
    root_block = _render_detail_block(root_anchor, f"0 — {title}", root_state, depth=0) + "</div>"

    toc_html = f"""
    <div class="toc">
      <h3>Contents</h3>
      <div style="margin-bottom:8px;">
        <button onclick="expandAll()">Expand all</button>
        <button onclick="collapseAll()">Collapse all</button>
      </div>
      <ul>
        <li><a href="#{root_anchor}">0 — { _safe(title) } (root)</a></li>
        { "".join(toc_entries) }
      </ul>
    </div>
    """

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{_safe(title)} — {_safe(ts)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
{CSS}
</head>
<body>
  <h1>{_safe(title)} {top_badge}</h1>
  <div class="meta">
    <div><b>Generated:</b> {_safe(ts)}</div>
    {"<div><b>Message:</b> " + _safe(top_msg) + "</div>" if top_msg else ""}
    <div><b>State Type:</b> <code class="inline">{_safe(top_type)}</code></div>
  </div>

  <table class="summary-table">
    <thead>
      <tr>
        <th width="60">#</th>
        <th>Step</th>
        <th width="120">Status</th>
        <th width="120">State Type</th>
        <th width="120">Subsequence</th>
      </tr>
    </thead>
    <tbody>
      {"".join(summary_rows)}
    </tbody>
  </table>

  {toc_html}

  {root_block}

  {details_html}

{JS}
</body>
</html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return out_path

# ---------- Example usage ----------
# from report_html import generate_html_report
# path = generate_html_report(root_state, title="MotherboardTestSequence")
# print("Report at:", path)

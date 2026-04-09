# report_html.py
from __future__ import annotations
import os, html, re
from datetime import datetime
from typing import Any
from pytestflow.config.config_manager import ConfigManager

config = ConfigManager().get_config()
REPORTS_FOLDER = config["test_reports"]


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

def _extract_children(state: Any) -> list[tuple[str, Any]]:
    return list(getattr(state, "children", []) or [])

def _extract_message(state: Any) -> str:
    return getattr(state, "message", "") or ""

def _extract_status_name(state: Any) -> str:
    n = getattr(state, "name", None)
    if n:
        return str(n)
    return state.__class__.__name__

def _extract_type_label(state: Any) -> str:
    return str(getattr(state, "type", "")) or ""

def _guess_step_label(name: str, state: Any) -> str:
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
    status_upper = status.upper()
    if "PAS" in status_upper:
        cls = "badge-pass"
    elif "FAIL" in status_upper or status_upper == "ERROR":
        cls = "badge-fail"
    else:
        cls = "badge-other"
    return f'<span class="badge {cls}">{_safe(status)}</span>'

def _collect_step_stats(state) -> dict:
    stats = {"passed": 0, "failed": 0, "done": 0, "other": 0, "total": 0}
    children = _extract_children(state)
    for _, child_state in children:
        stats["total"] += 1
        status = _extract_status_name(child_state).lower()
        if "pass" in status:
            stats["passed"] += 1
        elif "fail" in status:
            stats["failed"] += 1
        elif "done" in status:
            stats["done"] += 1
        else:
            stats["other"] += 1
    return stats

# ---------- HTML assembly ----------
CSS = """<style>
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
</style>"""

def _render_row_line(idx, anchor_id, label, status_badge_html, type_label, is_subsequence):
    sub = "Yes" if is_subsequence else "No"
    return f"""<tr>
        <td><small class="lo">{idx:03d}</small></td>
        <td>{_safe(label)}</td>
        <td>{status_badge_html}</td>
        <td><code class="inline">{_safe(type_label)}</code></td>
        <td><code class="inline">{sub}</code></td>
      </tr>"""

def _render_detail_block(anchor_id: str, label: str, state: Any, depth: int, children_html: str = "") -> str:
    ptf_state_type = state.__class__.__name__
    prefect_state_type = _extract_type_label(state)
    badge = _status_badge(_extract_status_name(state))
    msg = _extract_message(state)

    task_run_id = getattr(state, "task_run_id", None)
    flow_run_id = getattr(state, "flow_run_id", None)
    run_id_label, run_id_value = ("Task Run ID", task_run_id)
    if _extract_children(state):  # subsequence
        run_id_label, run_id_value = ("Flow Run ID", flow_run_id)

    ptf_result = getattr(state, "ptf_result", None)
    step_type = ptf_result.get("step_type") if isinstance(ptf_result, dict) else None

    # Step overview
    overview_html = f"""
      <div class="row" style="gap:14px; margin:6px 0; flex-wrap: wrap;">
        <div><b>PyTestFlow State:</b> <code class="inline">{_safe(ptf_state_type)}</code></div>
        <div><b>Prefect State:</b> <code class="inline">{_safe(prefect_state_type)}</code></div>
        {"<div><b>Step Type:</b> <code class='inline'>" + _safe(step_type) + "</code></div>" if step_type else ""}
        {("<div><b>" + run_id_label + ":</b> <code class='inline'>" + _safe(run_id_value) + "</code></div>") if run_id_value else ""}
        {"<div><b>Message:</b> " + _safe(msg) + "</div>" if msg else ""}
      </div>"""

    # Step-specific details
    ptf_details_html = ""
    if isinstance(ptf_result, dict):
        rows = []
        for k, v in ptf_result.items():
            if k in ("step_name","flow_run_id","flow_name","task_run_id","task_name","additional_info"):
                continue
            rows.append(f"<tr><td><b>{_safe(k)}</b></td><td>{_safe(v)}</td></tr>")
        if rows:
            ptf_details_html = f"""<table class="summary-table"><thead><tr><th colspan="2">Step Details</th></tr></thead><tbody>{"".join(rows)}</tbody></table>"""

    pad = " indent" if depth > 0 else ""
    return f"""<div id="{anchor_id}" class="{pad}">
      <div class="row" style="justify-content:space-between;"><h3>{_safe(label)} {badge}</h3></div>
      {overview_html}
      {ptf_details_html}
      {children_html}
    </div>"""

def _walk(state: Any, base_anchor: str, depth=0, index_prefix="1") -> tuple[str,list[str]]:
    children = _extract_children(state)
    out_html_parts, toc_entries = [], []
    for i,(name,child_state) in enumerate(children,start=1):
        label = _guess_step_label(str(name), child_state)
        idx = f"{index_prefix}.{i}"
        anchor_id = _slug(f"{base_anchor}-{idx}-{label}")
        
        child_has_children = _extract_children(child_state)
        if child_has_children:
            sub_html, sub_toc = _walk(child_state, base_anchor=anchor_id, depth=depth+1, index_prefix=idx)
            block = _render_detail_block(anchor_id, f"{idx} — {label}", child_state, depth, children_html=sub_html)
            toc_entries.append(f'<li><a href="#{anchor_id}">{_safe(idx)} — {_safe(label)} (subsequence)</a><ul>{"".join(sub_toc)}</ul></li>')
        else:
            block = _render_detail_block(anchor_id, f"{idx} — {label}", child_state, depth)
            toc_entries.append(f'<li><a href="#{anchor_id}">{_safe(idx)} — {_safe(label)}</a></li>')
        
        out_html_parts.append(block)
    return "\n".join(out_html_parts), toc_entries

def generate_html_report(serial_number: str, root_state: Any, out_dir: str | None = None) -> str:
    if out_dir is None:
        out_dir = REPORTS_FOLDER
    title="Test Sequence Report" + (f" — SN: {serial_number}" if serial_number else "")
    _ensure_dir(out_dir)
    ts = _now_ts()
    filename = f"{ts}_{_slug(title)}.html"
    out_path = os.path.join(out_dir, filename)

    top_status = _extract_status_name(root_state)
    top_badge = _status_badge(top_status)
    top_msg = _extract_message(root_state)
    top_type = _extract_type_label(root_state)

    root_anchor = _slug(f"root-{title}")
    stats = _collect_step_stats(root_state)

    summary_rows = []
    children = _extract_children(root_state)
    for i,(name,child_state) in enumerate(children,start=1):
        label = _guess_step_label(str(name), child_state)
        idx = i
        anchor_id = _slug(f"{root_anchor}-{idx}-{label}")
        status = _extract_status_name(child_state)
        badge = _status_badge(status)
        is_sub = len(_extract_children(child_state))>0
        row = _render_row_line(idx, anchor_id, label, badge, _extract_type_label(child_state), is_sub)
        summary_rows.append(row)

    details_html, toc_entries = _walk(root_state, base_anchor=root_anchor, depth=1, index_prefix="1")
    root_block = _render_detail_block(root_anchor, f"0 — {title}", root_state, depth=0, children_html=details_html)   

    stats_html = f"""<div class="meta">
      <div><b>Generated:</b> {_safe(ts)}</div>
      {"<div><b>Message:</b> "+_safe(top_msg)+"</div>" if top_msg else ""}
      <div><b>Steps:</b> {stats["total"]} total — ✅ {stats["passed"]} passed / ❌ {stats["failed"]} failed / ⚙️ {stats["done"]} done / {stats["other"]} other</div>
    </div>"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<title>{_safe(title)} — {_safe(ts)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
{CSS}</head><body>
  <h1>{_safe(title)} {top_badge}</h1>
  {stats_html}
  <table class="summary-table"><thead><tr>
        <th width="60">#</th><th>Step</th><th width="120">Status</th>
        <th width="120">State</th><th width="120">Subsequence</th>
  </tr></thead><tbody>{"".join(summary_rows)}</tbody></table>
  {root_block}
</body></html>"""

    with open(out_path,"w",encoding="utf-8") as f: f.write(html_doc)
    return out_path

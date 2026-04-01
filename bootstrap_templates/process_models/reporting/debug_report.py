import pickle
from pathlib import Path

from bootstrap_templates.process_models.reporting.html_report import generate_html_report


def main():
    pkl_path = Path("test_reports/dataf_for_report.pkl")
    if not pkl_path.exists():
        raise SystemExit(f"Pickle file not found: {pkl_path}")

    with open(pkl_path, "rb") as f:
        loaded = pickle.load(f)

    # Handle both dict and state object
    if isinstance(loaded, dict):
        state = loaded.get("main_results") or loaded.get("main_result")
        if state is None:
            raise ValueError("Pickle contains dict but no 'main_results' or 'main_result' key")
    else:
        state = loaded

    result = generate_html_report("MY_SERIAL_NUMBER", state, out_dir="test_reports")
    print(f"Report generated: {result}")


if __name__ == "__main__":
    main()
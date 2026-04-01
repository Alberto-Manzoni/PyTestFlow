class ReportManager:
    def __init__(self):
        self._last_report: None
        # self.report_dir = REPORTS_FOLDER # for future use

    def set_last_report(self, path: str):
        self._last_report = path

    def get_last_report(self) -> str | None:
        return self._last_report

    def has_report(self) -> bool:
        return self._last_report is not None

report_manager = ReportManager()
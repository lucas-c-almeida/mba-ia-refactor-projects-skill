"""Report use case."""


class ReportController:
    def __init__(self, reports):
        self._reports = reports

    def sales_report(self) -> dict:
        return self._reports.sales_report()

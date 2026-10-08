"""Health use case: proves the datastore answers and counts what it holds."""


class HealthController:
    def __init__(self, reports):
        self._reports = reports

    def check(self) -> dict:
        self._reports.ping()
        return self._reports.entity_counts()

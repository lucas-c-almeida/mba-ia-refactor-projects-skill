import logging

from models.errors import PersistenceError

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Transaction boundary shared by the repositories of one request."""

    def __init__(self, session):
        self._session = session

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def commit_or_raise(self, failure_message):
        """Commit; on failure roll back, log the cause and raise the domain error.

        The one place where a failed write becomes a PersistenceError whose message
        is what the caller is shown.
        """
        try:
            self._session.commit()
        except Exception:
            self._session.rollback()
            logger.exception(failure_message)
            raise PersistenceError(failure_message)

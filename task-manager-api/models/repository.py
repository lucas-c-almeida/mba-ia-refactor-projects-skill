"""Shared persistence plumbing for the repositories (persistence lives in the model layer)."""
import logging

from models.errors import PersistenceError

logger = logging.getLogger(__name__)


class Repository:
    def __init__(self, session):
        self._session = session

    def add(self, entity):
        self._session.add(entity)

    def delete(self, entity):
        self._session.delete(entity)

    def commit(self, failure_message):
        """Commit the unit of work; on failure roll back, log the cause, raise a safe error."""
        try:
            self._session.commit()
        except Exception as exc:
            self._session.rollback()
            logger.exception('commit failed: %s', failure_message)
            raise PersistenceError(failure_message) from exc

"""Transaction boundary shared by the controllers (RP-09)."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from models.errors import PersistenceError

logger = logging.getLogger(__name__)


class UnitOfWork:
    def __init__(self, db):
        self._db = db

    def commit(self, failure_message):
        """Commit; on a persistence failure roll back, log the cause and raise a domain error."""
        try:
            self._db.session.commit()
        except SQLAlchemyError:
            self._db.session.rollback()
            logger.exception(failure_message)
            raise PersistenceError(failure_message)

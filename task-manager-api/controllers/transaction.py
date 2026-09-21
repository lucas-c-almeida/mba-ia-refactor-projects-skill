"""Transaction boundary shared by the controllers."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from models.errors import PersistenceError

logger = logging.getLogger(__name__)


def commit(session, failure_message):
    """Commit the unit of work; on a datastore failure roll back, log, and raise."""
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception('commit failed: %s', failure_message)
        raise PersistenceError(failure_message)

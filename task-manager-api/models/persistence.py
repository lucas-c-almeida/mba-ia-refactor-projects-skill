import logging

from database import db
from models.errors import PersistenceError

logger = logging.getLogger(__name__)


def commit(failure_message):
    """Commit the session; on failure roll back, log the cause, raise a PersistenceError
    carrying the message the client has always received for that operation."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception(failure_message)
        raise PersistenceError(failure_message)

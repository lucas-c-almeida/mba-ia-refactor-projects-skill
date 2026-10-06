import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from models.errors import PersistenceError

db = SQLAlchemy()

logger = logging.getLogger(__name__)


def commit_or_fail(failure_message):
    """Commit the unit of work; on a datastore failure roll back, log, and raise the domain error."""
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception('commit failed: %s', failure_message)
        raise PersistenceError(failure_message)

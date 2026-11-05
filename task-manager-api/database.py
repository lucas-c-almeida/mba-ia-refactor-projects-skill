import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError

from models.errors import PersistenceError

db = SQLAlchemy()

# Largest value an INTEGER primary key can hold; a larger id cannot exist, so it is "not found"
# rather than a driver overflow (RP-02).
MAX_ID = 2 ** 63 - 1


def enforce_foreign_keys(engine):
    """SQLite ignores declared foreign keys unless each connection switches them on (RP-19)."""
    @event.listens_for(engine, 'connect')
    def _foreign_keys_on(dbapi_connection, _connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()


def get_by_id(model, record_id):
    """Primary-key lookup (Session.get, the successor of the legacy Query.get — RP-14)."""
    if not isinstance(record_id, int) or isinstance(record_id, bool) or not 0 < record_id <= MAX_ID:
        return None
    return db.session.get(model, record_id)


def commit(failure_message):
    """Commit the unit of work; on a database failure roll back and raise the application's
    own error for that operation (the message each operation already answered with)."""
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise PersistenceError(failure_message) from error

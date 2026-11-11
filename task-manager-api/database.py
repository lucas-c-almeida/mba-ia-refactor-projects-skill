from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def enable_sqlite_foreign_keys(engine):
    """SQLite ignores declared foreign keys unless each connection turns them on (AP-20)."""
    if engine.dialect.name != 'sqlite':
        return

    @event.listens_for(engine, 'connect')
    def _enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

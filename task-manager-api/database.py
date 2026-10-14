import logging
import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable

db = SQLAlchemy()

logger = logging.getLogger(__name__)

# Tables whose CHECK constraints are declared in the models.
CONSTRAINED_TABLES = ('users', 'tasks')


def enable_sqlite_foreign_keys(engine):
    """SQLite enforces declared foreign keys only when this pragma is on, per connection."""

    @event.listens_for(engine, 'connect')
    def _enable(dbapi_connection, _record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.execute('PRAGMA foreign_keys=ON')


def upgrade_legacy_tables(engine):
    """Idempotent. A database file created before the CHECK constraints existed gets its tables
    rebuilt by copy (SQLite cannot add a constraint in place). No row is dropped: if the rebuild
    fails, for instance because a row violates a constraint, the table is left untouched."""
    if engine.dialect.name != 'sqlite':
        return
    raw = engine.raw_connection()
    try:
        connection = raw.driver_connection
        for name in CONSTRAINED_TABLES:
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
            if row is not None and 'CHECK' not in row[0].upper():
                _rebuild_by_copy(connection, db.metadata.tables[name])
    finally:
        raw.close()


def _rebuild_by_copy(connection, table):
    name = table.name
    old_columns = {r[1] for r in connection.execute('PRAGMA table_info(%s)' % name)}
    columns = ', '.join(c.name for c in table.columns if c.name in old_columns)
    ddl = str(CreateTable(table).compile(dialect=sqlite.dialect())).replace(
        'CREATE TABLE %s (' % name, 'CREATE TABLE %s__new (' % name, 1)
    previous_isolation = connection.isolation_level
    connection.isolation_level = None  # autocommit: the transaction below is explicit
    connection.execute('PRAGMA foreign_keys=OFF')
    try:
        connection.execute('BEGIN')
        connection.execute(ddl)
        connection.execute('INSERT INTO %s__new (%s) SELECT %s FROM %s' % (name, columns, columns, name))
        connection.execute('DROP TABLE %s' % name)
        connection.execute('ALTER TABLE %s__new RENAME TO %s' % (name, name))
        connection.execute('COMMIT')
        logger.info('Table %s rebuilt with its CHECK constraints', name)
    except sqlite3.Error:
        if connection.in_transaction:
            connection.execute('ROLLBACK')
        logger.warning('Table %s keeps its previous definition: CHECK constraints not applied', name)
    finally:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.isolation_level = previous_isolation

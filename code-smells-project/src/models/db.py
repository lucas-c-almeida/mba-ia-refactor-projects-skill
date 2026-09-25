"""
Connection factory — no module-level connection, no side effects at import time.

Fixes AP-06 (hard-wired dependency / no composition root) and AP-07 (mutable global
connection state): the connection is now constructed once by the composition root
(app.py) and handed to whatever needs it, instead of being a lazily-initialized
module-level global that every layer reaches for directly.
"""
import sqlite3


def create_connection(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    # Foreign keys are off by default in SQLite; a declaration never enabled counts
    # as absent (catalog AP-20). Every connection this app creates turns it on.
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

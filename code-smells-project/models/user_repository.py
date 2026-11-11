"""Persistence for user accounts. Every statement is parameterized."""
import sqlite3

from models.database import transaction
from models.errors import ValidationError

_COLUMNS = "id, nome, email, senha, tipo, criado_em"
DEFAULT_ROLE = "cliente"


def _to_user(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": row["senha"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UserRepository:
    def __init__(self, connection_provider):
        self._connection = connection_provider

    def list_all(self):
        rows = self._connection().execute("SELECT {0} FROM usuarios ORDER BY id".format(_COLUMNS))
        return [_to_user(row) for row in rows]

    def find_by_id(self, user_id):
        row = self._connection().execute(
            "SELECT {0} FROM usuarios WHERE id = ?".format(_COLUMNS), (user_id,)
        ).fetchone()
        return _to_user(row) if row else None

    def find_by_email(self, email):
        row = self._connection().execute(
            "SELECT {0} FROM usuarios WHERE email = ? ORDER BY id LIMIT 1".format(_COLUMNS), (email,)
        ).fetchone()
        return _to_user(row) if row else None

    def exists(self, user_id):
        row = self._connection().execute("SELECT 1 FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        return row is not None

    def create(self, nome, email, password_hash, tipo=DEFAULT_ROLE):
        connection = self._connection()
        try:
            with transaction(connection):
                cursor = connection.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    (nome, email, password_hash, tipo),
                )
        except sqlite3.IntegrityError:
            raise ValidationError("Email já cadastrado")
        return cursor.lastrowid

    def replace_password_hash(self, user_id, password_hash):
        connection = self._connection()
        with transaction(connection):
            connection.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (password_hash, user_id))

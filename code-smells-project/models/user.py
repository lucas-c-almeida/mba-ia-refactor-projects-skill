"""User persistence and authentication. Statements bind their values."""

import sqlite3

from models.constants import DEFAULT_USER_TYPE
from models.credentials import hash_password, is_hashed, verify_password
from models.errors import ConflictError


def row_to_user(row) -> dict:
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

    def list_all(self) -> list:
        rows = self._connection().execute("SELECT * FROM usuarios").fetchall()
        return [row_to_user(row) for row in rows]

    def find_by_id(self, user_id):
        row = self._connection().execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        return row_to_user(row) if row else None

    def create(self, nome, email, senha, tipo=DEFAULT_USER_TYPE) -> int:
        connection = self._connection()
        try:
            cursor = connection.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, hash_password(senha), tipo),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.rollback()
            raise ConflictError("Email já cadastrado")
        return cursor.lastrowid

    def authenticate(self, email, senha):
        """Return the matching account without its password, or None.

        A legacy row that still holds the plain password is re-hashed on a successful login.
        """
        connection = self._connection()
        rows = connection.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()
        for row in rows:
            if not verify_password(senha, row["senha"]):
                continue
            if not is_hashed(row["senha"]):
                connection.execute(
                    "UPDATE usuarios SET senha = ? WHERE id = ?", (hash_password(senha), row["id"])
                )
                connection.commit()
            return {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipo": row["tipo"],
            }
        return None

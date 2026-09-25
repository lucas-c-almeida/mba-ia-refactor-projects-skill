"""
User persistence — parameterized queries only (fixes AP-02); passwords hashed with a
purpose-built KDF instead of stored and compared as plain text (fixes AP-08).

`senha` stays in every serialized user dict, with the same key and the same string
type as before, but its value is now a fixed redacted placeholder rather than a
usable credential (masking the value while keeping the field and its type is a safe
change per the contract gate — a legitimate client never reads a password back).
Removing the field entirely is a further hardening step proposed, not applied, in
the audit report.
"""
from werkzeug.security import check_password_hash, generate_password_hash

SENHA_REDACTED = "[REDACTED]"


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": SENHA_REDACTED,
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UserRepository:
    def __init__(self, connection):
        self._connection = connection

    def get_todos(self) -> list:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM usuarios")
        return [_row_to_dict(row) for row in cursor.fetchall()]

    def get_por_id(self, usuario_id: int):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        return _row_to_dict(row) if row else None

    def contar(self) -> int:
        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        return cursor.fetchone()[0]

    def existe(self, usuario_id: int) -> bool:
        cursor = self._connection.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,))
        return cursor.fetchone() is not None

    def criar(self, nome, email, senha, tipo="cliente") -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        self._connection.commit()
        return cursor.lastrowid

    def autenticar(self, email: str, senha: str):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row is None:
            return None
        if not check_password_hash(row["senha_hash"], senha):
            return None
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }

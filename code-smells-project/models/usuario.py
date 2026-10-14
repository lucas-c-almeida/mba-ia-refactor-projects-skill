"""User persistence and password handling."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from models.constants import VALOR_MASCARADO

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def hash_senha(senha):
    return generate_password_hash(senha)


def _eh_hash(armazenada):
    return isinstance(armazenada, str) and armazenada.startswith(_PREFIXOS_HASH)


def _confere(armazenada, senha):
    if _eh_hash(armazenada):
        return check_password_hash(armazenada, senha)
    # Legacy row stored as plain text: constant-time comparison, upgraded on first sign-in.
    return hmac.compare_digest((armazenada or "").encode("utf-8"), senha.encode("utf-8"))


def _para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": VALOR_MASCARADO,
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UsuarioRepository:
    def __init__(self, db):
        self._db = db

    def listar(self):
        with self._db.session() as conn:
            return [_para_dict(row) for row in conn.execute("SELECT * FROM usuarios").fetchall()]

    def buscar_por_id(self, usuario_id):
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
            return _para_dict(row) if row else None

    def criar(self, nome, email, senha, tipo="cliente"):
        with self._db.session() as conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, hash_senha(senha), tipo),
            )
            return cursor.lastrowid

    def autenticar(self, email, senha):
        """Return the public user fields when the credentials match, else None."""
        with self._db.session() as conn:
            rows = conn.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
            for row in rows:
                if not _confere(row["senha"], senha):
                    continue
                if not _eh_hash(row["senha"]):
                    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (hash_senha(senha), row["id"]))
                return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
            return None

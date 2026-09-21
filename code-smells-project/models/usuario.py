"""User persistence. Passwords are stored hashed (see models/passwords.py)."""
from models import passwords
from models.constants import TIPO_USUARIO_PADRAO


class UsuarioRepository:
    def __init__(self, connection_provider):
        self._conn = connection_provider

    def listar(self):
        rows = self._conn().execute("SELECT * FROM usuarios").fetchall()
        return [dict(row) for row in rows]

    def obter(self, usuario_id):
        row = self._conn().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return dict(row) if row else None

    def listar_por_email(self, email):
        rows = self._conn().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchall()
        return [dict(row) for row in rows]

    def criar(self, nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
        conn = self._conn()
        with conn:
            cursor = conn.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, passwords.hash_password(senha), tipo),
            )
        return cursor.lastrowid

    def substituir_hash_senha(self, usuario_id, senha):
        conn = self._conn()
        with conn:
            conn.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (passwords.hash_password(senha), usuario_id),
            )

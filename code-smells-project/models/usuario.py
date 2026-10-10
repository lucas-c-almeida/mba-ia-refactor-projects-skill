"""Users: domain constants and persistence."""
import sqlite3

from errors import ConflictError

TIPO_PADRAO = "cliente"
# The credential keeps its field in the account responses, but its value is never read back.
SENHA_MASCARADA = "********"

_COLUNAS = "id, nome, email, senha, tipo, criado_em"


def _para_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": SENHA_MASCARADA,
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UsuarioRepository:
    def __init__(self, get_connection):
        self._get_connection = get_connection

    def listar(self):
        rows = self._get_connection().execute(
            "SELECT " + _COLUNAS + " FROM usuarios ORDER BY id").fetchall()
        return [_para_dict(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._get_connection().execute(
            "SELECT " + _COLUNAS + " FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _para_dict(row) if row else None

    def buscar_credenciais_por_email(self, email):
        """Rows (id, nome, email, senha armazenada, tipo) that answer to this e-mail."""
        return self._get_connection().execute(
            "SELECT " + _COLUNAS + " FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()

    def existe_email(self, email):
        row = self._get_connection().execute(
            "SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone()
        return row is not None

    def criar(self, nome, email, senha_armazenada, tipo=TIPO_PADRAO):
        try:
            cursor = self._get_connection().execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_armazenada, tipo))
        except sqlite3.IntegrityError:
            raise ConflictError("Email já cadastrado")
        return cursor.lastrowid

    def atualizar_senha(self, usuario_id, senha_armazenada):
        self._get_connection().execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?", (senha_armazenada, usuario_id))

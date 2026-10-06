"""User: serialization and persistence (AP-02, AP-08, AP-20)."""

import sqlite3

from models.errors import ValidationError

TIPO_PADRAO = "cliente"

# The password field stays in the response (its shape is contract) but its value is never sent.
SENHA_MASCARADA = "********"

CAMPOS = ("id", "nome", "email", "senha", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def usuario_para_dict(linha):
    dados = {campo: linha[campo] for campo in CAMPOS}
    dados["senha"] = SENHA_MASCARADA
    return dados


def usuario_autenticado_para_dict(linha):
    return {campo: linha[campo] for campo in CAMPOS_LOGIN}


class UsuarioRepository:
    def __init__(self, conexao):
        self._conexao = conexao

    def listar_todos(self):
        linhas = self._conexao().execute("SELECT * FROM usuarios").fetchall()
        return [usuario_para_dict(linha) for linha in linhas]

    def obter_por_id(self, usuario_id):
        linha = self._conexao().execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return usuario_para_dict(linha) if linha else None

    def existe(self, usuario_id):
        linha = self._conexao().execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return linha is not None

    def existe_email(self, email):
        linha = self._conexao().execute(
            "SELECT 1 FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        return linha is not None

    def listar_por_email(self, email):
        """Rows with this email, oldest first: the order in which login used to match them."""
        return self._conexao().execute(
            "SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)
        ).fetchall()

    def criar(self, nome, email, senha_hash, tipo=TIPO_PADRAO):
        conexao = self._conexao()
        try:
            with conexao:
                cursor = conexao.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    (nome, email, senha_hash, tipo),
                )
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Email já cadastrado") from exc
        return cursor.lastrowid

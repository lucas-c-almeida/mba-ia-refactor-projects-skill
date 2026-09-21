"""Usuário: entidade, validação de entrada e persistência. Senhas só como hash."""
from dataclasses import dataclass

from models import senha as senhas
from models.erros import ErroValidacao

TIPO_PADRAO = "cliente"

_COLUNAS = "id, nome, email, senha, tipo, criado_em"


@dataclass(frozen=True)
class Usuario:
    id: int
    nome: str
    email: str
    senha: str          # sempre o hash armazenado; nunca serializado para o cliente
    tipo: str
    criado_em: str


@dataclass(frozen=True)
class DadosUsuario:
    nome: str
    email: str
    senha: str


@dataclass(frozen=True)
class Credenciais:
    email: str
    senha: str


def validar_dados_usuario(dados):
    if not isinstance(dados, dict) or not dados:
        raise ErroValidacao("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ErroValidacao("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ErroValidacao("Nome, email e senha devem ser texto")
    return DadosUsuario(nome, email, senha)


def validar_credenciais(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ErroValidacao("Email e senha são obrigatórios")
    return Credenciais(email, senha)


def _usuario(linha):
    return Usuario(**{chave: linha[chave] for chave in linha.keys()})


class UsuarioRepositorio:
    def __init__(self, provedor_conexao):
        self._conexao = provedor_conexao

    def listar(self):
        cursor = self._conexao().execute(f"SELECT {_COLUNAS} FROM usuarios ORDER BY id")
        return [_usuario(linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, usuario_id):
        cursor = self._conexao().execute(
            f"SELECT {_COLUNAS} FROM usuarios WHERE id = ?", (usuario_id,)
        )
        linha = cursor.fetchone()
        return _usuario(linha) if linha else None

    def listar_por_email(self, email):
        cursor = self._conexao().execute(
            f"SELECT {_COLUNAS} FROM usuarios WHERE email = ? ORDER BY id", (email,)
        )
        return [_usuario(linha) for linha in cursor.fetchall()]

    def inserir(self, nome, email, senha_em_claro, tipo=TIPO_PADRAO):
        cursor = self._conexao().execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senhas.gerar_hash(senha_em_claro), tipo),
        )
        return cursor.lastrowid

    def inserir_varios(self, usuarios):
        """`usuarios`: sequência de (nome, email, senha_em_claro, tipo)."""
        self._conexao().executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            [(nome, email, senhas.gerar_hash(senha), tipo) for nome, email, senha, tipo in usuarios],
        )

    def migrar_senhas_em_claro(self):
        """Converte para hash qualquer senha ainda armazenada em claro (bancos anteriores)."""
        conexao = self._conexao()
        linhas = conexao.execute("SELECT id, senha FROM usuarios").fetchall()
        pendentes = [
            (senhas.gerar_hash(str(linha["senha"])), linha["id"])
            for linha in linhas
            if linha["senha"] is not None and not senhas.eh_hash(linha["senha"])
        ]
        if pendentes:
            conexao.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", pendentes)
        return len(pendentes)

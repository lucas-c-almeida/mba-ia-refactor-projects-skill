"""User accounts: persistence. Passwords are never returned in clear."""

TIPO_PADRAO = "cliente"

# The field stays in user responses (clients read its presence and type); its value
# is never the stored credential.
SENHA_MASCARADA = "********"


def _para_dict(linha) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "senha": SENHA_MASCARADA,
        "tipo": linha["tipo"],
        "criado_em": linha["criado_em"],
    }


class UsuarioRepository:
    def __init__(self, obter_conexao):
        self._obter_conexao = obter_conexao

    def listar(self) -> list:
        linhas = self._obter_conexao().execute("SELECT * FROM usuarios").fetchall()
        return [_para_dict(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id: int):
        linha = self._obter_conexao().execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return _para_dict(linha) if linha else None

    def existe(self, usuario_id: int) -> bool:
        return self._obter_conexao().execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone() is not None

    def credenciais_por_email(self, email: str) -> list:
        """Every account answering to the email, oldest first, with its stored credential."""
        return self._obter_conexao().execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ? ORDER BY id",
            (email,),
        ).fetchall()

    def criar(self, nome, email, senha_armazenada, tipo=TIPO_PADRAO) -> int:
        conexao = self._obter_conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, senha_armazenada, tipo),
            )
        return cursor.lastrowid

    def substituir_senha(self, usuario_id: int, senha_armazenada: str) -> None:
        conexao = self._obter_conexao()
        with conexao:
            conexao.execute("UPDATE usuarios SET senha = ? WHERE id = ?",
                            (senha_armazenada, usuario_id))

    def contar(self) -> int:
        return self._obter_conexao().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

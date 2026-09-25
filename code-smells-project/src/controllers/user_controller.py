"""User and authentication use cases."""
from src.models.errors import NotAuthenticatedError, NotFoundError, ValidationError


class UserController:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self) -> list:
        return self._usuarios.get_todos()

    def buscar(self, usuario_id: int) -> dict:
        usuario = self._usuarios.get_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados: dict) -> int:
        if not dados:
            raise ValidationError("Dados inválidos")
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        return self._usuarios.criar(nome, email, senha)

    def login(self, dados: dict) -> dict:
        email = (dados or {}).get("email", "")
        senha = (dados or {}).get("senha", "")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")

        usuario = self._usuarios.autenticar(email, senha)
        if usuario is None:
            raise NotAuthenticatedError("Email ou senha inválidos", sucesso=False)
        return usuario

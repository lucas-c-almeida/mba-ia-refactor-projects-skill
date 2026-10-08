"""User use cases. Plain values in, plain values out; no request or response objects."""

from models.errors import AuthenticationError, NotFoundError, ValidationError


class UserController:
    def __init__(self, users):
        self._users = users

    def list_users(self) -> list:
        return self._users.list_all()

    def get_user(self, user_id) -> dict:
        user = self._users.find_by_id(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    def create_user(self, payload) -> int:
        if not payload or not isinstance(payload, dict):
            raise ValidationError("Dados inválidos")
        nome = payload.get("nome", "")
        email = payload.get("email", "")
        senha = payload.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        if not all(isinstance(value, str) for value in (nome, email, senha)):
            raise ValidationError("Nome, email e senha devem ser texto")
        return self._users.create(nome, email, senha)

    def login(self, payload) -> dict:
        if not payload or not isinstance(payload, dict):
            raise ValidationError("Dados inválidos")
        email = payload.get("email", "")
        senha = payload.get("senha", "")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        if not isinstance(email, str) or not isinstance(senha, str):
            raise ValidationError("Email e senha devem ser texto")
        user = self._users.authenticate(email, senha)
        if not user:
            raise AuthenticationError("Email ou senha inválidos", failure_flag=True)
        return user

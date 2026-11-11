"""Account use cases: listing, registration and sign-in."""
import logging

from models.errors import AuthenticationError, NotFoundError, ValidationError
from models.passwords import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, users):
        self._users = users

    def list_all(self):
        return self._users.list_all()

    def get(self, user_id):
        user = self._users.find_by_id(user_id) if user_id is not None else None
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def register(self, nome, email, senha):
        if self._users.find_by_email(email) is not None:
            raise ValidationError("Email já cadastrado")
        user_id = self._users.create(nome, email, hash_password(senha))
        logger.info("Usuário criado: id %s", user_id)
        return user_id

    def sign_in(self, email, senha):
        user = self._users.find_by_email(email)
        matches, needs_rehash = verify_password(user["senha"], senha) if user else (False, False)
        if not matches:
            logger.info("Login falhou")
            raise AuthenticationError("Email ou senha inválidos", with_success_flag=True)
        if needs_rehash:
            # A password stored before hashing existed is upgraded on its first sign-in.
            self._users.replace_password_hash(user["id"], hash_password(senha))
        logger.info("Login bem-sucedido: usuário %s", user["id"])
        return {"id": user["id"], "nome": user["nome"], "email": user["email"], "tipo": user["tipo"]}

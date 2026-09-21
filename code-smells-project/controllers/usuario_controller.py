"""User use cases: listing, registration and authentication."""
import logging

from models import passwords
from models.errors import AuthenticationError

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self):
        return self._usuarios.listar()

    def obter(self, usuario_id):
        return self._usuarios.obter(usuario_id)

    def criar(self, nome, email, senha):
        usuario_id = self._usuarios.criar(nome, email, senha)
        logger.info("Usuário criado: id=%s", usuario_id)  # no personal data in logs
        return usuario_id

    def autenticar(self, email, senha):
        """Return the matching user record, or raise AuthenticationError."""
        for usuario in self._usuarios.listar_por_email(email):
            if passwords.verify_password(usuario["senha"], senha):
                if passwords.needs_rehash(usuario["senha"]):
                    # Transparent upgrade of a row stored before hashing was introduced.
                    self._usuarios.substituir_hash_senha(usuario["id"], senha)
                logger.info("Login bem-sucedido: id=%s", usuario["id"])
                return usuario
        logger.info("Login falhou")
        raise AuthenticationError("Email ou senha inválidos")

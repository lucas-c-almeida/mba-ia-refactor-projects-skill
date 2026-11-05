"""User use cases."""
import logging

from controllers.validation import exigir_objeto
from models.errors import NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        exigir_objeto(dados)
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise ValidationError("Nome, email e senha são obrigatórios")
        if not all(isinstance(valor, str) for valor in (nome, email, senha)):
            raise ValidationError("Nome, email e senha devem ser texto")
        usuario_id = self._usuarios.criar(nome, email, senha)
        logger.info("Usuário criado: %s", email)
        return usuario_id

    def login(self, dados):
        exigir_objeto(dados, permitir_vazio=True)
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            raise ValidationError("Email e senha são obrigatórios")
        if not isinstance(email, str) or not isinstance(senha, str):
            raise ValidationError("Email e senha devem ser texto")
        usuario = self._usuarios.autenticar(email, senha)
        if not usuario:
            logger.info("Login falhou: %s", email)
            raise UnauthorizedError("Email ou senha inválidos", sucesso_false=True)
        logger.info("Login bem-sucedido: %s", email)
        return usuario

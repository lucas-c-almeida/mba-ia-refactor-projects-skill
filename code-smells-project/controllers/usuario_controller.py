import logging

from models import senhas
from models.errors import FALHA, AuthenticationError, NotFoundError, ValidationError
from models.usuario import usuario_autenticado_para_dict

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self):
        return self._usuarios.listar_todos()

    def obter(self, usuario_id):
        usuario = self._usuarios.obter_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, nome, email, senha):
        if self._usuarios.existe_email(email):
            raise ValidationError("Email já cadastrado")
        usuario_id = self._usuarios.criar(nome, email, senhas.gerar_hash(senha))
        logger.info("Usuário criado: id %s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        for linha in self._usuarios.listar_por_email(email):
            if senhas.verificar(senha, linha["senha"]):
                logger.info("Login bem-sucedido: usuario %s", linha["id"])
                return usuario_autenticado_para_dict(linha)
        logger.info("Login falhou")
        raise AuthenticationError("Email ou senha inválidos", extra=FALHA)

"""User use cases: registration and sign-in. Plain values in, plain values out."""
import logging

from errors import AuthenticationError, ConflictError, NotFoundError
from models.passwords import hash_password, verify_password

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

    def criar(self, nome, email, senha):
        if self._usuarios.existe_email(email):
            raise ConflictError("Email já cadastrado")
        usuario_id = self._usuarios.criar(nome, email, hash_password(senha))
        logger.info("Usuário criado: %s", email)
        return usuario_id

    def login(self, email, senha):
        for conta in self._usuarios.buscar_credenciais_por_email(email):
            confere, precisa_rehash = verify_password(senha, conta["senha"])
            if not confere:
                continue
            if precisa_rehash:
                # Rows written before hashing existed are upgraded the first time they sign in.
                self._usuarios.atualizar_senha(conta["id"], hash_password(senha))
            logger.info("Login bem-sucedido: %s", email)
            return {
                "id": conta["id"],
                "nome": conta["nome"],
                "email": conta["email"],
                "tipo": conta["tipo"],
            }
        logger.info("Login falhou: %s", email)
        raise AuthenticationError("Email ou senha inválidos", sucesso=False)

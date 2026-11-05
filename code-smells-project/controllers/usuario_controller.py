import logging

from models import senha

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios):
        self._usuarios = usuarios

    def listar(self) -> list:
        return self._usuarios.listar()

    def obter(self, usuario_id: int):
        return self._usuarios.buscar_por_id(usuario_id)

    def criar(self, nome: str, email: str, senha_informada: str) -> int:
        usuario_id = self._usuarios.criar(nome, email, senha.gerar_hash(senha_informada))
        logger.info("Usuário criado: id %s", usuario_id)
        return usuario_id

    def autenticar(self, email: str, senha_informada: str):
        """The first account for this email whose credential matches, or None.

        A credential still stored as given (written by the previous code) is replaced by
        its hash on the first successful sign-in.
        """
        for conta in self._usuarios.credenciais_por_email(email):
            if senha.verificar(senha_informada, conta["senha"]):
                if senha.e_legada(conta["senha"]):
                    self._usuarios.substituir_senha(conta["id"], senha.gerar_hash(senha_informada))
                logger.info("Login bem-sucedido: usuario id %s", conta["id"])
                return {"id": conta["id"], "nome": conta["nome"],
                        "email": conta["email"], "tipo": conta["tipo"]}
        logger.info("Login falhou")
        return None

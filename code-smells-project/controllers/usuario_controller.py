"""Casos de uso de usuário e autenticação. Nenhum dado pessoal vai para o log."""
import logging

from models import senha as senhas
from models.usuario import validar_credenciais, validar_dados_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios, unidade_de_trabalho):
        self._usuarios = usuarios
        self._transacao = unidade_de_trabalho

    def listar(self):
        return self._usuarios.listar()

    def buscar(self, usuario_id):
        return self._usuarios.buscar_por_id(usuario_id)

    def criar(self, dados):
        valido = validar_dados_usuario(dados)
        with self._transacao():
            usuario_id = self._usuarios.inserir(valido.nome, valido.email, valido.senha)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def autenticar(self, dados):
        """Devolve o usuário autenticado, ou None se as credenciais não conferem."""
        credenciais = validar_credenciais(dados)
        candidatos = self._usuarios.listar_por_email(credenciais.email)
        if not candidatos:
            senhas.verificar_ficticio(credenciais.senha)   # mesmo custo: não revela contas
        for usuario in candidatos:
            if senhas.verificar(credenciais.senha, usuario.senha):
                logger.info("Login bem-sucedido: usuario_id=%s", usuario.id)
                return usuario
        logger.info("Login falhou")
        return None

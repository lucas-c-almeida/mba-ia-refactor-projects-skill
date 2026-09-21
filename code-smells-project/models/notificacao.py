"""Porta de notificação do domínio e o adaptador atual (registro em log).

O comportamento original apenas imprimia as mensagens; o adaptador preserva isso via
logging. Um envio real (e-mail, SMS, push) é outro adaptador, ligado na raiz de composição.
"""
import logging
from typing import Protocol

from models.pedido import StatusPedido


class Notificador(Protocol):
    def pedido_criado(self, pedido_id, usuario_id): ...

    def status_alterado(self, pedido_id, novo_status): ...


class NotificadorLog:
    def __init__(self, logger=None):
        self._logger = logger or logging.getLogger("notificacoes")

    def pedido_criado(self, pedido_id, usuario_id):
        self._logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        self._logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        self._logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == StatusPedido.APROVADO:
            self._logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        if novo_status == StatusPedido.CANCELADO:
            self._logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

"""Notification adapter. The controllers depend on these two methods only; this
implementation writes them to the log, as the application did before (no real channel)."""
import logging

from models.pedido import StatusPedido

logger = logging.getLogger("notificacoes")


class NotificadorLog:
    def pedido_criado(self, pedido_id: int, usuario_id: int) -> None:
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def status_alterado(self, pedido_id: int, status: str) -> None:
        if status == StatusPedido.APROVADO:
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        elif status == StatusPedido.CANCELADO:
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

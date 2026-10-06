"""Notification adapter. The application has no real email/SMS/push integration: the original
wrote these notifications to standard output, and this adapter keeps doing exactly that through
the logging module. A real integration replaces this class in the composition root (app.py)."""

import logging

logger = logging.getLogger("notificacoes")


class NotificadorConsole:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def pedido_aprovado(self, pedido_id):
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

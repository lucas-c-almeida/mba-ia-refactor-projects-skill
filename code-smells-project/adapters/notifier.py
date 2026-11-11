"""Notification adapter. The application has no real e-mail/SMS/push integration: these
messages have always been written to the console, and still are, from one place."""
import logging

from models import order_status

logger = logging.getLogger("loja.notificacoes")


class ConsoleNotifier:
    def order_created(self, order_id, user_id):
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", order_id, user_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def order_status_changed(self, order_id, status):
        if status == order_status.APROVADO:
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", order_id)
        if status == order_status.CANCELADO:
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", order_id)

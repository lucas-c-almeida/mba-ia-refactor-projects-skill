"""Order notifications. Today they are log lines; this is the seam where a real channel plugs in."""

import logging

from models.constants import ORDER_STATUS_APPROVED, ORDER_STATUS_CANCELED

logger = logging.getLogger(__name__)


class LogNotifier:
    def order_created(self, order_id, user_id) -> None:
        logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", order_id, user_id)
        logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
        logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")

    def order_status_changed(self, order_id, status) -> None:
        if status == ORDER_STATUS_APPROVED:
            logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", order_id)
        if status == ORDER_STATUS_CANCELED:
            logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", order_id)

"""Notification port and its only current implementation.

No real e-mail/SMS/push integration exists. The adapter records the event in the log and says so,
instead of claiming a delivery that never happens.
"""
import logging

logger = logging.getLogger("notificacoes")


class NotificadorLog:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Pedido %s criado para usuario %s (notificação registrada; envio não implementado)",
                    pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Pedido %s aprovado: preparar envio (notificação registrada)", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Pedido %s cancelado: devolução de estoque pendente (notificação registrada)", pedido_id)

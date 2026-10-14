"""Order use cases."""
import logging

from controllers.validation import como_inteiro, eh_numero, exigir_objeto
from models.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS
from models.errors import ValidationError

logger = logging.getLogger(__name__)


def _validar_itens(itens):
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos: esperado uma lista")
    validados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Itens inválidos: cada item deve ser um objeto")
        if "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Itens inválidos: produto_id e quantidade são obrigatórios")
        quantidade = item["quantidade"]
        if not eh_numero(quantidade):
            raise ValidationError("Itens inválidos: quantidade deve ser numérica")
        if quantidade < 0:
            raise ValidationError("Itens inválidos: quantidade não pode ser negativa")
        validados.append({"produto_id": como_inteiro(item["produto_id"], "produto_id"), "quantidade": quantidade})
    return validados


class PedidoController:
    def __init__(self, pedidos):
        self._pedidos = pedidos

    def criar(self, dados):
        exigir_objeto(dados)
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens or len(itens) == 0:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        usuario_id = como_inteiro(usuario_id, "usuario_id")
        resultado = self._pedidos.criar(usuario_id, _validar_itens(itens))
        logger.info(
            "Pedido %s criado para usuario %s (notificações por e-mail, SMS e push ainda não implementadas)",
            resultado["pedido_id"], usuario_id,
        )
        return resultado

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self._pedidos.listar_todos()

    def atualizar_status(self, pedido_id, dados):
        exigir_objeto(dados, permitir_vazio=True)
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")
        self._pedidos.atualizar_status(pedido_id, novo_status)
        if novo_status == STATUS_APROVADO:
            logger.info("Pedido %s aprovado; preparar envio (notificação não implementada)", pedido_id)
        if novo_status == STATUS_CANCELADO:
            logger.info("Pedido %s cancelado; devolver estoque (não implementado)", pedido_id)

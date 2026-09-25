"""
Order use cases (fixes AP-05: this logic used to live directly in the Flask route
handler in controllers.py, including the persistence calls now delegated to the
repository).
"""
from src.models.constants import STATUS_VALIDOS
from src.models.errors import ValidationError
from src.validation import validar_item_pedido


class OrderController:
    def __init__(self, pedidos, usuarios):
        # Product existence/stock is validated inside OrderRepository.criar itself
        # (it is the one place that already reads each item's product row); this
        # controller does not need its own reference to the product repository.
        self._pedidos = pedidos
        self._usuarios = usuarios

    def criar(self, dados: dict) -> dict:
        if not dados:
            raise ValidationError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        if not itens or len(itens) == 0:
            raise ValidationError("Pedido deve ter pelo menos 1 item")

        # New checks (fix AP-11 / AP-20): a fabricated usuario_id, or a malformed
        # item, is a value no legitimate client sends — the original had no check
        # at all here and would silently accept both. See the audit report: this
        # passes the legitimate-use test and is applied, not merely proposed.
        if (
            not isinstance(usuario_id, int)
            or isinstance(usuario_id, bool)
            or not self._usuarios.existe(usuario_id)
        ):
            raise ValidationError("Usuario {0} não encontrado".format(usuario_id))
        for item in itens:
            erros = validar_item_pedido(item)
            if erros:
                raise ValidationError(erros[0])

        return self._pedidos.criar(usuario_id, itens)

    def listar_todos(self) -> list:
        return self._pedidos.get_todos()

    def listar_por_usuario(self, usuario_id: int) -> list:
        return self._pedidos.get_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id: int, dados: dict) -> None:
        novo_status = (dados or {}).get("status", "")
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        self._pedidos.atualizar_status(pedido_id, novo_status)

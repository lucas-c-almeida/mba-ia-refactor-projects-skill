"""Boundary parsing: is this a well-formed request? Every value read from a request is
type- and range-checked here, before a controller sees it, with no silent coercion
(a boolean is not a number, a string is not an integer)."""
import math

from models import order_status
from models.catalog import DEFAULT_CATEGORY, VALID_CATEGORIES
from models.errors import ValidationError
from models.money import INT64_MAX, to_cents


def bounded_id(value):
    """A path identifier outside the storage range matches nothing: None means 'no such row'."""
    return value if 0 <= value <= INT64_MAX else None


def _as_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        value = int(value)
    if isinstance(value, int) and -INT64_MAX <= value <= INT64_MAX:
        return value
    return None


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_id(value):
    number = _as_int(value)
    return number if number is not None and number > 0 else None


def parse_product(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    for key, message in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"),
                         ("estoque", "Estoque é obrigatório")):
        if key not in data:
            raise ValidationError(message)
    nome = data["nome"]
    descricao = data.get("descricao", "")
    preco = data["preco"]
    estoque = _as_int(data["estoque"])
    categoria = data.get("categoria", DEFAULT_CATEGORY)
    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _is_number(preco) or to_cents(abs(preco)) > INT64_MAX:
        raise ValidationError("Preço inválido")
    if estoque is None:
        raise ValidationError("Estoque inválido")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria inválida. Válidas: " + str(VALID_CATEGORIES))
    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def _price_param(raw):
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ValidationError("Parâmetro de preço inválido")
    if not math.isfinite(value):
        raise ValidationError("Parâmetro de preço inválido")
    return value


def parse_search(args):
    return {
        "term": args.get("q", ""),
        "category": args.get("categoria", None),
        "min_price": _price_param(args.get("preco_min", None)),
        "max_price": _price_param(args.get("preco_max", None)),
    }


def parse_new_user(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    values = [data.get("nome", ""), data.get("email", ""), data.get("senha", "")]
    if not all(isinstance(value, str) and value for value in values):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return values


def parse_credentials(data):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    email, senha = data.get("email", ""), data.get("senha", "")
    if not (isinstance(email, str) and email and isinstance(senha, str) and senha):
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def parse_order(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    raw_user_id = data.get("usuario_id")
    raw_items = data.get("itens", [])
    if not raw_user_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not raw_items:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    user_id = _positive_id(raw_user_id)
    if user_id is None:
        raise ValidationError("Usuario ID inválido")
    if not isinstance(raw_items, list):
        raise ValidationError("Itens inválidos")
    items = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValidationError("Item inválido")
        product_id = _positive_id(item.get("produto_id"))
        quantity = _positive_id(item.get("quantidade"))
        if product_id is None or quantity is None:
            raise ValidationError("Item inválido: produto_id e quantidade devem ser inteiros positivos")
        items.append((product_id, quantity))
    return user_id, items


def parse_status(data):
    status = data.get("status", "") if isinstance(data, dict) else None
    if not isinstance(status, str) or status not in order_status.ALL:
        raise ValidationError("Status inválido")
    return status

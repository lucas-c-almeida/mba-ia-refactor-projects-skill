"""Response shapes: one serializer per entity, explicit fields."""
from models.money import from_cents

# The listing has always carried a "senha" field; its value is no longer the secret.
MASKED_SECRET = "********"


def product_out(product):
    return {
        "id": product["id"],
        "nome": product["nome"],
        "descricao": product["descricao"],
        "preco": from_cents(product["preco_centavos"]),
        "estoque": product["estoque"],
        "categoria": product["categoria"],
        "ativo": product["ativo"],
        "criado_em": product["criado_em"],
    }


def user_out(user):
    return {
        "id": user["id"],
        "nome": user["nome"],
        "email": user["email"],
        "senha": MASKED_SECRET,
        "tipo": user["tipo"],
        "criado_em": user["criado_em"],
    }


def order_out(order):
    return {
        "id": order["id"],
        "usuario_id": order["usuario_id"],
        "status": order["status"],
        "total": from_cents(order["total_centavos"]),
        "criado_em": order["criado_em"],
        "itens": [
            {
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": from_cents(item["preco_unitario_centavos"]),
            }
            for item in order["itens"]
        ],
    }

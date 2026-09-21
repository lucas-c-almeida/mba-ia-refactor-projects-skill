"""Conversão de objetos do domínio para o formato de resposta (uma função por entidade)."""

# O campo `senha` faz parte do formato de resposta atual; removê-lo é mudança de contrato
# (PROPOSED, NOT APPLIED). O valor nunca é devolvido: nem em claro, nem como hash.
SENHA_OCULTA = "********"


def produto(p):
    return {
        "id": p.id,
        "nome": p.nome,
        "descricao": p.descricao,
        "preco": p.preco,
        "estoque": p.estoque,
        "categoria": p.categoria,
        "ativo": p.ativo,
        "criado_em": p.criado_em,
    }


def usuario(u):
    return {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "senha": SENHA_OCULTA,
        "tipo": u.tipo,
        "criado_em": u.criado_em,
    }


def usuario_autenticado(u):
    return {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo}


def pedido(p):
    return {
        "id": p.id,
        "usuario_id": p.usuario_id,
        "status": p.status,
        "total": p.total,
        "criado_em": p.criado_em,
        "itens": [
            {
                "produto_id": item.produto_id,
                "produto_nome": item.produto_nome,
                "quantidade": item.quantidade,
                "preco_unitario": item.preco_unitario,
            }
            for item in p.itens
        ],
    }


def resumo_vendas(r):
    return {
        "total_pedidos": r.total_pedidos,
        "faturamento_bruto": r.faturamento_bruto,
        "desconto_aplicavel": r.desconto_aplicavel,
        "faturamento_liquido": r.faturamento_liquido,
        "pedidos_pendentes": r.pedidos_pendentes,
        "pedidos_aprovados": r.pedidos_aprovados,
        "pedidos_cancelados": r.pedidos_cancelados,
        "ticket_medio": r.ticket_medio,
    }

"""Boundary validation: turn request input into plain, typed values or raise ValidationError.

Messages are the ones the API already returned; the checks run in the order the API already
applied them, so the first error a client sees is unchanged.
"""
from flask import request

from models.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def corpo_json():
    """The parsed JSON object body, or None when absent, malformed or not an object."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


def corpo_obrigatorio():
    dados = corpo_json()
    if not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _texto(valor, mensagem):
    if not isinstance(valor, str):
        raise ValidationError(mensagem)
    return valor


def _numero(valor, mensagem):
    if not _is_number(valor):
        raise ValidationError(mensagem)
    return valor


def _inteiro(valor, mensagem):
    """Accept an int, an integral float, or a string of digits; anything else is rejected."""
    if isinstance(valor, bool):
        raise ValidationError(mensagem)
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor.strip())
    raise ValidationError(mensagem)


def produto(dados, categoria_padrao):
    """Presence and type checks shared by product create and update."""
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")
    return {
        "nome": _texto(dados["nome"], "Nome inválido"),
        "descricao": _texto(dados.get("descricao", ""), "Descrição inválida"),
        "preco": _numero(dados["preco"], "Preço inválido"),
        "estoque": _numero(dados["estoque"], "Estoque inválido"),
        "categoria": _texto(dados.get("categoria", categoria_padrao), "Categoria inválida"),
    }


def filtro_preco(nome_parametro):
    bruto = request.args.get(nome_parametro, None)
    if not bruto:
        return bruto
    try:
        return float(bruto)
    except ValueError:
        raise ValidationError("Parâmetro " + nome_parametro + " inválido") from None


def usuario(dados):
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {
        "nome": _texto(nome, "Nome inválido"),
        "email": _texto(email, "Email inválido"),
        "senha": _texto(senha, "Senha inválida"),
    }


def credenciais(dados):
    if dados is None:
        raise ValidationError("Dados inválidos")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return _texto(email, "Email inválido"), _texto(senha, "Senha inválida")


def pedido(dados):
    """Returns (usuario_id, [(produto_id, quantidade), ...])."""
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    usuario_id = _inteiro(usuario_id, "Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos")

    normalizados = []
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item deve ter produto_id e quantidade")
        produto_id = _inteiro(item["produto_id"], "produto_id inválido")
        quantidade = _inteiro(item["quantidade"], "Quantidade inválida")
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        normalizados.append((produto_id, quantidade))
    return usuario_id, normalizados


def status(dados):
    if dados is None:
        raise ValidationError("Status inválido")
    return dados.get("status", "")

"""Boundary validation: is this a well-formed request? Domain rules live in the controllers.

Every function takes what the request carried and returns plain values, or raises ValidationError
with the message the endpoint has always used.
"""
import math

from flask import request

from errors import ValidationError
from models.pedido import STATUS_VALIDOS
from models.produto import CATEGORIA_PADRAO


def corpo_json(nao_vazio=True):
    """The request body as a JSON object. Malformed, absent or non-object bodies are a 400."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or (nao_vazio and not dados):
        raise ValidationError("Dados inválidos")
    return dados


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and math.isfinite(valor)


def _inteiro(valor):
    """An integer given as an integer, an integral number or a string of digits; else None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and math.isfinite(valor) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str) and valor.isascii() and valor.isdigit():
        return int(valor)
    return None


def parse_produto(dados):
    for campo, mensagem in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)
    nome, preco, estoque = dados["nome"], dados["preco"], dados["estoque"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not _numero(preco):
        raise ValidationError("Preço inválido")
    if not _numero(estoque):
        raise ValidationError("Estoque inválido")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not isinstance(categoria, str):
        raise ValidationError("Categoria inválida")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque,
            "categoria": categoria}


def _preco_da_busca(texto, nome):
    if not texto:
        return None
    try:
        valor = float(texto)
    except ValueError:
        raise ValidationError(nome + " inválido")
    if not math.isfinite(valor):
        raise ValidationError(nome + " inválido")
    return valor


def parse_busca(args):
    return (
        args.get("q", ""),
        args.get("categoria", None),
        _preco_da_busca(args.get("preco_min", None), "preco_min"),
        _preco_da_busca(args.get("preco_max", None), "preco_max"),
    )


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor if isinstance(valor, str) else ""


def parse_usuario(dados):
    nome, email, senha = _texto(dados, "nome"), _texto(dados, "email"), _texto(dados, "senha")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    return nome, email, senha


def parse_login(dados):
    email, senha = _texto(dados, "email"), _texto(dados, "senha")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def _quantidade(valor):
    if not _numero(valor) or valor <= 0 or not float(valor).is_integer():
        return None
    return int(valor)


def parse_pedido(dados):
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    usuario_id = _inteiro(usuario_id)
    if usuario_id is None:
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos")
    linhas = []
    for item in itens:
        produto_id = _inteiro(item.get("produto_id")) if isinstance(item, dict) else None
        quantidade = _quantidade(item.get("quantidade")) if isinstance(item, dict) else None
        if produto_id is None or quantidade is None:
            raise ValidationError(
                "Item inválido: produto_id e quantidade (inteiro positivo) são obrigatórios")
        linhas.append({"produto_id": produto_id, "quantidade": quantidade})
    return usuario_id, linhas


def parse_status(dados):
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status

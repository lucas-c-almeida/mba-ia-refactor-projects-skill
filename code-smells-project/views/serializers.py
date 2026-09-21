"""Response representations: explicit field allow-lists per entity."""

_CAMPOS_PRODUTO = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")

# `senha` is still part of the public contract of the user endpoints; it now carries a one-way
# hash, never the password. Removing it is listed under PROPOSED, NOT APPLIED.
_CAMPOS_USUARIO = ("id", "nome", "email", "senha", "tipo", "criado_em")

_CAMPOS_USUARIO_LOGIN = ("id", "nome", "email", "tipo")


def _selecionar(registro, campos):
    return {campo: registro[campo] for campo in campos}


def produto(registro):
    return _selecionar(registro, _CAMPOS_PRODUTO)


def produtos(registros):
    return [produto(r) for r in registros]


def usuario(registro):
    return _selecionar(registro, _CAMPOS_USUARIO)


def usuarios(registros):
    return [usuario(r) for r in registros]


def usuario_autenticado(registro):
    return _selecionar(registro, _CAMPOS_USUARIO_LOGIN)

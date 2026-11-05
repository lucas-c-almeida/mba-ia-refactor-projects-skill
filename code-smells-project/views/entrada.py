"""Boundary parsing: every value read from a request is checked for type and range here,
before a controller sees it. No silent coercion: a boolean is not a number, a list is not
a string. A value that fails answers the application's own 400 ({"erro": ...})."""
import math

from flask import request

from models.erros import ErroDeValidacao
from models.produto import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS
from models.pedido import StatusPedido

# Range of an SQLite INTEGER column, and of the driver's integer binding.
INTEIRO_MAXIMO = 2 ** 63 - 1


def corpo_json():
    """The JSON body, or None when it is absent or not valid JSON."""
    return request.get_json(silent=True)


def objeto(dados, mensagem="Dados inválidos") -> dict:
    if not dados or not isinstance(dados, dict):
        raise ErroDeValidacao(mensagem)
    return dados


def id_no_intervalo(valor: int) -> bool:
    """Path identifiers: the routing converter guarantees a non-negative int."""
    return 0 <= valor <= INTEIRO_MAXIMO


def _e_numero(valor) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def texto(valor, mensagem) -> str:
    if not isinstance(valor, str):
        raise ErroDeValidacao(mensagem)
    return valor


def numero(valor, mensagem) -> float:
    if not _e_numero(valor) or not math.isfinite(valor):
        raise ErroDeValidacao(mensagem)
    return float(valor)


def inteiro(valor, mensagem, minimo=-INTEIRO_MAXIMO) -> int:
    """An integer as sent; an integral JSON number such as 3.0 is accepted as 3."""
    if isinstance(valor, float) and math.isfinite(valor) and valor.is_integer():
        valor = int(valor)
    if not _e_numero(valor) or not isinstance(valor, int) or not minimo <= valor <= INTEIRO_MAXIMO:
        raise ErroDeValidacao(mensagem)
    return valor


def numero_de_consulta(nome: str):
    """An optional numeric query parameter: absent or empty → None, as before."""
    bruto = request.args.get(nome, None)
    if not bruto:
        return None
    try:
        valor = float(bruto)
    except ValueError:
        raise ErroDeValidacao("Parâmetro " + nome + " inválido")
    if not math.isfinite(valor):
        raise ErroDeValidacao("Parâmetro " + nome + " inválido")
    return valor


def ler_filtros_de_busca() -> dict:
    return {
        "termo": request.args.get("q", ""),
        "categoria": request.args.get("categoria", None),
        "preco_min": numero_de_consulta("preco_min"),
        "preco_max": numero_de_consulta("preco_max"),
    }


def ler_produto(dados) -> dict:
    dados = objeto(dados)
    if "nome" not in dados:
        raise ErroDeValidacao("Nome é obrigatório")
    if "preco" not in dados:
        raise ErroDeValidacao("Preço é obrigatório")
    if "estoque" not in dados:
        raise ErroDeValidacao("Estoque é obrigatório")
    mensagem_categoria = "Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS))
    return {
        "nome": texto(dados["nome"], "Nome deve ser texto"),
        "descricao": texto(dados.get("descricao", ""), "Descrição deve ser texto"),
        "preco": numero(dados["preco"], "Preço deve ser um número"),
        "estoque": inteiro(dados["estoque"], "Estoque deve ser um número inteiro"),
        "categoria": texto(dados.get("categoria", CATEGORIA_PADRAO), mensagem_categoria),
    }


def ler_novo_usuario(dados) -> dict:
    dados = objeto(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ErroDeValidacao("Nome, email e senha devem ser texto")
    if not nome or not email or not senha:
        raise ErroDeValidacao("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha_informada": senha}


def ler_credenciais(dados) -> dict:
    dados = objeto(dados)
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not isinstance(email, str) or not isinstance(senha, str):
        raise ErroDeValidacao("Email e senha devem ser texto")
    if not email or not senha:
        raise ErroDeValidacao("Email e senha são obrigatórios")
    return {"email": email, "senha_informada": senha}


def ler_pedido(dados) -> dict:
    dados = objeto(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ErroDeValidacao("Usuario ID é obrigatório")
    usuario_id = inteiro(usuario_id, "Usuario ID inválido", minimo=1)
    if not itens:
        raise ErroDeValidacao("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list):
        raise ErroDeValidacao("Itens do pedido inválidos")
    itens_lidos = []
    for item in itens:
        if not isinstance(item, dict):
            raise ErroDeValidacao("Item de pedido inválido")
        itens_lidos.append({
            "produto_id": inteiro(item.get("produto_id"), "Produto do item inválido", minimo=1),
            "quantidade": inteiro(item.get("quantidade"), "Quantidade do item deve ser um inteiro positivo", minimo=1),
        })
    return {"usuario_id": usuario_id, "itens": itens_lidos}


def ler_status(dados) -> str:
    dados = objeto(dados)
    status = dados.get("status", "")
    if not isinstance(status, str) or status not in StatusPedido.TODOS:
        raise ErroDeValidacao("Status inválido")
    return status

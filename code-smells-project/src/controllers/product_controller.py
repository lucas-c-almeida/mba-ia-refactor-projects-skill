"""
Product use cases. Each method is one use case, callable with no web request in
sight (fixes AP-05 / AP-03: the original had every one of these rules embedded
directly in the Flask route handler in controllers.py).
"""
from src.models.errors import NotFoundError, ValidationError
from src.validation import (
    validar_produto_campos_basicos,
    validar_produto_criacao_extra,
)


class ProductController:
    def __init__(self, produtos):
        self._produtos = produtos

    def listar(self) -> list:
        return self._produtos.get_todos()

    def buscar(self, produto_id: int) -> dict:
        produto = self._produtos.get_por_id(produto_id)
        if produto is None:
            # This 404 carried "sucesso": False in the original; the equivalent
            # check in atualizar()/deletar() below never did. Preserved exactly.
            raise NotFoundError("Produto não encontrado", sucesso=False)
        return produto

    def criar(self, dados: dict) -> int:
        erros = validar_produto_campos_basicos(dados)
        if erros:
            raise ValidationError(erros[0])
        erros = validar_produto_criacao_extra(dados)
        if erros:
            raise ValidationError(erros[0])

        return self._produtos.criar(
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )

    def atualizar(self, produto_id: int, dados: dict) -> None:
        if self._produtos.get_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")

        # Deliberately NOT validar_produto_criacao_extra here: the original
        # atualizar_produto never checked name length or category, and adding
        # that check would reject PUT requests it accepts today (see AP-12 in
        # the audit report — proposed, not applied, for this specific gap).
        erros = validar_produto_campos_basicos(dados)
        if erros:
            raise ValidationError(erros[0])

        self._produtos.atualizar(
            produto_id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )

    def deletar(self, produto_id: int) -> None:
        if self._produtos.get_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")
        self._produtos.deletar(produto_id)

    def buscar_por_filtro(self, termo, categoria, preco_min, preco_max) -> list:
        return self._produtos.buscar(termo, categoria, preco_min, preco_max)

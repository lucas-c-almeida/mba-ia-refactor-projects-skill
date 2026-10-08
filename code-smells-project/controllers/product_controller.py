"""Product use cases. Plain values in, plain values out; no request or response objects."""

from models.errors import NotFoundError
from models.product_rules import validate_new_product, validate_product_update

PRODUCT_NOT_FOUND = "Produto não encontrado"


class ProductController:
    def __init__(self, products):
        self._products = products

    def list_products(self) -> list:
        return self._products.list_all()

    def get_product(self, product_id) -> dict:
        product = self._products.find_by_id(product_id)
        if not product:
            raise NotFoundError(PRODUCT_NOT_FOUND, failure_flag=True)
        return product

    def create_product(self, payload) -> int:
        nome, descricao, preco, estoque, categoria = validate_new_product(payload)
        return self._products.create(nome, descricao, preco, estoque, categoria)

    def update_product(self, product_id, payload) -> None:
        if not self._products.find_by_id(product_id):
            raise NotFoundError(PRODUCT_NOT_FOUND)
        nome, descricao, preco, estoque, categoria = validate_product_update(payload)
        self._products.update(product_id, nome, descricao, preco, estoque, categoria)

    def delete_product(self, product_id) -> None:
        if not self._products.find_by_id(product_id):
            raise NotFoundError(PRODUCT_NOT_FOUND)
        self._products.delete(product_id)

    def search_products(self, term, category, min_price, max_price) -> list:
        return self._products.search(term, category, min_price, max_price)

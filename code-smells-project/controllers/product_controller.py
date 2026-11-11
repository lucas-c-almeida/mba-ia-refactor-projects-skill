"""Product use cases. Plain values in, plain values out; no framework objects."""
import logging

from models.catalog import check_product_invariants
from models.errors import NotFoundError
from models.money import to_cents

logger = logging.getLogger(__name__)

NOT_FOUND = "Produto não encontrado"


class ProductController:
    def __init__(self, products):
        self._products = products

    def list_all(self):
        products = self._products.list_all()
        logger.info("Listando %d produtos", len(products))
        return products

    def get(self, product_id):
        product = self._products.find_by_id(product_id) if product_id is not None else None
        if product is None:
            raise NotFoundError(NOT_FOUND, with_success_flag=True)
        return product

    def ensure_exists(self, product_id):
        if product_id is None or self._products.find_by_id(product_id) is None:
            raise NotFoundError(NOT_FOUND)

    def search(self, term, category, min_price, max_price):
        return self._products.search(
            term,
            category,
            min_price * 100 if min_price else None,
            max_price * 100 if max_price else None,
        )

    def create(self, data):
        check_product_invariants(data["nome"], data["preco"], data["estoque"], data["categoria"])
        product_id = self._products.create(
            data["nome"], data["descricao"], to_cents(data["preco"]), data["estoque"], data["categoria"]
        )
        logger.info("Produto criado com ID: %s", product_id)
        return product_id

    def update(self, product_id, data):
        self.ensure_exists(product_id)
        check_product_invariants(data["nome"], data["preco"], data["estoque"], data["categoria"])
        self._products.update(
            product_id, data["nome"], data["descricao"], to_cents(data["preco"]), data["estoque"], data["categoria"]
        )

    def delete(self, product_id):
        self.ensure_exists(product_id)
        self._products.delete(product_id)
        logger.info("Produto %s deletado", product_id)

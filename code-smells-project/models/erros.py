"""Domain error taxonomy. The error boundary (middlewares/tratamento_de_erros.py) maps it
to HTTP responses in one place."""


class ErroDeDominio(Exception):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroDeValidacao(ErroDeDominio):
    """The request is malformed, or a value breaks an invariant the domain states."""


class ErroDeRegraDeNegocio(ErroDeDominio):
    """A well-formed request the domain refuses (unknown product, insufficient stock)."""

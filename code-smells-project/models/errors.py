"""Domain error taxonomy. The delivery layer maps these to protocol responses."""


class AppError(Exception):
    """Base class. `sucesso_false` keeps the legacy body shape of routes that add it."""

    def __init__(self, mensagem, sucesso_false=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.sucesso_false = sucesso_false


class ValidationError(AppError):
    """The input is invalid."""


class NotFoundError(AppError):
    """The requested record does not exist."""


class UnauthorizedError(AppError):
    """Credentials were not accepted."""


class ForbiddenError(AppError):
    """The operation is not allowed for the caller."""


class ServicoIndisponivelError(AppError):
    """A dependency (the datastore) failed. Carries a safe message, never the driver text."""

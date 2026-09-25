"""
A small domain error taxonomy, owned by the domain layer (fixes AP-09: previously
every handler caught the base Exception and returned raw exception text). Each type
maps to exactly one HTTP status in src/middlewares/errors.py, preserving the status
codes the original returned for the same situations.

`sucesso`, when given, is carried through into the response body as-is. The original
code was itself inconsistent about whether an error body included a `"sucesso"` key
(compare buscar_produto's 404, which had it, with atualizar_produto's 404, which did
not) — that inconsistency is preserved here on purpose, call site by call site,
because unifying it would change the shape of responses existing clients observe
today (see AP-12 / the report's note on AP-09's contract). `sucesso=None` (the
default) omits the key entirely, matching the call sites that never had it.
"""


class DomainError(Exception):
    """Base for every error the domain raises on purpose."""

    def __init__(self, message: str, sucesso: bool = None):
        super().__init__(message)
        self.message = message
        self.sucesso = sucesso


class ValidationError(DomainError):
    """Malformed or invalid input. Maps to 400, like the original's ad-hoc checks."""


class NotFoundError(DomainError):
    """A referenced record does not exist. Maps to 404."""


class NotAuthenticatedError(DomainError):
    """Credentials did not check out. Maps to 401, like the original login route."""


class ConflictError(DomainError):
    """The request cannot be satisfied given the current state (e.g. insufficient
    stock). Maps to 400, matching the original's behaviour for this situation."""

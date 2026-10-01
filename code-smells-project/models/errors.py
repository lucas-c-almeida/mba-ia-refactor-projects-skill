"""Domain error taxonomy (AP-09). Mapped to HTTP responses in one place:
middlewares/error_handler.py."""


class AppError(Exception):
    status = 500

    def __init__(self, message, extra=None):
        super().__init__(message)
        self.message = message
        self.extra = dict(extra or {})

    def body(self):
        body = {"erro": self.message}
        body.update(self.extra)
        return body


class ValidationError(AppError):
    status = 400


class BusinessRuleError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class AuthenticationError(AppError):
    status = 401


class HealthCheckError(AppError):
    """The health check keeps its own error body: {"status": "erro", "detalhes": ...}."""

    status = 500

    def body(self):
        return {"status": "erro", "detalhes": self.message}


# The body flag some error responses carried in the original API; kept so the shape is unchanged.
FALHA = {"sucesso": False}

"""Error taxonomy shared by every layer. The error boundary maps it to responses in one place."""


class AppError(Exception):
    """An error the application raises on purpose. ``status`` and ``body()`` are its contract."""

    status = 500

    def __init__(self, message, sucesso=None):
        super().__init__(message)
        self.message = message
        self.sucesso = sucesso

    def body(self):
        body = {"erro": self.message}
        if self.sucesso is not None:
            body["sucesso"] = self.sucesso
        return body


class ValidationError(AppError):
    status = 400


class AuthenticationError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409


class HealthCheckError(AppError):
    """The health endpoint has its own error body shape, which clients may read."""

    status = 500

    def body(self):
        return {"status": "erro", "detalhes": self.message}

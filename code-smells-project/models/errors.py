"""Domain error taxonomy. The error boundary (middlewares/error_handler.py) maps these
to responses; no other layer chooses a status code for an error."""


class AppError(Exception):
    status = 500

    def __init__(self, message, with_success_flag=False):
        super().__init__(message)
        self.message = message
        # Some of the application's own error bodies carry "sucesso": false and some do
        # not; the flag keeps each response exactly as clients already receive it.
        self.with_success_flag = with_success_flag


class ValidationError(AppError):
    status = 400


class BusinessRuleError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class AuthenticationError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class DatabaseUnavailableError(AppError):
    status = 500

"""Domain error taxonomy (RP-09). Mapped to responses in one place: middlewares/error_handler.py."""

# Messages shared by several use cases (the API's existing wording).
INVALID_DATA = 'Dados inválidos'
TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'
UPDATE_FAILED = 'Erro ao atualizar'
DELETE_FAILED = 'Erro ao deletar'


class AppError(Exception):
    status = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status = 400


class NotAuthenticated(AppError):
    status = 401


class Forbidden(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409


class PersistenceError(AppError):
    status = 500

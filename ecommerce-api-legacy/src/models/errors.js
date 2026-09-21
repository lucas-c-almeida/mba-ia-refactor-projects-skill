// Domain error taxonomy. (AP-09 -> RP-09)
// Each error carries the client-facing message the API already used; the mapping to HTTP lives
// only in middlewares/errorHandler.js.

class AppError extends Error {
    constructor(message, cause) {
        super(message);
        this.name = this.constructor.name;
        if (cause) this.cause = cause;
    }
}

class InvalidInputError extends AppError {}
class NotFoundError extends AppError {}
class PaymentDeclinedError extends AppError {}
class DependencyError extends AppError {} // a datastore failure

// Client-facing message for a generic datastore failure, shared by every use case.
const DB_ERROR_MESSAGE = 'Erro DB';

module.exports = {
    AppError, InvalidInputError, NotFoundError, PaymentDeclinedError, DependencyError, DB_ERROR_MESSAGE,
};

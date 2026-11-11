// Domain error taxonomy. The error boundary (middlewares/errorHandler.js) maps it to responses.
// Messages are the bodies the application has always returned on purpose: they are contract.

class AppError extends Error {
    constructor(message, status) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(message, 400); }
}

class ForbiddenError extends AppError {
    constructor(message = 'Forbidden') { super(message, 403); }
}

class NotFoundError extends AppError {
    constructor(message = 'Not Found') { super(message, 404); }
}

// A datastore failure. `message` is the body the client receives; `cause` keeps the driver error
// for the log only.
class DependencyError extends AppError {
    constructor(message = 'Erro DB', cause) {
        super(message, 500);
        this.cause = cause;
    }
}

module.exports = {
    AppError, ValidationError, PaymentDeclinedError, ForbiddenError, NotFoundError, DependencyError,
};

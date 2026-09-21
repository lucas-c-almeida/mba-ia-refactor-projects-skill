// Domain error taxonomy (AP-09 — RP-09). The message is what the client receives; the status is
// mapped once, in middlewares/errorBoundary.js. Messages are the ones the API has always returned.

class AppError extends Error {
    constructor(message, status, cause) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
        if (cause) this.cause = cause;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(message, 400); }
}

// The generic client-facing message of a datastore failure, as the API has always returned it.
const GENERIC_DB_ERROR = 'Erro DB';

// A datastore failure. The message is the safe, client-facing one; the driver error is kept as
// `cause` for the log and never sent to the client.
class DependencyError extends AppError {
    constructor(message, cause) { super(message, 500, cause); }
}

module.exports = {
    AppError, ValidationError, NotFoundError, PaymentDeclinedError, DependencyError, GENERIC_DB_ERROR,
};

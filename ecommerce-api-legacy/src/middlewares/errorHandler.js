// The single error boundary: domain taxonomy -> HTTP, in one place. (AP-09 -> RP-09)
// Status codes and plain-text bodies are the ones the API already returned.
const { STATUS_CODES } = require('node:http');
const {
    AppError, InvalidInputError, NotFoundError, PaymentDeclinedError, DependencyError,
} = require('../models/errors');

const STATUS_BY_ERROR = new Map([
    [InvalidInputError, 400],
    [PaymentDeclinedError, 400],
    [NotFoundError, 404],
    [DependencyError, 500],
]);

function statusFor(err) {
    for (const [ErrorType, status] of STATUS_BY_ERROR) {
        if (err instanceof ErrorType) return status;
    }
    return 500;
}

function errorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) {
            const status = statusFor(err);
            if (status >= 500) logger.error(`${req.method} ${req.path} failed:`, err.cause || err);
            return res.status(status).send(err.message);
        }
        // Client errors raised by the body parser (malformed JSON, oversized body): same status as
        // the framework default, without the stack trace its default page used to include.
        if (err && err.type && Number.isInteger(err.status) && err.status >= 400 && err.status < 500) {
            return res.status(err.status).send(STATUS_CODES[err.status]);
        }
        logger.error(`${req.method} ${req.path} failed:`, err);
        return res.status(500).send('Internal Server Error');
    };
}

module.exports = { errorHandler };

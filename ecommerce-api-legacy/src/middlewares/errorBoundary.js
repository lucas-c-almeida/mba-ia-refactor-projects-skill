// The single error boundary (AP-09, AP-18 — RP-09, RP-17). Registered last.
// Domain errors keep the status and plain-text body the API has always returned. Anything else —
// including the framework's own errors, such as a malformed JSON body — keeps its status code but
// gets a generic body: no stack trace, driver message or file path ever reaches the client.

const http = require('http');
const { AppError } = require('../models/errors');

module.exports = (logger) => (err, req, res, next) => {
    if (res.headersSent) return next(err);

    // Log the stack, never the error object itself: framework errors carry the raw request body
    // (which may hold a card number or a password) as a property (AP-08).
    const where = `${req.method} ${req.path}`;

    if (err instanceof AppError) {
        if (err.status >= 500) logger.error(`${where}: ${err.message}`, (err.cause || err).stack);
        return res.status(err.status).send(err.message);
    }

    const status = Number.isInteger(err.status) && err.status >= 400 && err.status < 600 ? err.status : 500;
    if (status >= 500) logger.error(`${where}: unhandled error`, err.stack);
    else logger.warn(`${where}: ${status} ${err.type || err.name}`);
    return res.status(status).send(http.STATUS_CODES[status]);
};

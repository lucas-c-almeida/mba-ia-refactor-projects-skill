'use strict';

const http = require('node:http');
const { AppError } = require('../errors');

const INTERNAL_ERROR_STATUS = 500;

// The single error boundary, registered last (AP-09, AP-18).
// - Errors the application raises on purpose keep their status and text.
// - Errors raised by the framework with a client status (for example a malformed JSON body)
//   keep their status; the body is the status text, never the stack trace.
// - Anything else is logged in full and answered with a generic 500.
module.exports = (logger) => (err, req, res, next) => {
    if (res.headersSent) return next(err);

    if (err instanceof AppError) {
        if (err.status >= INTERNAL_ERROR_STATUS) logger.error(err.message, err.cause || err);
        return res.status(err.status).send(err.message);
    }

    const clientStatus = Number(err.status || err.statusCode);
    if (clientStatus >= 400 && clientStatus < INTERNAL_ERROR_STATUS) {
        return res.status(clientStatus).send(http.STATUS_CODES[clientStatus]);
    }

    logger.error('unhandled error', err);
    return res.status(INTERNAL_ERROR_STATUS).send(http.STATUS_CODES[INTERNAL_ERROR_STATUS]);
};

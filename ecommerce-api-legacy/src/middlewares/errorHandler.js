// The error boundary, registered last. The application's own errors keep their status and body;
// anything else keeps its status and gets a generic body. Details go to the log only.
const http = require('http');
const { AppError } = require('../models/errors');

const INTERNAL_ERROR = 500;

function createErrorHandler(logger) {
    // Express recognizes an error handler by its four parameters.
    return (err, req, res, _next) => {
        if (err instanceof AppError) {
            if (err.status >= INTERNAL_ERROR) {
                logger.error(`[${req.id}] ${err.message}: ${err.cause ? err.cause.message : 'no cause'}`);
            }
            return res.status(err.status).send(err.message);
        }

        const status = Number.isInteger(err.status) && err.status >= 400 && err.status < 600
            ? err.status
            : INTERNAL_ERROR;
        logger.error(`[${req.id}] ${status} ${err.name}: ${err.message}`);
        res.status(status).send(http.STATUS_CODES[status]);
    };
}

module.exports = { createErrorHandler };

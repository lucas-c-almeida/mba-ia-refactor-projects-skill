const http = require('http');
const { AppError } = require('../errors');

const SERVER_ERROR_STATUS = 500;

// The single place where errors become responses. Intentional errors keep their status and text;
// anything else is disclosed as nothing more than its status line. Server-side failures are logged
// in full, with their cause.
function errorBoundary(logger = console) {
    // Express recognises an error handler by its four parameters.
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) {
            if (err.status >= SERVER_ERROR_STATUS) logger.error(err, err.cause);
            return res.status(err.status).send(err.message);
        }
        // Errors raised by the framework itself, such as a malformed JSON body.
        const status = Number.isInteger(err.status) && err.status >= 400 && err.status < 500
            ? err.status
            : SERVER_ERROR_STATUS;
        if (status >= SERVER_ERROR_STATUS) logger.error(err);
        return res.status(status).send(http.STATUS_CODES[status]);
    };
}

module.exports = { errorBoundary };

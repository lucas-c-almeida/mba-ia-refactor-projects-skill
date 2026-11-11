// Correlation id: one per request, returned in a header and written in every log line about it.
const crypto = require('crypto');

const REQUEST_ID_HEADER = 'X-Request-Id';

function requestId(req, res, next) {
    req.id = crypto.randomUUID();
    res.set(REQUEST_ID_HEADER, req.id);
    next();
}

module.exports = { requestId };

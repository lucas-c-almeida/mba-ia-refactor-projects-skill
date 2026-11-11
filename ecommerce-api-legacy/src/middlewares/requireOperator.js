// Guard for privileged operations: requires the operator credential from configuration,
// compared in constant time. With no credential configured, the guard stays closed.
const crypto = require('crypto');
const { ForbiddenError } = require('../models/errors');

const OPERATOR_HEADER = 'x-operator-token';

function requireOperator(operatorToken) {
    const expected = Buffer.from(operatorToken || '');
    return (req, _res, next) => {
        const given = Buffer.from(req.get(OPERATOR_HEADER) || '');
        const allowed = expected.length > 0
            && given.length === expected.length
            && crypto.timingSafeEqual(given, expected);
        next(allowed ? undefined : new ForbiddenError());
    };
}

module.exports = { requireOperator };

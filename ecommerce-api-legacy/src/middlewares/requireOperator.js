const crypto = require('crypto');

const OPERATOR_HEADER = 'x-operator-token';

// Guard for privileged operations (RP-04). With no operator token configured it is closed: 403.
function requireOperator(operatorToken) {
    const wanted = Buffer.from(operatorToken || '');

    return (req, res, next) => {
        const given = Buffer.from(req.get(OPERATOR_HEADER) || '');
        const allowed = wanted.length > 0
            && given.length === wanted.length
            && crypto.timingSafeEqual(given, wanted);
        if (!allowed) return res.status(403).json({ error: 'forbidden' });
        return next();
    };
}

module.exports = { requireOperator, OPERATOR_HEADER };

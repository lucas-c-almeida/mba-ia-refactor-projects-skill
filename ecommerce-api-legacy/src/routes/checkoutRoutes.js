'use strict';

const express = require('express');
const { ValidationError } = require('../errors');

const isScalar = (value) => typeof value === 'string' || typeof value === 'number';

// Boundary schema for POST /api/checkout. Field names are the public contract.
// Presence rules are the original ones; the type rules reject only values no legitimate
// client sends (a card number that is not a string, an object where a value is expected).
function parseCheckout(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};
    if (!usr || !eml || !courseId || !card) throw new ValidationError();
    if (typeof card !== 'string') throw new ValidationError();
    if (!isScalar(usr) || !isScalar(eml) || !isScalar(courseId)) throw new ValidationError();
    if (pwd !== undefined && pwd !== null && !isScalar(pwd)) throw new ValidationError();
    return {
        name: usr,
        email: eml,
        password: pwd ? String(pwd) : undefined,
        courseId,
        cardNumber: card,
    };
}

module.exports = (checkoutController) => {
    const router = express.Router();

    router.post('/api/checkout', async (req, res, next) => {
        try {
            const result = await checkoutController.checkout(parseCheckout(req.body));
            res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
        } catch (err) {
            next(err);
        }
    });

    return router;
};

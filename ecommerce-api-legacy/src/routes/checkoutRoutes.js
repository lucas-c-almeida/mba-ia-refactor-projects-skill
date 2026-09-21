// POST /api/checkout — parse, call the use case, render. (AP-05 -> RP-05, AP-11 -> RP-11)
const express = require('express');
const { InvalidInputError } = require('../models/errors');

// Public request field names (usr, eml, pwd, c_id, card) are part of the contract and kept as-is.
function parseCheckoutRequest(body = {}) {
    const input = {
        name: body.usr,
        email: body.eml,
        password: body.pwd,
        courseId: body.c_id,
        cardNumber: body.card,
    };
    if (!input.name || !input.email || !input.courseId || !input.cardNumber) {
        throw new InvalidInputError('Bad Request');
    }
    return input;
}

function checkoutRoutes(checkoutController) {
    const router = express.Router();

    router.post('/api/checkout', async (req, res, next) => {
        try {
            const { enrollmentId } = await checkoutController.checkout(parseCheckoutRequest(req.body));
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { checkoutRoutes };

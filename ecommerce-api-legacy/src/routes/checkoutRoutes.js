// POST /api/checkout — delivery only: parse, call the use case, render (AP-05 — RP-05).
// The request field names (usr, eml, pwd, c_id, card) are public contract and stay as they are.

const { ValidationError } = require('../models/errors');

// Boundary schema (AP-11 — RP-11). Presence rules are the original ones; the type rules reject
// only values of the wrong type, which no legitimate client sends (a non-string card or password
// used to crash the whole process).
function parseCheckoutRequest(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};
    if (!usr || !eml || !courseId || !card) throw new ValidationError();
    if (typeof usr !== 'string' || typeof eml !== 'string' || typeof card !== 'string') {
        throw new ValidationError();
    }
    if (pwd && typeof pwd !== 'string') throw new ValidationError();
    return { name: usr, email: eml, password: pwd, courseId, cardNumber: card };
}

module.exports = function registerCheckoutRoutes(router, checkoutController) {
    router.post('/api/checkout', async (req, res, next) => {
        try {
            const input = parseCheckoutRequest(req.body);
            const { enrollmentId } = await checkoutController.checkout(input);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            next(err);
        }
    });
};

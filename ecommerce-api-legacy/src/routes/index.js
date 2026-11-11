// Route declarations: parse the request, call one controller method, render the response.
const express = require('express');
const { parseCheckout, parseUserId } = require('./validators');
const { requireOperator } = require('../middlewares/requireOperator');

const USER_DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';
const CHECKOUT_SUCCESS_MESSAGE = 'Sucesso';

// Express 4 does not forward rejected promises to the error boundary by itself.
const handle = (fn) => (req, res, next) => Promise.resolve(fn(req, res)).catch(next);

function createRouter({ checkout, reports, users, operatorToken }) {
    const router = express.Router();
    const operatorOnly = requireOperator(operatorToken);

    router.post('/api/checkout', handle(async (req, res) => {
        const { enrollmentId } = await checkout.checkout(parseCheckout(req.body));
        res.status(200).json({ msg: CHECKOUT_SUCCESS_MESSAGE, enrollment_id: enrollmentId });
    }));

    router.get('/api/admin/financial-report', operatorOnly, handle(async (req, res) => {
        res.json(await reports.financialReport());
    }));

    router.delete('/api/users/:id', operatorOnly, handle(async (req, res) => {
        await users.deleteUser(parseUserId(req.params.id));
        res.send(USER_DELETED_MESSAGE);
    }));

    return router;
}

module.exports = { createRouter };

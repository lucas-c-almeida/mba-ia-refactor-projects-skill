'use strict';

const express = require('express');
const { parseCheckoutRequest, parseUserId } = require('./requestParsers');
const { asyncHandler } = require('../middlewares/asyncHandler');

const USER_DELETED_MESSAGE =
  'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

// Delivery layer: parse -> call one controller method -> render. Paths, methods, status codes
// and bodies are the application's public contract and are unchanged.
function buildRouter({ checkout, reports, users, requireOperator }) {
  const router = express.Router();

  router.post('/api/checkout', asyncHandler(async (req, res) => {
    const enrollmentId = await checkout.checkout(parseCheckoutRequest(req.body));
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
  }));

  router.get('/api/admin/financial-report', requireOperator, asyncHandler(async (req, res) => {
    res.json(await reports.financialReport());
  }));

  router.delete('/api/users/:id', requireOperator, asyncHandler(async (req, res) => {
    await users.deleteUser(parseUserId(req.params.id));
    res.send(USER_DELETED_MESSAGE);
  }));

  return router;
}

module.exports = { buildRouter };

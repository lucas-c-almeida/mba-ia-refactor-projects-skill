'use strict';

const { AppError } = require('../errors');
const { asyncHandler } = require('../middlewares/asyncHandler');

const BAD_REQUEST = 'Bad Request';
const USER_DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

/**
 * Boundary validation for the checkout body. The request field names are part
 * of the public contract. Presence is checked as before; on top of that,
 * values of the wrong type (which used to crash the process) are rejected
 * with the same 400.
 */
function parseCheckoutBody(body) {
  const { usr, eml, pwd, c_id: courseId, card } = body;
  if (!usr || !eml || !courseId || !card) throw new AppError(BAD_REQUEST, 400);
  if (typeof card !== 'string') throw new AppError(BAD_REQUEST, 400);
  if (pwd && typeof pwd !== 'string') throw new AppError(BAD_REQUEST, 400);
  return { name: usr, email: eml, password: pwd, courseId, card };
}

/** Route declarations only: parse, call one controller method, render. */
function registerRoutes(app, { checkout, reports, users, requireOperator }) {
  app.post('/api/checkout', asyncHandler(async (req, res) => {
    const { enrollmentId } = await checkout.checkout(parseCheckoutBody(req.body));
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
  }));

  app.get('/api/admin/financial-report', requireOperator, asyncHandler(async (req, res) => {
    res.json(await reports.financialReport());
  }));

  app.delete('/api/users/:id', requireOperator, asyncHandler(async (req, res) => {
    await users.deleteUser(req.params.id);
    res.send(USER_DELETED_MESSAGE);
  }));
}

module.exports = { registerRoutes, parseCheckoutBody };

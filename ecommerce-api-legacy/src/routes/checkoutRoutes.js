'use strict';

const { Router } = require('express');
const { ValidationError } = require('../errors');

/**
 * Delivery boundary for checkout — resolves AP-03/AP-05 (original: parsing, rules and
 * persistence were interleaved in src/AppManager.js:28-78). Reads as parse -> call -> render.
 *
 * Presence validation reproduces the original's exact check (src/AppManager.js:35:
 * `if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request")`) byte for byte
 * — same status, same body. The one addition — rejecting a `c_id` that cannot be a course
 * id at all — is AP-11's safe half: a value that is invalid on its face fails downstream
 * today anyway (a lookup that can never match), so rejecting it here earlier changes
 * nothing a legitimate client observes (`04-architecture-guidelines.md` §6). `pwd` stays
 * optional, exactly as the original left it; requiring it would reject a request some
 * client sends today, so that stays a product decision (see the AP-11 finding's Contract
 * field in reports/audit-latest.md).
 */
function checkoutRoutes(controller) {
  const router = Router();

  router.post('/api/checkout', async (req, res, next) => {
    try {
      const {
        usr, eml, pwd, c_id: cId, card,
      } = req.body || {};

      if (!usr || !eml || !cId || !card) throw new ValidationError('Bad Request');

      const courseId = Number(cId);
      if (!Number.isInteger(courseId) || courseId <= 0) throw new ValidationError('Bad Request');

      const result = await controller.checkout({
        userName: usr, email: eml, password: pwd, courseId, cardNumber: card,
      });
      res.status(200).json({ msg: 'Sucesso', enrollment_id: result.enrollmentId });
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = { checkoutRoutes };

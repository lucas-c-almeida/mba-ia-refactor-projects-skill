'use strict';

const { Router } = require('express');

/**
 * Delivery boundary for user deletion. Deliberately unchanged in behaviour from the
 * original (src/AppManager.js:131-137): no authorization check (AP-04) and the same fixed
 * response regardless of outcome (AP-09) — both fixes are `PROPOSED, NOT APPLIED` in
 * reports/audit-latest.md, because the application has no identity model and today's single
 * observable outcome would change either way. See that report before changing this route.
 */
function userRoutes(controller) {
  const router = Router();

  router.delete('/api/users/:id', async (req, res, next) => {
    try {
      await controller.deleteUser(req.params.id);
      res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = { userRoutes };

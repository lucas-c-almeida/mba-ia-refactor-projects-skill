'use strict';

const { Router } = require('express');

/** Delivery boundary for the financial report. Parse -> call -> render; no rules here. */
function financialReportRoutes(controller) {
  const router = Router();

  router.get('/api/admin/financial-report', async (req, res, next) => {
    try {
      const report = await controller.report();
      res.status(200).json(report);
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = { financialReportRoutes };

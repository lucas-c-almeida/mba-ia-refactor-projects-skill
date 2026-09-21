// GET /api/admin/financial-report. (AP-05 -> RP-05)
// No authentication: adding it is PROPOSED, NOT APPLIED (AP-04, contract-changing).
const express = require('express');

function adminRoutes(reportController) {
    const router = express.Router();

    router.get('/api/admin/financial-report', async (req, res, next) => {
        try {
            res.json(await reportController.financialReport());
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { adminRoutes };

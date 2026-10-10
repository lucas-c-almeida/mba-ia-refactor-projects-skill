const { asyncHandler } = require('../middlewares/asyncHandler');

// Privileged operations: every route here sits behind the operator guard (closed unless configured).
function adminRoutes(router, { reportController, userController, operatorGuard }) {
    router.get('/api/admin/financial-report', operatorGuard, asyncHandler(async (req, res) => {
        res.json(await reportController.financialReport());
    }));

    router.delete('/api/users/:id', operatorGuard, asyncHandler(async (req, res) => {
        await userController.remove(req.params.id);
        res.send('Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.');
    }));

    return router;
}

module.exports = { adminRoutes };

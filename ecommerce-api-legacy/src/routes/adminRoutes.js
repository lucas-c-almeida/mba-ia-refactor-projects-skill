// Administrative routes — delivery only (AP-05 — RP-05).
// PROPOSED, NOT APPLIED (AP-04): these routes have no authentication, because the application has
// no identity model and adding one would reject every current client.

const USER_DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

module.exports = function registerAdminRoutes(router, { reportController, userController }) {
    router.get('/api/admin/financial-report', async (req, res, next) => {
        try {
            res.json(await reportController.financialReport());
        } catch (err) {
            next(err);
        }
    });

    router.delete('/api/users/:id', async (req, res, next) => {
        try {
            await userController.deleteUser(req.params.id);
            res.send(USER_DELETED_MESSAGE);
        } catch (err) {
            next(err);
        }
    });
};

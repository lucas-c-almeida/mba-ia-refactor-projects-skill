// DELETE /api/users/:id. (AP-05 -> RP-05)
// No authentication: adding it is PROPOSED, NOT APPLIED (AP-04, contract-changing).
const express = require('express');

// Response text is part of the public contract and kept verbatim.
const USER_DELETED_MESSAGE = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

function userRoutes(userController) {
    const router = express.Router();

    router.delete('/api/users/:id', async (req, res, next) => {
        try {
            await userController.deleteUser(req.params.id);
            res.send(USER_DELETED_MESSAGE);
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { userRoutes };

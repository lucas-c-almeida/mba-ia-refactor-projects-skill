'use strict';

const express = require('express');
const { ValidationError } = require('../errors');

// The response text is the public contract and is kept as clients receive it today.
const USER_DELETED = 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.';

// User ids are integer primary keys; anything else is invalid on its face (AP-11).
const USER_ID_PATTERN = /^[0-9]+$/;

module.exports = (userController) => {
    const router = express.Router();

    router.delete('/api/users/:id', async (req, res, next) => {
        try {
            if (!USER_ID_PATTERN.test(req.params.id)) throw new ValidationError();
            await userController.deleteUser(Number(req.params.id));
            res.send(USER_DELETED);
        } catch (err) {
            next(err);
        }
    });

    return router;
};

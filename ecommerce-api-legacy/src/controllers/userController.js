// Use case: remove an account (operator only; the guard is applied by the route).
const { DependencyError } = require('../models/errors');

function createUserController({ users }) {
    return {
        async deleteUser(id) {
            try {
                await users.deleteById(id);
            } catch (err) {
                throw new DependencyError('Erro DB', err);
            }
        },
    };
}

module.exports = { createUserController };

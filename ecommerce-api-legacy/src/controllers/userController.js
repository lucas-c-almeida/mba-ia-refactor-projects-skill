// User administration use case (AP-05 — RP-05). A datastore failure now propagates instead of
// being reported as a successful deletion (AP-09).

const { DependencyError, GENERIC_DB_ERROR } = require('../models/errors');

class UserController {
    constructor({ users }) {
        this.users = users;
    }

    async deleteUser(id) {
        try {
            await this.users.deleteById(id);
        } catch (err) {
            throw new DependencyError(GENERIC_DB_ERROR, err);
        }
    }
}

module.exports = { UserController };

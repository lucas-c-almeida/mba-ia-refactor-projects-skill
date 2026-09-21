// User use cases. (AP-05 -> RP-05)
const { DependencyError, DB_ERROR_MESSAGE } = require('../models/errors');

class UserController {
    constructor({ transaction, users }) {
        this.transaction = transaction;
        this.users = users;
    }

    // Preserved: related enrollments/payments are left in place and an unknown id is not an error.
    // Both are PROPOSED, NOT APPLIED (see report) — they need a product/accounting decision.
    async deleteUser(id) {
        try {
            await this.transaction(() => this.users.deleteById(id));
        } catch (err) {
            throw new DependencyError(DB_ERROR_MESSAGE, err);
        }
    }
}

module.exports = { UserController };

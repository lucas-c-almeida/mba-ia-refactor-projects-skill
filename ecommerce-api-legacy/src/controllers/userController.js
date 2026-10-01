'use strict';

class UserController {
    constructor({ users }) {
        this.users = users;
    }

    // Deletes the user row only. What happens to the user's enrollments and payments is a
    // product decision, proposed in the audit report rather than decided here.
    async deleteUser(id) {
        await this.users.deleteById(id);
    }
}

module.exports = { UserController };

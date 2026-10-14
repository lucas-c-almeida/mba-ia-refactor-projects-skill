'use strict';

/** Account removal use case. Enrollments and payments are left as they were (see the audit report). */
class UserController {
  constructor({ users }) {
    this.users = users;
  }

  async deleteUser(id) {
    await this.users.deleteById(id);
  }
}

module.exports = { UserController };

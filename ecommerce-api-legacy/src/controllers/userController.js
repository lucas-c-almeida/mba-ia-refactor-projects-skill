'use strict';

const { PersistenceError } = require('../models/errors');

class UserController {
  constructor({ users }) {
    this.users = users;
  }

  /**
   * Deletes the account. Its enrollments and payments are kept, as before: what should happen to
   * them is a product decision recorded as a proposal in the audit report.
   */
  async deleteUser(id) {
    try {
      await this.users.deleteById(id);
    } catch (err) {
      throw new PersistenceError('Erro DB', err);
    }
  }
}

module.exports = { UserController };

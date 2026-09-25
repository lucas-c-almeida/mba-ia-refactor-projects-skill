'use strict';

/**
 * Resolves AP-03/AP-06 (original: src/AppManager.js:131-137, the delete was issued directly
 * inside the route handler against a connection the class owned itself).
 *
 * Does NOT fix AP-04 (no authorization check) or AP-09 (the delete's own error is not
 * surfaced) — both are `PROPOSED, NOT APPLIED` in reports/audit-latest.md, because the
 * application has no identity model and today's single observable outcome (200, fixed
 * text, regardless of what happened) would change. This method is therefore a faithful
 * move of the original behaviour, not a fix of it.
 */
class UserController {
  constructor({ users }) {
    this.users = users;
  }

  async deleteUser(id) {
    await this.users.deleteById(id);
  }
}

module.exports = { UserController };

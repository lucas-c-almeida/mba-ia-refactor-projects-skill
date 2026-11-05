'use strict';

class UserRepository {
  constructor(db) {
    this.db = db;
  }

  async findIdByEmail(email) {
    const row = await this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    return row ? row.id : null;
  }

  async create({ name, email, passwordHash }) {
    const { lastId } = await this.db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash],
    );
    return lastId;
  }

  async deleteById(id) {
    await this.db.run('DELETE FROM users WHERE id = ?', [id]);
  }
}

module.exports = { UserRepository };

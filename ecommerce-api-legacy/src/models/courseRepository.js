'use strict';

const { ACTIVE } = require('./schema');

class CourseRepository {
  constructor(db) {
    this.db = db;
  }

  async findActiveById(id) {
    const row = await this.db.get(
      'SELECT id, title, price_cents FROM courses WHERE id = ? AND active = ?', [id, ACTIVE],
    );
    return row ? { id: row.id, title: row.title, priceCents: row.price_cents } : null;
  }
}

module.exports = { CourseRepository };

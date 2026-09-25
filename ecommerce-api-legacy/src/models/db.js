'use strict';

const { hashPassword } = require('./password');
const { toCents } = require('./money');

/**
 * Schema and seed data. Moved from src/AppManager.js:10-23 (original) with no behavioural
 * change beyond what the Phase 2 audit and the Phase 3 re-audit authorized:
 *
 *  - AP-20 (safe half, applied): a UNIQUE index on users.email (the column the application
 *    already treats as an identity — see reports/audit-latest.md). The foreign keys below
 *    are DECLARED for documentation but never enforced (no `PRAGMA foreign_keys = ON` is
 *    issued anywhere in this codebase, matching the original exactly): enabling enforcement
 *    changes what DELETE /api/users/:id does to a user with existing enrollments, which is
 *    `PROPOSED, NOT APPLIED` pending a product decision on cascade/restrict/detach.
 *  - AP-20 (money): price and amount are stored as integer cents (`price_cents`,
 *    `amount_cents`) instead of `REAL`. See models/money.js.
 *  - AP-01, `missed-in-phase-2` (found by the first Phase 3 re-audit, not by Phase 2): the
 *    seed's own user row stored its password as the plain literal "123"
 *    (src/AppManager.js:18, original) — a credential literal reaching the runtime datastore,
 *    same signal as the finding Phase 2 did catch on utils.js:1-7, just missed on this line.
 *    Fixed here in the bounded fix loop: hashed with the same KDF as every other password
 *    (models/password.js). Nothing reads this value back through the HTTP surface (the
 *    seeded user is only ever looked up by email, never authenticated against this
 *    password — see checkoutController.js), so this is not observable and required no new
 *    surface entry to verify.
 */

function initSchema(db) {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
      db.run('CREATE UNIQUE INDEX users_email_key ON users (email)');
      db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price_cents INTEGER, active INTEGER)');
      // The FOREIGN KEY clauses below are real SQL, declared for documentation. SQLite does
      // not enforce a foreign key unless the connection also issues `PRAGMA foreign_keys =
      // ON` — this codebase never does (see the module comment above) — so declaring them
      // here changes nothing about the running application's behaviour by itself.
      db.run(
        'CREATE TABLE enrollments ('
        + 'id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER, '
        + 'FOREIGN KEY (user_id) REFERENCES users(id), '
        + 'FOREIGN KEY (course_id) REFERENCES courses(id)'
        + ')',
      );
      db.run(
        'CREATE TABLE payments ('
        + 'id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount_cents INTEGER, status TEXT, '
        + 'FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)'
        + ')',
      );
      db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

      db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')],
      );
      db.run(
        'INSERT INTO courses (title, price_cents, active) VALUES (?, ?, 1), (?, ?, 1)',
        ['Clean Architecture', toCents(997.00), 'Docker', toCents(497.00)],
      );
      db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
      db.run(
        'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
        [1, toCents(997.00), 'PAID'],
        (err) => {
          if (err) reject(err);
          else resolve();
        },
      );
    });
  });
}

module.exports = { initSchema };

'use strict';

const { PaymentStatus } = require('./payment');
const { toCents } = require('./money');
const { unusablePasswordHash } = require('./password');

// Schema of the in-memory datastore, created at every start (RP-19).
// users.email is the account identity (checkout looks accounts up by it), hence UNIQUE.
// Foreign keys are not declared: what deleting a user does to its enrollments and payments is a
// product decision (proposed in the audit report), and enforcing them would change it.
const SCHEMA = [
  `CREATE TABLE users (
     id INTEGER PRIMARY KEY,
     name TEXT NOT NULL,
     email TEXT NOT NULL UNIQUE,
     pass TEXT NOT NULL)`,
  `CREATE TABLE courses (
     id INTEGER PRIMARY KEY,
     title TEXT NOT NULL,
     price_cents INTEGER NOT NULL,
     active INTEGER NOT NULL)`,
  `CREATE TABLE enrollments (
     id INTEGER PRIMARY KEY,
     user_id INTEGER NOT NULL,
     course_id INTEGER NOT NULL)`,
  `CREATE TABLE payments (
     id INTEGER PRIMARY KEY,
     enrollment_id INTEGER NOT NULL,
     amount_cents INTEGER NOT NULL,
     status TEXT NOT NULL CHECK (status IN ('${PaymentStatus.PAID}', '${PaymentStatus.DENIED}')))`,
  `CREATE TABLE audit_logs (
     id INTEGER PRIMARY KEY,
     action TEXT NOT NULL,
     created_at DATETIME NOT NULL)`,
];

const ACTIVE = 1;

// Seed data, as the original application loaded it at boot. The seeded account gets an unusable
// password: no credential literal ships with the code.
const SEED_USERS = [{ name: 'Leonan', email: 'leonan@fullcycle.com.br' }];
const SEED_COURSES = [
  { title: 'Clean Architecture', price: 997.0 },
  { title: 'Docker', price: 497.0 },
];
const SEED_ENROLLMENTS = [{ userId: 1, courseId: 1 }];
const SEED_PAYMENTS = [{ enrollmentId: 1, amount: 997.0, status: PaymentStatus.PAID }];

async function initializeSchema(db) {
  for (const statement of SCHEMA) {
    await db.run(statement);
  }
  for (const user of SEED_USERS) {
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [user.name, user.email, unusablePasswordHash()]);
  }
  for (const course of SEED_COURSES) {
    await db.run('INSERT INTO courses (title, price_cents, active) VALUES (?, ?, ?)',
      [course.title, toCents(course.price), ACTIVE]);
  }
  for (const enrollment of SEED_ENROLLMENTS) {
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [enrollment.userId, enrollment.courseId]);
  }
  for (const payment of SEED_PAYMENTS) {
    await db.run('INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
      [payment.enrollmentId, toCents(payment.amount), payment.status]);
  }
}

module.exports = { initializeSchema, ACTIVE };

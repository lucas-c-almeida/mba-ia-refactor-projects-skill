'use strict';

const { PAYMENT_STATUS } = require('./payment');
const { hashPassword, generateSecret } = require('./passwordHasher');

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };
const SEED_COURSES = [
  { title: 'Clean Architecture', priceCents: 99700 },
  { title: 'Docker', priceCents: 49700 },
];

/**
 * Creates the schema and loads the demo data. The seed account gets a
 * generated, hashed password nobody knows. Meant to run once on a fresh database.
 */
async function initSchema(db) {
  await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
  await db.run('CREATE UNIQUE INDEX IF NOT EXISTS users_email_key ON users (email)');
  await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price_cents INTEGER, active INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
  await db.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount_cents INTEGER, status TEXT)');
  await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

  const seedPass = await hashPassword(generateSecret());
  await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [SEED_USER.name, SEED_USER.email, seedPass]);
  for (const course of SEED_COURSES) {
    await db.run('INSERT INTO courses (title, price_cents, active) VALUES (?, ?, 1)', [course.title, course.priceCents]);
  }
  await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await db.run('INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (1, ?, ?)', [SEED_COURSES[0].priceCents, PAYMENT_STATUS.PAID]);
}

module.exports = { initSchema };

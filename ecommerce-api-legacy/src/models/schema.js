// Schema and seed data for the store. (AP-03 -> RP-03)
// Seed rows are the same as before; the seeded password is now stored hashed (AP-08 -> RP-08).
const { hashPassword } = require('./password');
const { PAYMENT_STATUS } = require('./payment');

const SEED_USER_PASSWORD = '123';

async function createSchema(db) {
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seed(db) {
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        ['Leonan', 'leonan@fullcycle.com.br', hashPassword(SEED_USER_PASSWORD)]);
    await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
        ['Clean Architecture', 997.0, 'Docker', 497.0]);
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', [PAYMENT_STATUS.PAID]);
}

async function initializeDatabase(db) {
    await createSchema(db);
    await seed(db);
}

module.exports = { initializeDatabase };

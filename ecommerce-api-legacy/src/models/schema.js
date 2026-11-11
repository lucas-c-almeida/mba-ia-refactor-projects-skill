// Schema and seed data, created at every boot (the datastore is in memory).
const { hashPassword, generatePassword } = require('./password');
const { PAYMENT_STATUS, toCents } = require('./payment');

const SCHEMA = [
    'PRAGMA foreign_keys = ON',
    `CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`,
    `CREATE TABLE courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
        active INTEGER NOT NULL DEFAULT 1
    )`,
    // user_id has no foreign key on purpose: what deleting a user does to its enrollments and
    // payments is a product decision, recorded under PROPOSED, NOT APPLIED in the audit report.
    `CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL REFERENCES courses (id)
    )`,
    `CREATE TABLE payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments (id),
        amount_cents INTEGER NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('${PAYMENT_STATUS.PAID}', '${PAYMENT_STATUS.DENIED}'))
    )`,
    'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
];

const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };
const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.00 },
    { title: 'Docker', price: 497.00 },
];

async function initializeSchema(db, { seedUserPassword }) {
    for (const statement of SCHEMA) {
        await db.run(statement);
    }

    const passwordHash = await hashPassword(seedUserPassword || generatePassword());
    const user = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [SEED_USER.name, SEED_USER.email, passwordHash],
    );
    const courseIds = [];
    for (const course of SEED_COURSES) {
        const inserted = await db.run(
            'INSERT INTO courses (title, price_cents, active) VALUES (?, ?, 1)',
            [course.title, toCents(course.price)],
        );
        courseIds.push(inserted.lastID);
    }
    const enrollment = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [user.lastID, courseIds[0]],
    );
    await db.run(
        'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
        [enrollment.lastID, toCents(SEED_COURSES[0].price), PAYMENT_STATUS.PAID],
    );
}

module.exports = { initializeSchema };

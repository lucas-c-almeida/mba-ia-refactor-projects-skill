'use strict';

const { hashPassword, generatePassword } = require('./password');
const { toCents } = require('./money');
const { PaymentStatus } = require('./payment');

// Schema, created at boot as before (the datastore is in-memory by default).
// Money in integer cents; users.email unique, since checkout identifies users by it (AP-20).
// Foreign keys and the delete rule for a user's enrollments and payments are a product
// decision and are proposed, not applied (see the audit report).
const SCHEMA = `
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass TEXT NOT NULL
);
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    active INTEGER NOT NULL
);
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL
);
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('${PaymentStatus.PAID}', '${PaymentStatus.DENIED}'))
);
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT,
    created_at DATETIME
);
`;

// Initial catalogue and sample enrollment, as the original seeded them. The seeded account
// gets an unguessable password instead of a literal one (AP-01).
const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br' };
const SEED_COURSES = [
    { title: 'Clean Architecture', price: 997.0, active: 1 },
    { title: 'Docker', price: 497.0, active: 1 },
];

async function createSchema(db) {
    await db.exec(SCHEMA);
}

async function seed(db) {
    const pass = await hashPassword(generatePassword());
    await db.transaction(async () => {
        const user = await db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [SEED_USER.name, SEED_USER.email, pass],
        );
        const courseIds = [];
        for (const course of SEED_COURSES) {
            const inserted = await db.run(
                'INSERT INTO courses (title, price_cents, active) VALUES (?, ?, ?)',
                [course.title, toCents(course.price), course.active],
            );
            courseIds.push(inserted.lastID);
        }
        const enrollment = await db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [user.lastID, courseIds[0]],
        );
        await db.run(
            'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
            [enrollment.lastID, toCents(SEED_COURSES[0].price), PaymentStatus.PAID],
        );
    });
}

module.exports = { createSchema, seed };

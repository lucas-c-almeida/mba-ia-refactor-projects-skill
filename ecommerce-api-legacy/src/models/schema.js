// Schema and seed of the in-memory datastore (moved out of the God Class — AP-03, RP-03).
// Tables and seed rows are unchanged, except that the seeded account's password is stored through
// the password KDF instead of in plain text (AP-08).

const { PaymentStatus } = require('./payment');
const { hashPassword, randomPassword } = require('./password');

const SCHEMA = `
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
    CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
    CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function initializeSchema(db, { seedUserPassword }) {
    await db.exec(SCHEMA);

    const seedHash = await hashPassword(seedUserPassword || randomPassword());
    await db.transaction(async (tx) => {
        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', seedHash]);
        await tx.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)',
            [PaymentStatus.PAID]);
    });
}

module.exports = { initializeSchema };

// Money is stored as integer minor units (cents); the API still shows decimal numbers (RP-19).
const SEED_COURSES = [
    { title: 'Clean Architecture', priceCents: 99700 },
    { title: 'Docker', priceCents: 49700 },
];

// Creates the tables and the sample data. users.email is unique: it is the lookup identity, and
// payments.status is a closed set.
async function initializeSchema(db, passwords) {
    await db.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT)');
    await db.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price INTEGER, active INTEGER)');
    await db.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await db.run(
        "CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount INTEGER, status TEXT CHECK (status IN ('PAID', 'DENIED')))",
    );
    await db.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

    // The sample user gets a random, unknown secret: no credential literal exists in the code.
    const sampleHash = await passwords.hash(passwords.generateSecret());
    await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', sampleHash]);

    for (const course of SEED_COURSES) {
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1)', [course.title, course.priceCents]);
    }

    const enrollment = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollment.lastID, SEED_COURSES[0].priceCents, 'PAID'],
    );
}

module.exports = { initializeSchema };

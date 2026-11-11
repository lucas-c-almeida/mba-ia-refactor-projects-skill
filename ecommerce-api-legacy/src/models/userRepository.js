// Persistence for user accounts.

function createUserRepository(db) {
    return {
        findIdByEmail: (email) => db.get('SELECT id FROM users WHERE email = ?', [email]),

        async create({ name, email, passwordHash }) {
            const result = await db.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash],
            );
            return result.lastID;
        },

        async deleteById(id) {
            await db.exclusive(() => db.run('DELETE FROM users WHERE id = ?', [id]));
        },
    };
}

module.exports = { createUserRepository };

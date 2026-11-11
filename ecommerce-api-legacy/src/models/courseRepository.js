// Persistence for the course catalog.

function createCourseRepository(db) {
    return {
        async findActiveById(id) {
            const row = await db.get(
                'SELECT id, title, price_cents FROM courses WHERE id = ? AND active = 1',
                [id],
            );
            return row ? { id: row.id, title: row.title, priceCents: row.price_cents } : null;
        },
    };
}

module.exports = { createCourseRepository };

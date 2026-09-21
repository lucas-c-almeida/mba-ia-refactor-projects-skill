// Enrollment persistence. (AP-03 -> RP-03)

class EnrollmentRepository {
    constructor(db) {
        this.db = db;
    }

    async create({ userId, courseId }) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return lastID;
    }
}

module.exports = { EnrollmentRepository };

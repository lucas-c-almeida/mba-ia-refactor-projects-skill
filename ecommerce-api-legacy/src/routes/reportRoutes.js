'use strict';

const express = require('express');

const UNKNOWN_STUDENT = 'Unknown';

// Presentation of the financial report: the response shape is the public contract.
const renderCourse = (course) => ({
    course: course.title,
    revenue: course.revenue,
    students: course.students.map((s) => ({
        student: s.name ?? UNKNOWN_STUDENT,
        paid: s.paid,
    })),
});

module.exports = (reportController) => {
    const router = express.Router();

    router.get('/api/admin/financial-report', async (req, res, next) => {
        try {
            const courses = await reportController.financialReport();
            res.json(courses.map(renderCourse));
        } catch (err) {
            next(err);
        }
    });

    return router;
};

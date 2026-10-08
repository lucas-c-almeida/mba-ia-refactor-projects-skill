// Composition root: the only place that names concrete implementations and wires them together.
const express = require('express');
const { loadConfig } = require('./config');
const { openDatabase } = require('./models/database');
const { initializeSchema } = require('./models/schema');
const { passwords } = require('./models/passwordHasher');
const { UserRepository } = require('./models/userRepository');
const { CourseRepository } = require('./models/courseRepository');
const { EnrollmentRepository } = require('./models/enrollmentRepository');
const { ReportRepository } = require('./models/reportRepository');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const { requireOperator } = require('./middlewares/requireOperator');
const { errorBoundary } = require('./middlewares/errorBoundary');
const { checkoutRoutes } = require('./views/checkoutRoutes');
const { adminRoutes } = require('./views/adminRoutes');

function createApp({ config, db, logger = console }) {
    const users = new UserRepository(db);
    const courses = new CourseRepository(db);
    const enrollments = new EnrollmentRepository(db);
    const reports = new ReportRepository(db);

    const app = express();
    app.disable('x-powered-by');
    app.use(express.json());

    const router = express.Router();
    checkoutRoutes(router, new CheckoutController({ users, courses, enrollments, passwords, logger }));
    adminRoutes(router, {
        reportController: new ReportController({ reports }),
        userController: new UserController({ users }),
        operatorGuard: requireOperator(config.operatorToken),
    });
    app.use(router);

    app.use(errorBoundary(logger));
    return app;
}

async function main() {
    const config = loadConfig();
    const db = openDatabase(':memory:');
    await initializeSchema(db, passwords);

    const app = createApp({ config, db });
    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    main().catch((err) => {
        console.error(err);
        process.exit(1);
    });
}

module.exports = { createApp };

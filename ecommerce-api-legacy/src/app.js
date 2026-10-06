'use strict';

// Composition root: the only place that names concrete implementations and wires them.
const express = require('express');

const { loadConfig } = require('./config');
const { Database } = require('./models/database');
const { createSchema, seed } = require('./models/schema');
const {
    CourseRepository,
    UserRepository,
    EnrollmentRepository,
    PaymentRepository,
    AuditLogRepository,
    FinancialReportRepository,
} = require('./models/repositories');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middlewares/errorHandler');

function createApp({ db, logger }) {
    const users = new UserRepository(db);

    const checkoutController = new CheckoutController({
        db,
        courses: new CourseRepository(db),
        users,
        enrollments: new EnrollmentRepository(db),
        payments: new PaymentRepository(db),
        auditLog: new AuditLogRepository(db),
        logger,
    });
    const reportController = new ReportController({ reports: new FinancialReportRepository(db) });
    const userController = new UserController({ users });

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes(checkoutController));
    app.use(reportRoutes(reportController));
    app.use(userRoutes(userController));
    app.use(errorHandler(logger));
    return app;
}

async function start() {
    const config = loadConfig();
    const logger = console;
    const db = await Database.open(config.databaseFile);
    await createSchema(db);
    await seed(db);

    createApp({ db, logger }).listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        console.error('failed to start', err);
        process.exit(1);
    });
}

module.exports = { createApp, start };

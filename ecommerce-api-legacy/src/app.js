// Composition root: load config, open the store, wire repositories -> controllers -> routes,
// register the error boundary, start. The only place concrete implementations are named. (AP-06 -> RP-06)
const express = require('express');
const { loadConfig } = require('./config');
const { Database } = require('./models/database');
const { initializeDatabase } = require('./models/schema');
const { UserRepository } = require('./models/user');
const { CourseRepository } = require('./models/course');
const { EnrollmentRepository } = require('./models/enrollment');
const { PaymentRepository } = require('./models/payment');
const { AuditLogRepository } = require('./models/auditLog');
const { FinancialReportRepository } = require('./models/financialReport');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const { checkoutRoutes } = require('./routes/checkoutRoutes');
const { adminRoutes } = require('./routes/adminRoutes');
const { userRoutes } = require('./routes/userRoutes');
const { errorHandler } = require('./middlewares/errorHandler');

function buildApp({ db, logger }) {
    const transaction = (work) => db.transaction(work);
    const users = new UserRepository(db);

    const checkoutController = new CheckoutController({
        transaction,
        users,
        courses: new CourseRepository(db),
        enrollments: new EnrollmentRepository(db),
        payments: new PaymentRepository(db),
        auditLogs: new AuditLogRepository(db),
        logger,
    });
    const reportController = new ReportController({ financialReports: new FinancialReportRepository(db) });
    const userController = new UserController({ transaction, users });

    const app = express();
    app.use(express.json());
    app.use(checkoutRoutes(checkoutController));
    app.use(adminRoutes(reportController));
    app.use(userRoutes(userController));
    app.use(errorHandler(logger));
    return app;
}

async function main() {
    const config = loadConfig();
    const logger = console;
    const db = await Database.open(config.dbPath);
    await initializeDatabase(db);

    const app = buildApp({ db, logger });
    const server = app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });

    // Release the listener and the database handle on shutdown. (AP-13 -> RP-13)
    const shutdown = () => server.close(() => db.close().finally(() => process.exit(0)));
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
}

if (require.main === module) {
    main().catch((err) => {
        console.error('Failed to start:', err);
        process.exit(1);
    });
}

module.exports = { buildApp };

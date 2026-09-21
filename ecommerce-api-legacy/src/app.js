// Composition root (AP-06 — RP-06): the only place that names concrete implementations.
// Loads configuration, opens the datastore, builds repositories and controllers, registers routes
// and the error boundary. Importing this module has no side effect; `npm start` runs main().

const express = require('express');
const sqlite3 = require('sqlite3');

const { loadConfig } = require('./config');
const { Database } = require('./models/database');
const { initializeSchema } = require('./models/schema');
const {
    CourseRepository, UserRepository, EnrollmentRepository, ReportRepository,
} = require('./models/repositories');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const registerCheckoutRoutes = require('./routes/checkoutRoutes');
const registerAdminRoutes = require('./routes/adminRoutes');
const errorBoundary = require('./middlewares/errorBoundary');

async function createApp({ config, logger = console }) {
    const db = new Database(new sqlite3.Database(':memory:'));
    await initializeSchema(db, config);

    const users = new UserRepository(db);
    const checkoutController = new CheckoutController({
        db,
        courses: new CourseRepository(db),
        users,
        enrollments: new EnrollmentRepository(),
        logger,
    });
    const reportController = new ReportController({ reports: new ReportRepository(db) });
    const userController = new UserController({ users });

    const app = express();
    app.use(express.json());
    registerCheckoutRoutes(app, checkoutController);
    registerAdminRoutes(app, { reportController, userController });
    app.use(errorBoundary(logger));
    return app;
}

async function main() {
    const config = loadConfig();
    const app = await createApp({ config });
    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    main().catch((err) => {
        console.error('failed to start', err);
        process.exit(1);
    });
}

module.exports = { createApp };

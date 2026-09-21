"""The delivery layer: route declarations and response presenters."""
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def register_routes(app, *, tasks, users, categories, reports):
    app.register_blueprint(create_task_blueprint(tasks))
    app.register_blueprint(create_user_blueprint(users))
    app.register_blueprint(create_report_blueprint(reports))
    app.register_blueprint(create_category_blueprint(categories))
    app.register_blueprint(create_system_blueprint())

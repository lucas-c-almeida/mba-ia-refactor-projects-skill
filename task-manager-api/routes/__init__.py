"""Delivery layer: blueprints built from the controllers the composition root hands in."""
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint


def register_routes(app, controllers, operator_guard):
    app.register_blueprint(create_task_blueprint(controllers['tasks']))
    app.register_blueprint(create_user_blueprint(controllers['users'], operator_guard))
    app.register_blueprint(create_report_blueprint(controllers['reports'], operator_guard))
    app.register_blueprint(create_category_blueprint(controllers['categories']))
    app.register_blueprint(create_system_blueprint())

"""
Administrative routes — still reachable with no authentication, unchanged from the
original on purpose. See src/controllers/admin_controller.py and AP-04/AP-02 in
reports/audit-latest.md ("Proposed, Not Applied").
"""
from flask import jsonify, request


def register(app, admin_controller) -> None:
    @app.route("/admin/reset-db", methods=["POST"])
    def reset_database():
        admin_controller.reset_db()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @app.route("/admin/query", methods=["POST"])
    def executar_query():
        resultado = admin_controller.executar_query(request.get_json())
        return jsonify(resultado), 200

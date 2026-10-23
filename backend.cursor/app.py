"""Lowkey backend entry point. Run:  python app.py"""
import logging
import sqlite3

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

import config
import db
from errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("lowkey")


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    db.init_db()

    from routes import auth, chat, dashboard, interventions, students, study_plans
    for m in (auth, dashboard, students, study_plans, interventions, chat):
        app.register_blueprint(m.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "genai": "configured" if config.ANTHROPIC_API_KEY else "offline-demo"})

    # ---- CORS (explicit allow-list) ----
    @app.before_request
    def preflight():
        if request.method == "OPTIONS":
            return "", 204

    @app.after_request
    def cors(resp):
        origin = request.headers.get("Origin")
        if origin in config.CORS_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
            resp.headers["Vary"] = "Origin"
        return resp

    # ---- consistent errors, no internals leaked ----
    @app.errorhandler(AppError)
    def app_error(e):
        return e.to_response()

    @app.errorhandler(sqlite3.Error)
    def db_error(e):
        log.error("Database error: %s", e)
        return AppError(503, "database_unavailable", "The database is temporarily unavailable.").to_response()

    @app.errorhandler(HTTPException)
    def http_error(e):
        return {"error": {"code": e.name.lower().replace(" ", "_"), "message": e.description}}, e.code

    @app.errorhandler(Exception)
    def unexpected(e):
        log.exception("Unhandled error")
        return {"error": {"code": "internal_error", "message": "Something went wrong on our side."}}, 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=config.PORT, debug=config.DEBUG)

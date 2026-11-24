"""Flask application factory."""
from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.extensions import db, jwt, limiter


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    from app.routes import (admin, analytics, announcements, assistant, auth, chat, documents, feedback,
                            questions, quizzes, research)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    for m in (documents, chat, feedback, assistant, questions, quizzes, announcements, analytics, research):
        app.register_blueprint(m.bp)

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Content-Security-Policy"] = "default-src 'none'"
        return resp

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    from app.models import User

    @jwt.token_verification_loader
    def user_still_valid(header, payload):
        """Reject tokens of deleted or deactivated accounts."""
        u = db.session.get(User, int(payload["sub"]))
        return bool(u and u.is_active)

    @jwt.token_verification_failed_loader
    def verification_failed(header, payload):
        return jsonify(error="Your account is disabled or no longer exists."), 401

    from app.services.llm import LLMError

    @app.errorhandler(LLMError)
    def llm_error(e):
        return jsonify(error=str(e)), 502

    @app.errorhandler(404)
    def nf(e):
        return jsonify(error="Not found"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify(error="Too many requests. Please wait a minute and try again."), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled error")
        return jsonify(error="Something went wrong on the server. Please try again."), 500

    @app.errorhandler(413)
    def too_big(e):
        return jsonify(error="File too large"), 413

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            raise RuntimeError(
                "Cannot connect to the database. Check that MySQL is running, that database 'uniassist' exists "
                "(run database/schema.sql) and that DATABASE_URL in backend/.env is correct "
                "(special characters in the password must be URL-encoded, e.g. @ -> %40).\n"
                f"Original error: {e}") from e
        seed_roles()
    return app


def seed_roles():
    from app.models import Role
    for n in ("student", "faculty", "admin"):
        if not Role.query.filter_by(name=n).first():
            db.session.add(Role(name=n))
    db.session.commit()

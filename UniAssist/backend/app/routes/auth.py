"""Authentication: register, login, profile."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from app.extensions import db, limiter
from app.models import Role, User
from app.utils.security import (EMAIL_RE, check_password, clean, current_user,
                                hash_password, log_activity, validate_password)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
SELF_REGISTER_ROLES = {"student", "faculty"}  # admins are created only by seed/admin


@bp.post("/register")
@limiter.limit("10 per hour")
def register():
    d = request.get_json(silent=True) or {}
    name, email = clean(d.get("full_name"), 120), clean(d.get("email"), 150).lower()
    role_name = d.get("role", "student")
    if not name or not EMAIL_RE.match(email):
        return jsonify(error="Valid name and email are required."), 400
    if role_name not in SELF_REGISTER_ROLES:
        return jsonify(error="Invalid role."), 400
    err = validate_password(d.get("password", ""))
    if err:
        return jsonify(error=err), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="Email already registered."), 409
    role = Role.query.filter_by(name=role_name).first()
    user = User(role_id=role.id, full_name=name, email=email,
                password_hash=hash_password(d["password"]),
                department=clean(d.get("department"), 100))
    db.session.add(user)
    db.session.commit()
    log_activity("register", user.id, {"role": role_name})
    return jsonify(user=user.to_dict()), 201


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    d = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=clean(d.get("email"), 150).lower()).first()
    if not user or not user.is_active or not check_password(d.get("password", ""), user.password_hash):
        log_activity("login_failed", user.id if user else None)
        return jsonify(error="Invalid credentials."), 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role.name})
    log_activity("login", user.id)
    return jsonify(access_token=token, user=user.to_dict())


@bp.get("/me")
@jwt_required()
def me():
    return jsonify(user=current_user().to_dict())


@bp.put("/me")
@jwt_required()
def update_me():
    d = request.get_json(silent=True) or {}
    u = current_user()
    if "full_name" in d:
        u.full_name = clean(d["full_name"], 120) or u.full_name
    if d.get("preferred_language") in ("en", "kn", "hi"):
        u.preferred_language = d["preferred_language"]
    if d.get("theme") in ("light", "dark"):
        u.theme = d["theme"]
    if d.get("new_password"):
        if not check_password(d.get("current_password", ""), u.password_hash):
            return jsonify(error="Current password incorrect."), 400
        err = validate_password(d["new_password"])
        if err:
            return jsonify(error=err), 400
        u.password_hash = hash_password(d["new_password"])
    db.session.commit()
    log_activity("profile_update", u.id)
    return jsonify(user=u.to_dict())

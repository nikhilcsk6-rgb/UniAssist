"""Admin: user management and audit log viewing."""
import os
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import ActivityLog, Document, Role, User
from app.services import vectorstore
from app.utils.security import current_user, log_activity, roles_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/users")
@roles_required("admin")
def list_users():
    q = User.query
    if request.args.get("role"):
        q = q.join(Role).filter(Role.name == request.args["role"])
    return jsonify(users=[u.to_dict() for u in q.order_by(User.id).all()])


@bp.put("/users/<int:uid>")
@roles_required("admin")
def update_user(uid):
    u = db.get_or_404(User, uid)
    d = request.get_json(silent=True) or {}
    if "is_active" in d:
        if u.id == current_user().id and not d["is_active"]:
            return jsonify(error="You cannot deactivate yourself."), 400
        u.is_active = bool(d["is_active"])
    if d.get("role") in ("student", "faculty", "admin"):
        u.role_id = Role.query.filter_by(name=d["role"]).first().id
    db.session.commit()
    log_activity("admin_update_user", current_user().id, {"target": uid})
    return jsonify(user=u.to_dict())


@bp.delete("/users/<int:uid>")
@roles_required("admin")
def delete_user(uid):
    if uid == current_user().id:
        return jsonify(error="You cannot delete yourself."), 400
    target = db.get_or_404(User, uid)
    docs = Document.query.filter_by(owner_id=uid).all()
    try:
        db.session.delete(target)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="This user owns research data (benchmarks/experiments) and cannot be deleted. Disable the account instead."), 409
    upload_dir = os.path.abspath(os.getenv("UPLOAD_DIR", "./uploads"))
    for d in docs:   # clean up vectors and files after the DB delete succeeded
        vectorstore.delete_document(d.id)
        try:
            os.remove(os.path.join(upload_dir, d.stored_filename))
        except FileNotFoundError:
            pass
    log_activity("admin_delete_user", current_user().id, {"target": uid})
    return jsonify(ok=True)


@bp.get("/logs")
@roles_required("admin")
def logs():
    rows = ActivityLog.query.order_by(ActivityLog.id.desc()).limit(200).all()
    return jsonify(logs=[{"id": r.id, "user_id": r.user_id, "action": r.action,
                          "details": r.details, "ip": r.ip_address,
                          "at": r.created_at.isoformat()} for r in rows])

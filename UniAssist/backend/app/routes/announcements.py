"""University announcements: everyone reads, faculty/admin publish."""
from datetime import date
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Announcement
from app.utils.security import clean, clean_text, current_user, log_activity, roles_required

bp = Blueprint("announcements", __name__, url_prefix="/api/announcements")
CATS = {"exam", "event", "holiday", "deadline", "circular", "general"}


def _fields(d, a):
    title, body = clean(d.get("title"), 200), clean_text(d.get("body"), 5000)
    if not title or not body:
        return "Title and body are required."
    if d.get("category", "general") not in CATS or d.get("audience", "all") not in ("all", "student", "faculty"):
        return "Invalid category or audience."
    a.title, a.body = title, body
    a.category, a.audience = d.get("category", "general"), d.get("audience", "all")
    try:
        a.event_date = date.fromisoformat(d["event_date"]) if d.get("event_date") else None
    except ValueError:
        return "event_date must be YYYY-MM-DD."
    return None


@bp.get("")
@jwt_required()
def list_all():
    user = current_user()
    q = Announcement.query
    if user.role.name != "admin":
        q = q.filter(Announcement.audience.in_(["all", user.role.name]))
    if request.args.get("category") in CATS:
        q = q.filter_by(category=request.args["category"])
    return jsonify(announcements=[a.to_dict() for a in q.order_by(Announcement.id.desc()).limit(200).all()])


@bp.post("")
@roles_required("faculty", "admin")
def create():
    user, a = current_user(), Announcement(author_id=current_user().id)
    err = _fields(request.get_json(silent=True) or {}, a)
    if err:
        return jsonify(error=err), 400
    db.session.add(a)
    db.session.commit()
    log_activity("announcement_create", user.id, {"id": a.id})
    return jsonify(announcement=a.to_dict()), 201


@bp.put("/<int:aid>")
@roles_required("faculty", "admin")
def update(aid):
    user, a = current_user(), db.get_or_404(Announcement, aid)
    if a.author_id != user.id and user.role.name != "admin":
        return jsonify(error="Forbidden"), 403
    err = _fields(request.get_json(silent=True) or {}, a)
    if err:
        return jsonify(error=err), 400
    db.session.commit()
    return jsonify(announcement=a.to_dict())


@bp.delete("/<int:aid>")
@roles_required("faculty", "admin")
def delete(aid):
    user, a = current_user(), db.get_or_404(Announcement, aid)
    if a.author_id != user.id and user.role.name != "admin":
        return jsonify(error="Forbidden"), 403
    db.session.delete(a)
    db.session.commit()
    log_activity("announcement_delete", user.id, {"id": aid})
    return jsonify(ok=True)

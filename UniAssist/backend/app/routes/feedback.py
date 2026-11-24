"""Feedback: rate answers, report incorrect answers, suggestions."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db, limiter
from app.models import ChatMessage, ChatSession, Feedback
from app.utils.security import clean_text, current_user, log_activity, roles_required

bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@bp.post("")
@jwt_required()
@limiter.limit("30 per hour")
def submit():
    user, d = current_user(), request.get_json(silent=True) or {}
    ftype = d.get("type")
    if ftype not in ("rating", "incorrect_report", "suggestion"):
        return jsonify(error="Invalid feedback type."), 400
    rating = d.get("rating")
    if ftype == "rating":
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            return jsonify(error="Rating must be an integer from 1 to 5."), 400
    else:
        rating = None
    mid = d.get("message_id")
    if mid is not None:
        m = db.session.get(ChatMessage, mid)
        s = db.session.get(ChatSession, m.session_id) if m else None
        if not s or s.user_id != user.id:
            return jsonify(error="Message not found."), 404
    elif ftype in ("rating", "incorrect_report"):
        return jsonify(error="message_id is required for this feedback type."), 400
    comment = clean_text(d.get("comment"), 2000)
    if ftype == "suggestion" and not comment:
        return jsonify(error="Please write your suggestion."), 400
    if ftype == "rating" and mid is not None:  # one rating per message: update instead of duplicate
        old = Feedback.query.filter_by(user_id=user.id, message_id=mid, type="rating").first()
        if old:
            old.rating, old.comment = rating, comment
            db.session.commit()
            return jsonify(feedback=old.to_dict())
    f = Feedback(user_id=user.id, message_id=mid, type=ftype, rating=rating, comment=comment)
    db.session.add(f)
    db.session.commit()
    log_activity("feedback", user.id, {"type": ftype})
    return jsonify(feedback=f.to_dict()), 201


@bp.get("")
@roles_required("admin")
def list_all():
    q = Feedback.query
    if request.args.get("type"):
        q = q.filter_by(type=request.args["type"])
    return jsonify(feedback=[f.to_dict() for f in q.order_by(Feedback.id.desc()).limit(300).all()])


@bp.get("/mine")
@jwt_required()
def mine():
    rows = Feedback.query.filter_by(user_id=current_user().id).order_by(Feedback.id.desc()).limit(100).all()
    return jsonify(feedback=[f.to_dict() for f in rows])

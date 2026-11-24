"""Document assistant + study assistant (text/JSON generation tools)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import limiter
from app.services import generation as gen
from app.utils.security import clean_text, current_user, log_activity

bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


def _lang(user, d):
    return d.get("language") if d.get("language") in ("en", "kn", "hi") else user.preferred_language


def _material(user, d):
    """Return (text, topic, doc_title, truncated) from document_id or topic."""
    if d.get("document_id"):
        doc, text, trunc = gen.load_material(int(d["document_id"]), user)
        return text, None, doc.title, trunc
    topic = clean_text(d.get("topic"), 300)
    if not topic:
        raise ValueError("Provide a document or a topic.")
    return None, topic, None, False


@bp.errorhandler(gen.AccessError)
def _forbidden(e):
    return jsonify(error=str(e)), 403


@bp.errorhandler(LookupError)
def _missing(e):
    return jsonify(error=str(e)), 404


@bp.errorhandler(ValueError)
def _bad(e):
    return jsonify(error=str(e)), 400


@bp.post("/document/<int:doc_id>/<task>")
@jwt_required()
@limiter.limit("20 per minute")
def document_task(doc_id, task):
    if task not in gen.DOC_TASKS:
        return jsonify(error="Unknown task."), 404
    user, d = current_user(), request.get_json(silent=True) or {}
    doc, text, truncated = gen.load_material(doc_id, user)
    out = gen.run_text_task(task, text, _lang(user, d))
    log_activity("document_task", user.id, {"doc": doc_id, "task": task})
    return jsonify(result=out, truncated=truncated, document=doc.title)


@bp.post("/explain")
@jwt_required()
@limiter.limit("20 per minute")
def explain():
    user, d = current_user(), request.get_json(silent=True) or {}
    text, topic, _, trunc = _material(user, d)
    level = d.get("level") if d.get("level") in ("beginner", "intermediate", "advanced") else "beginner"
    out = gen.run_text_task("explain", text, _lang(user, d), topic, extra=f"Audience level: {level}.")
    return jsonify(result=out, grounded_in_document=bool(text), truncated=trunc)


@bp.post("/revision-notes")
@jwt_required()
@limiter.limit("20 per minute")
def revision_notes():
    user, d = current_user(), request.get_json(silent=True) or {}
    text, topic, _, trunc = _material(user, d)
    return jsonify(result=gen.run_text_task("revision", text, _lang(user, d), topic),
                   grounded_in_document=bool(text), truncated=trunc)


@bp.post("/study-plan")
@jwt_required()
@limiter.limit("10 per minute")
def study_plan():
    user, d = current_user(), request.get_json(silent=True) or {}
    subject = clean_text(d.get("subject"), 200)
    if not subject:
        return jsonify(error="Subject is required."), 400
    try:
        days, hours = max(1, min(int(d.get("days", 7)), 90)), max(0.5, min(float(d.get("hours_per_day", 2)), 12))
    except (TypeError, ValueError):
        return jsonify(error="days and hours_per_day must be numbers."), 400
    goals = clean_text(d.get("goals"), 500)
    extra = (f"Create a personalised day-by-day study plan in Markdown for '{subject}' over {days} days, "
             f"{hours} hours per day. Student goals/weak areas: {goals or 'not specified'}. Include daily topics, "
             "revision slots, practice tasks and a final-day mock test.")
    text, topic = None, subject
    if d.get("document_id"):
        _, text, _ = gen.load_material(int(d["document_id"]), user)
    return jsonify(result=gen.run_text_task("study_plan", text, _lang(user, d), topic, extra=extra))


@bp.post("/flashcards")
@jwt_required()
@limiter.limit("20 per minute")
def flashcards():
    user, d = current_user(), request.get_json(silent=True) or {}
    text, topic, _, trunc = _material(user, d)
    count = max(3, min(int(d.get("count", 10)), 30))
    return jsonify(flashcards=gen.generate_flashcards(text, topic, count, _lang(user, d)), truncated=trunc)

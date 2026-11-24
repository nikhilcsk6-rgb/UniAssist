"""Question paper generator + PDF export."""
import uuid
from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app.extensions import db, limiter
from app.models import GeneratedQuestion
from app.services import generation as gen
from app.utils.pdf import question_paper_pdf
from app.utils.security import clean, current_user, log_activity, roles_required

bp = Blueprint("questions", __name__, url_prefix="/api/questions")


@bp.errorhandler(gen.AccessError)
def _forbidden(e):
    return jsonify(error=str(e)), 403


@bp.errorhandler(LookupError)
def _missing(e):
    return jsonify(error=str(e)), 404


@bp.errorhandler(ValueError)
def _bad(e):
    return jsonify(error=str(e)), 400


@bp.post("/generate")
@jwt_required()
@limiter.limit("10 per minute")
def generate():
    user, d = current_user(), request.get_json(silent=True) or {}
    spec = gen.normalize_spec(d.get("spec"))
    language = d.get("language") if d.get("language") in ("en", "kn", "hi") else user.preferred_language
    doc_id, text, topic = d.get("document_id"), None, clean(d.get("topic"), 300)
    if doc_id:
        _, text, _ = gen.load_material(int(doc_id), user)
    elif not topic:
        return jsonify(error="Choose a document or enter a topic."), 400
    questions = gen.generate_questions(text, topic, spec, language)
    pid, title = uuid.uuid4().hex[:12], clean(d.get("title"), 200) or "Question Paper"
    for q in questions:
        db.session.add(GeneratedQuestion(user_id=user.id, document_id=doc_id, question_type=q["type"],
                                         marks=q["marks"], difficulty=q["difficulty"], question_text=q["question"],
                                         options=q["options"], answer_key=q["answer"], paper_id=pid,
                                         paper_title=title))
    db.session.commit()
    log_activity("question_paper", user.id, {"paper": pid, "count": len(questions)})
    return jsonify(paper_id=pid, title=title, questions=questions), 201


@bp.get("/papers")
@jwt_required()
def papers():
    rows = (db.session.query(GeneratedQuestion.paper_id, GeneratedQuestion.paper_title,
                             func.count(GeneratedQuestion.id), func.max(GeneratedQuestion.created_at))
            .filter_by(user_id=current_user().id).group_by(GeneratedQuestion.paper_id, GeneratedQuestion.paper_title)
            .order_by(func.max(GeneratedQuestion.created_at).desc()).all())
    return jsonify(papers=[{"paper_id": r[0], "title": r[1], "count": r[2], "created_at": r[3].isoformat()}
                           for r in rows])


def _paper(pid):
    qs = GeneratedQuestion.query.filter_by(paper_id=pid, user_id=current_user().id).order_by(GeneratedQuestion.id).all()
    if not qs:
        raise LookupError("Paper not found.")
    return qs


@bp.get("/papers/<pid>")
@jwt_required()
def paper(pid):
    qs = _paper(pid)
    return jsonify(paper_id=pid, title=qs[0].paper_title, questions=[q.to_dict() for q in qs])


@bp.get("/papers/<pid>/pdf")
@jwt_required()
def paper_pdf(pid):
    qs = _paper(pid)
    data = question_paper_pdf(qs[0].paper_title or "Question Paper", [q.to_dict() for q in qs],
                              include_answers=request.args.get("answers") == "1")
    return Response(data, mimetype="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="paper_{pid}.pdf"'})


@bp.delete("/papers/<pid>")
@jwt_required()
def delete_paper(pid):
    for q in _paper(pid):
        db.session.delete(q)
    db.session.commit()
    return jsonify(ok=True)

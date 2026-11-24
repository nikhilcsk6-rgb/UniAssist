"""Interactive quizzes: generate, take, score (server-side), history."""
from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required
from app.extensions import db, limiter
from app.models import Quiz, QuizResult, User
from app.services import generation as gen
from app.utils.security import clean, current_user, log_activity

bp = Blueprint("quizzes", __name__, url_prefix="/api/quizzes")


@bp.errorhandler(gen.AccessError)
def _forbidden(e):
    return jsonify(error=str(e)), 403


@bp.errorhandler(LookupError)
def _missing(e):
    return jsonify(error=str(e)), 404


def _visible(quiz, user):
    """Own quizzes, plus quizzes published by faculty/admin."""
    if quiz.creator_id == user.id:
        return True
    creator = db.session.get(User, quiz.creator_id)
    return creator is not None and creator.role.name in ("faculty", "admin")


def _public(quiz, with_answers=False):
    qs = quiz.questions if with_answers else [{"question": q["question"], "options": q["options"]}
                                              for q in quiz.questions]
    return {"id": quiz.id, "title": quiz.title, "difficulty": quiz.difficulty, "count": len(quiz.questions),
            "creator_id": quiz.creator_id, "created_at": quiz.created_at.isoformat(), "questions": qs}


@bp.post("/generate")
@jwt_required()
@limiter.limit("10 per minute")
def generate():
    user, d = current_user(), request.get_json(silent=True) or {}
    count = max(3, min(int(d.get("count", 10)), 30))
    diff = d.get("difficulty") if d.get("difficulty") in ("easy", "medium", "difficult") else "medium"
    lang = d.get("language") if d.get("language") in ("en", "kn", "hi") else user.preferred_language
    text, topic, doc_id = None, clean(d.get("topic"), 300), d.get("document_id")
    if doc_id:
        _, text, _ = gen.load_material(int(doc_id), user)
    elif not topic:
        return jsonify(error="Choose a document or enter a topic."), 400
    questions = gen.generate_quiz_questions(text, topic, count, diff, lang)
    quiz = Quiz(creator_id=user.id, document_id=doc_id, difficulty=diff, questions=questions,
                title=clean(d.get("title"), 200) or f"Quiz: {topic or 'document'}"[:200])
    db.session.add(quiz)
    db.session.commit()
    log_activity("quiz_generate", user.id, {"quiz": quiz.id})
    return jsonify(quiz=_public(quiz)), 201


@bp.get("")
@jwt_required()
def list_quizzes():
    user = current_user()
    quizzes = [q for q in Quiz.query.order_by(Quiz.id.desc()).limit(200).all() if _visible(q, user)]
    return jsonify(quizzes=[{k: v for k, v in _public(q).items() if k != "questions"} for q in quizzes])


@bp.get("/results")
@jwt_required()
def my_results():
    rows = (QuizResult.query.filter_by(user_id=current_user().id).order_by(QuizResult.id.desc()).limit(100).all())
    titles = {q.id: q.title for q in Quiz.query.filter(Quiz.id.in_([r.quiz_id for r in rows])).all()} if rows else {}
    return jsonify(results=[{"id": r.id, "quiz_id": r.quiz_id, "quiz_title": titles.get(r.quiz_id),
                             "score": r.score, "total": r.total, "taken_at": r.taken_at.isoformat()} for r in rows])


@bp.get("/<int:qid>")
@jwt_required()
def get_quiz(qid):
    quiz = db.session.get(Quiz, qid)
    if not quiz or not _visible(quiz, current_user()):
        raise LookupError("Quiz not found.")
    return jsonify(quiz=_public(quiz))   # answers are never sent before submission


@bp.post("/<int:qid>/submit")
@jwt_required()
def submit(qid):
    user, quiz = current_user(), db.session.get(Quiz, qid)
    if not quiz or not _visible(quiz, user):
        raise LookupError("Quiz not found.")
    answers = (request.get_json(silent=True) or {}).get("answers")
    if not isinstance(answers, list) or len(answers) != len(quiz.questions):
        return jsonify(error="Provide one answer (or null) per question."), 400
    detail, score = [], 0
    for q, a in zip(quiz.questions, answers):
        ok = isinstance(a, int) and a == q["answer_index"]
        score += ok
        detail.append({"correct": ok, "your_answer": a, "answer_index": q["answer_index"],
                       "explanation": q.get("explanation", "")})
    db.session.add(QuizResult(quiz_id=quiz.id, user_id=user.id, score=score, total=len(quiz.questions),
                              answers=answers))
    db.session.commit()
    log_activity("quiz_submit", user.id, {"quiz": qid, "score": score})
    return jsonify(score=score, total=len(quiz.questions), details=detail)


@bp.errorhandler(ValueError)
def _bad(e):
    return jsonify(error="Invalid input: " + str(e)), 400

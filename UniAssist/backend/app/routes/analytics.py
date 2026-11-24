"""Dashboard statistics."""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app.extensions import db
from app.models import (Announcement, ChatMessage, ChatSession, Document, Feedback, GeneratedQuestion, Quiz,
                        QuizResult, Role, User)
from app.utils.security import current_user, roles_required

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("/me")
@jwt_required()
def me():
    u = current_user()
    results = QuizResult.query.filter_by(user_id=u.id).order_by(QuizResult.id.desc()).limit(10).all()
    papers = db.session.query(func.count(func.distinct(GeneratedQuestion.paper_id))).filter_by(user_id=u.id).scalar()
    return jsonify(
        documents=Document.query.filter_by(owner_id=u.id).count(),
        chat_sessions=ChatSession.query.filter_by(user_id=u.id).count(),
        quizzes_taken=QuizResult.query.filter_by(user_id=u.id).count(),
        papers_generated=papers or 0,
        announcements_posted=Announcement.query.filter_by(author_id=u.id).count(),
        recent_quiz_scores=[{"quiz_id": r.quiz_id, "score": r.score, "total": r.total,
                             "taken_at": r.taken_at.isoformat()} for r in reversed(results)])


@bp.get("/overview")
@roles_required("admin")
def overview():
    since = datetime.utcnow() - timedelta(days=14)
    by_role = dict(db.session.query(Role.name, func.count(User.id)).outerjoin(User, User.role_id == Role.id)
                   .group_by(Role.name).all())
    per_day = (db.session.query(func.date(ChatMessage.created_at), func.count(ChatMessage.id))
               .filter(ChatMessage.sender == "user", ChatMessage.created_at >= since)
               .group_by(func.date(ChatMessage.created_at)).order_by(func.date(ChatMessage.created_at)).all())
    ans = ChatMessage.query.filter(ChatMessage.sender == "assistant")
    rag_answers = ans.filter(ChatMessage.grounded.isnot(None)).count()
    grounded = ans.filter(ChatMessage.grounded.is_(True)).count()
    avg_time = db.session.query(func.avg(ChatMessage.response_time_ms)).filter(
        ChatMessage.sender == "assistant").scalar()
    fb = dict(db.session.query(Feedback.type, func.count(Feedback.id)).group_by(Feedback.type).all())
    avg_rating = db.session.query(func.avg(Feedback.rating)).filter(Feedback.type == "rating").scalar()
    return jsonify(
        users_by_role=by_role, documents=Document.query.count(),
        official_documents=Document.query.filter_by(category="official").count(),
        chat_sessions=ChatSession.query.count(), messages=ChatMessage.query.count(),
        quizzes=Quiz.query.count(), questions_generated=GeneratedQuestion.query.count(),
        messages_per_day=[{"date": str(d), "count": c} for d, c in per_day],
        rag_answers=rag_answers, grounded_answers=grounded,
        not_found_rate=(1 - grounded / rag_answers) if rag_answers else None,
        avg_response_time_ms=float(avg_time) if avg_time is not None else None,
        feedback_by_type=fb, avg_rating=float(avg_rating) if avg_rating is not None else None)

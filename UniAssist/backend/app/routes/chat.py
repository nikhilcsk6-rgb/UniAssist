"""Chat sessions, messages (RAG answers) and history."""
from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required
from app.extensions import db, limiter
from app.models import ChatMessage, ChatSession, Document
from app.services import rag
from app.utils.security import clean, clean_text, current_user, log_activity

bp = Blueprint("chat", __name__, url_prefix="/api/chat")
MODES = {"university", "document", "study"}


def _own_session(sid):
    s = db.session.get(ChatSession, sid)
    if not s or s.user_id != current_user().id:
        abort(404)  # 404 (not 403) so session ids of other users are not revealed
    return s


@bp.get("/sessions")
@jwt_required()
def list_sessions():
    q = ChatSession.query.filter_by(user_id=current_user().id)
    term = clean(request.args.get("q"), 100)
    if term:
        like = f"%{term}%"
        matching = db.session.query(ChatMessage.session_id).filter(ChatMessage.content.like(like))
        q = q.filter(db.or_(ChatSession.title.like(like), ChatSession.id.in_(matching)))
    return jsonify(sessions=[s.to_dict() for s in q.order_by(ChatSession.id.desc()).limit(200).all()])


@bp.post("/sessions")
@jwt_required()
def create_session():
    user, d = current_user(), request.get_json(silent=True) or {}
    mode = d.get("mode", "university")
    if mode not in MODES:
        return jsonify(error="Invalid mode."), 400
    doc_id = d.get("document_id")
    if mode == "document":
        doc = db.session.get(Document, doc_id) if doc_id else None
        if not doc or (doc.owner_id != user.id and doc.visibility != "public"):
            return jsonify(error="Choose a document you have access to."), 400
    lang = d.get("language") if d.get("language") in ("en", "kn", "hi") else user.preferred_language
    s = ChatSession(user_id=user.id, mode=mode, document_id=doc_id if mode == "document" else None,
                    language=lang, title=clean(d.get("title"), 200) or "New chat")
    db.session.add(s)
    db.session.commit()
    return jsonify(session=s.to_dict()), 201


@bp.get("/sessions/<int:sid>")
@jwt_required()
def get_session(sid):
    s = _own_session(sid)
    return jsonify(session=s.to_dict(), messages=[m.to_dict() for m in s.messages])


@bp.put("/sessions/<int:sid>")
@jwt_required()
def update_session(sid):
    s, d = _own_session(sid), request.get_json(silent=True) or {}
    if d.get("title"):
        s.title = clean(d["title"], 200)
    if d.get("language") in ("en", "kn", "hi"):
        s.language = d["language"]
    db.session.commit()
    return jsonify(session=s.to_dict())


@bp.delete("/sessions/<int:sid>")
@jwt_required()
def delete_session(sid):
    db.session.delete(_own_session(sid))
    db.session.commit()
    return jsonify(ok=True)


@bp.post("/sessions/<int:sid>/messages")
@jwt_required()
@limiter.limit("30 per minute")
def send_message(sid):
    user, s = current_user(), _own_session(sid)
    content = clean_text((request.get_json(silent=True) or {}).get("content"), 2000)
    if not content:
        return jsonify(error="Message cannot be empty."), 400
    history = [(m.sender, m.content) for m in s.messages]
    res = rag.answer_question(user, content, history=history, mode=s.mode, language=s.language,
                              document_id=s.document_id, use_rag=True)
    um = ChatMessage(session_id=s.id, sender="user", content=content)
    am = ChatMessage(session_id=s.id, sender="assistant", content=res["answer"], sources=res["sources"],
                     response_time_ms=res["response_time_ms"], grounded=res["grounded"])
    db.session.add_all([um, am])
    if s.title == "New chat":
        s.title = content[:60]
    db.session.commit()
    log_activity("chat_message", user.id, {"session": s.id, "grounded": res["grounded"]})
    return jsonify(user_message=um.to_dict(), assistant_message=am.to_dict())

"""Document management + semantic search."""
import os
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Document
from app.services import ingestion, vectorstore
from app.utils.files import new_stored_name, validate_upload
from app.utils.security import clean, current_user, log_activity

bp = Blueprint("documents", __name__, url_prefix="/api/documents")


def _upload_dir():
    d = os.path.abspath(os.getenv("UPLOAD_DIR", "./uploads"))
    os.makedirs(d, exist_ok=True)
    return d


@bp.post("")
@jwt_required()
@limiter.limit("30 per hour")
def upload():
    user, role = current_user(), current_user().role.name
    category = request.form.get("category", "personal")
    visibility = request.form.get("visibility", "private")
    # Permission matrix: only admin may publish official documents; faculty may share study material.
    if category == "official" and role != "admin":
        return jsonify(error="Only administrators can upload official documents."), 403
    if category == "study_material" and role == "student":
        return jsonify(error="Students can only upload personal documents."), 403
    if category not in ("official", "study_material", "personal"):
        return jsonify(error="Invalid category."), 400
    if category == "personal" or visibility not in ("public", "private"):
        visibility = "private"
    if category == "official":
        visibility = "public"
    try:
        ext, name, data = validate_upload(request.files.get("file"), current_app.config["MAX_CONTENT_LENGTH"])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    stored = new_stored_name(ext)
    with open(os.path.join(_upload_dir(), stored), "wb") as f:
        f.write(data)
    doc = Document(owner_id=user.id, title=clean(request.form.get("title"), 255) or name,
                   original_filename=name, stored_filename=stored, file_type=ext,
                   category=category, visibility=visibility)
    db.session.add(doc)
    db.session.commit()
    try:
        ingestion.index_document(doc, _upload_dir())
    except Exception as e:  # keep the row so the user can see/retry/delete it
        current_app.logger.exception("Indexing failed")
        log_activity("document_index_failed", user.id, {"doc": doc.id})
        return jsonify(error=f"Uploaded but indexing failed: {e}", document=doc.to_dict()), 422
    log_activity("document_upload", user.id, {"doc": doc.id, "category": category})
    return jsonify(document=doc.to_dict()), 201


@bp.get("")
@jwt_required()
def list_documents():
    user = current_user()
    q = Document.query.filter(or_(Document.owner_id == user.id, Document.visibility == "public"))
    if request.args.get("category"):
        q = q.filter_by(category=request.args["category"])
    if request.args.get("mine") == "1":
        q = q.filter_by(owner_id=user.id)
    return jsonify(documents=[d.to_dict() for d in q.order_by(Document.id.desc()).all()])


@bp.delete("/<int:doc_id>")
@jwt_required()
def delete_document(doc_id):
    user, doc = current_user(), db.get_or_404(Document, doc_id)
    if doc.owner_id != user.id and user.role.name != "admin":
        return jsonify(error="Forbidden"), 403
    vectorstore.delete_document(doc.id)
    try:
        os.remove(os.path.join(_upload_dir(), doc.stored_filename))
    except FileNotFoundError:
        pass
    db.session.delete(doc)
    db.session.commit()
    log_activity("document_delete", user.id, {"doc": doc_id})
    return jsonify(ok=True)


@bp.post("/<int:doc_id>/reindex")
@jwt_required()
def reindex(doc_id):
    user, doc = current_user(), db.get_or_404(Document, doc_id)
    if doc.owner_id != user.id and user.role.name != "admin":
        return jsonify(error="Forbidden"), 403
    try:
        ingestion.index_document(doc, _upload_dir())
    except Exception as e:
        return jsonify(error=str(e)), 422
    return jsonify(document=doc.to_dict())


@bp.get("/search")
@jwt_required()
@limiter.limit("60 per minute")
def semantic_search():
    q = clean(request.args.get("q"), 500)
    if not q:
        return jsonify(error="Query 'q' is required."), 400
    top_k = min(int(request.args.get("top_k", 5)), 10)
    hits = ingestion.search(q, current_user(), top_k, category=request.args.get("category"))
    return jsonify(results=[{"filename": h["filename"], "page": h["page"], "similarity": round(h["similarity"], 3),
                             "text": h["text"]} for h in hits])

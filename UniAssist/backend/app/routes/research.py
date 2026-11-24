"""Research & evaluation module (admin only)."""
import csv
import io
from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func
from app.extensions import db, limiter
from app.models import BenchmarkItem, EvaluationMetric, ResearchExperiment
from app.services import research_eval as ev
from app.utils.pdf import research_pdf
from app.utils.security import clean, current_user, log_activity, roles_required

bp = Blueprint("research", __name__, url_prefix="/api/research")
MAX_ROWS = 200


@bp.post("/benchmark")
@roles_required("admin")
def upload_benchmark():
    """CSV columns: question, reference_answer, [reference_document], [reference_page]"""
    f, name = request.files.get("file"), clean(request.form.get("dataset_name"), 120)
    if not f or not name or not f.filename.lower().endswith(".csv"):
        return jsonify(error="Provide dataset_name and a .csv file."), 400
    try:
        text = f.read(2_000_000).decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify(error="CSV must be UTF-8 encoded."), 400
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not {"question", "reference_answer"} <= set(reader.fieldnames):
        return jsonify(error="CSV needs columns: question, reference_answer (optional: reference_document, reference_page)."), 400
    items = []
    for row in reader:
        q, a = (row.get("question") or "").strip(), (row.get("reference_answer") or "").strip()
        if not q or not a:
            continue
        page = (row.get("reference_page") or "").strip()
        items.append(BenchmarkItem(dataset_name=name, question=q[:2000], reference_answer=a[:4000],
                                   reference_document=(row.get("reference_document") or "").strip() or None,
                                   reference_page=int(page) if page.isdigit() else None,
                                   uploaded_by=current_user().id))
    if not items or len(items) > MAX_ROWS:
        return jsonify(error=f"CSV must contain 1-{MAX_ROWS} valid rows."), 400
    BenchmarkItem.query.filter_by(dataset_name=name).delete()   # re-upload replaces the dataset
    db.session.add_all(items)
    db.session.commit()
    log_activity("benchmark_upload", current_user().id, {"dataset": name, "rows": len(items)})
    return jsonify(dataset_name=name, rows=len(items)), 201


@bp.get("/datasets")
@roles_required("admin")
def datasets():
    rows = db.session.query(BenchmarkItem.dataset_name, func.count(BenchmarkItem.id)).group_by(
        BenchmarkItem.dataset_name).all()
    return jsonify(datasets=[{"name": n, "rows": c} for n, c in rows])


@bp.delete("/datasets/<name>")
@roles_required("admin")
def delete_dataset(name):
    BenchmarkItem.query.filter_by(dataset_name=name).delete()
    db.session.commit()
    return jsonify(ok=True)


@bp.post("/experiments")
@roles_required("admin")
@limiter.limit("5 per hour")
def run():
    d, user = request.get_json(silent=True) or {}, current_user()
    items = BenchmarkItem.query.filter_by(dataset_name=d.get("dataset_name")).order_by(BenchmarkItem.id).all()
    if not items:
        return jsonify(error="Dataset not found."), 404
    limit = max(1, min(int(d.get("limit", 30)), 50))   # synchronous run: keep requests short
    try:
        temperature, top_k = float(d.get("temperature", 0.1)), max(1, min(int(d.get("top_k", 5)), 10))
    except (TypeError, ValueError):
        return jsonify(error="temperature and top_k must be numbers."), 400
    exp = ResearchExperiment(name=clean(d.get("name"), 160) or "Experiment", dataset_name=d["dataset_name"],
                             llm_model=ev.model_name(), temperature=temperature, top_k=top_k,
                             is_sample=False, created_by=user.id)
    db.session.add(exp)
    db.session.commit()
    try:
        ev.run_experiment(exp, items[:limit], user)
    except Exception as e:
        return jsonify(error=f"Experiment failed: {e}", experiment=exp.to_dict()), 502
    log_activity("experiment_run", user.id, {"id": exp.id})
    return jsonify(experiment=exp.to_dict(), summary=ev.summarize(exp.id)), 201


@bp.get("/experiments")
@roles_required("admin")
def list_experiments():
    return jsonify(experiments=[e.to_dict() for e in ResearchExperiment.query.order_by(
        ResearchExperiment.id.desc()).all()])


def _rows(exp_id):
    out = []
    for m in EvaluationMetric.query.filter_by(experiment_id=exp_id).order_by(
            EvaluationMetric.benchmark_item_id, EvaluationMetric.model_variant).all():
        out.append({"question_id": m.benchmark_item_id, "question": m.item.question,
                    "reference_answer": m.item.reference_answer, "variant": m.model_variant,
                    "answer": m.generated_answer, "accuracy": m.accuracy_score, "relevance": m.relevance_score,
                    "hallucinated": m.hallucinated, "abstained": m.abstained, "response_time_ms": m.response_time_ms,
                    "citation_correct": m.citation_correct, "retrieval_precision": m.retrieval_precision})
    return out


@bp.get("/experiments/<int:eid>")
@roles_required("admin")
def experiment(eid):
    exp = db.get_or_404(ResearchExperiment, eid)
    return jsonify(experiment=exp.to_dict(), summary=ev.summarize(eid), satisfaction=ev.satisfaction(),
                   rows=_rows(eid))


@bp.delete("/experiments/<int:eid>")
@roles_required("admin")
def delete_experiment(eid):
    db.session.delete(db.get_or_404(ResearchExperiment, eid))
    db.session.commit()
    return jsonify(ok=True)


@bp.get("/experiments/<int:eid>/export.csv")
@roles_required("admin")
def export_csv(eid):
    db.get_or_404(ResearchExperiment, eid)
    rows = _rows(eid)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["question_id"])
    w.writeheader()
    w.writerows(rows)
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="experiment_{eid}.csv"'})


@bp.get("/experiments/<int:eid>/export.pdf")
@roles_required("admin")
def export_pdf(eid):
    exp = db.get_or_404(ResearchExperiment, eid)
    data = research_pdf(exp, ev.summarize(eid), ev.satisfaction(), _rows(eid))
    return Response(data, mimetype="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="experiment_{eid}.pdf"'})

from datetime import datetime
from app.extensions import db


class BenchmarkItem(db.Model):
    __tablename__ = "benchmark_items"
    id = db.Column(db.Integer, primary_key=True)
    dataset_name = db.Column(db.String(120), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    reference_answer = db.Column(db.Text, nullable=False)
    reference_document = db.Column(db.String(255))
    reference_page = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class ResearchExperiment(db.Model):
    __tablename__ = "research_experiments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    dataset_name = db.Column(db.String(120), nullable=False)
    llm_model = db.Column(db.String(80), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    top_k = db.Column(db.Integer, nullable=False)
    is_sample = db.Column(db.Boolean, nullable=False, default=False)  # True = illustrative, False = measured
    status = db.Column(db.String(10), default="pending")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    metrics = db.relationship("EvaluationMetric", backref="experiment", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "dataset_name": self.dataset_name, "llm_model": self.llm_model,
                "temperature": self.temperature, "top_k": self.top_k, "is_sample": self.is_sample,
                "status": self.status, "created_at": self.created_at.isoformat()}


class EvaluationMetric(db.Model):
    __tablename__ = "evaluation_metrics"
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey("research_experiments.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    benchmark_item_id = db.Column(db.Integer, db.ForeignKey("benchmark_items.id", ondelete="CASCADE"), nullable=False)
    model_variant = db.Column(db.String(10), nullable=False)       # A_no_rag | B_rag
    generated_answer = db.Column(db.Text)
    accuracy_score = db.Column(db.Float)
    relevance_score = db.Column(db.Float)
    hallucinated = db.Column(db.Boolean)
    response_time_ms = db.Column(db.Integer)
    abstained = db.Column(db.Boolean, default=False)
    citation_correct = db.Column(db.Boolean)
    retrieval_precision = db.Column(db.Float)
    item = db.relationship("BenchmarkItem")

"""ORM model: Document (mirrors database/schema.sql)."""
from datetime import datetime
from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(5), nullable=False)          # pdf | docx | txt
    category = db.Column(db.String(20), default="personal")      # official | study_material | personal
    visibility = db.Column(db.String(10), default="private")     # public | private
    page_count = db.Column(db.Integer, default=0)
    chunk_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(10), default="uploaded")        # uploaded | indexed | failed
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "owner_id": self.owner_id, "title": self.title,
                "filename": self.original_filename, "file_type": self.file_type,
                "category": self.category, "visibility": self.visibility,
                "page_count": self.page_count, "chunk_count": self.chunk_count,
                "status": self.status,
                "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None}

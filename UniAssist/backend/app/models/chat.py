from datetime import datetime
from app.extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), default="New chat")
    mode = db.Column(db.String(12), default="university")   # university | document | study
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    language = db.Column(db.String(2), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("ChatMessage", backref="session", cascade="all, delete-orphan",
                               order_by="ChatMessage.id")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "mode": self.mode, "document_id": self.document_id,
                "language": self.language, "created_at": self.created_at.isoformat()}


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = db.Column(db.String(10), nullable=False)        # user | assistant
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON)
    response_time_ms = db.Column(db.Integer)
    grounded = db.Column(db.Boolean)                         # None = not a RAG answer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "sender": self.sender, "content": self.content, "sources": self.sources or [],
                "grounded": self.grounded, "response_time_ms": self.response_time_ms,
                "created_at": self.created_at.isoformat()}

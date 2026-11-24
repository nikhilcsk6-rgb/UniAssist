"""ORM models: Role, User, ActivityLog (mirror database/schema.sql)."""
from datetime import datetime
from app.extensions import db


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100))
    preferred_language = db.Column(db.String(2), default="en")
    theme = db.Column(db.String(5), default="light")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.relationship("Role")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "email": self.email,
                "role": self.role.name, "department": self.department,
                "preferred_language": self.preferred_language, "theme": self.theme,
                "is_active": self.is_active,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

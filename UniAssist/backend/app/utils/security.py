"""Password hashing, RBAC decorator, validation and audit logging helpers."""
import re
import bcrypt
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from app.extensions import db
from app.models import ActivityLog, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def check_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def validate_password(pw: str):
    """Return an error string, or None if the password is acceptable."""
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not (re.search(r"[A-Za-z]", pw) and re.search(r"\d", pw)):
        return "Password must contain letters and digits."
    return None


def clean(text, max_len=200):
    """Trim and strip control characters / angle brackets (basic XSS hardening)."""
    text = (text or "").strip()
    text = re.sub(r"[\x00-\x1f<>]", "", text)
    return text[:max_len]


def roles_required(*roles):
    """Allow access only to users whose JWT role claim is in `roles`."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            verify_jwt_in_request()
            user = current_user()
            if user is None or user.role.name not in roles:
                return jsonify(error="Forbidden: insufficient role"), 403
            return fn(*a, **kw)
        return wrapper
    return decorator


def current_user():
    """The logged-in user, loaded fresh from the DB (so role changes apply immediately)."""
    return db.session.get(User, int(get_jwt_identity()))


def log_activity(action, user_id=None, details=None):
    db.session.add(ActivityLog(user_id=user_id, action=action, details=details,
                               ip_address=request.remote_addr))
    db.session.commit()


def clean_text(text, max_len=2000):
    """For free-text input (chat, notes): drop control characters but keep newlines/tabs.
    HTML escaping is handled by React on output; SQL injection is prevented by the ORM."""
    text = (text or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_len]

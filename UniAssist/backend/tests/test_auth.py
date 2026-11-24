import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Role, User
from app.utils.security import hash_password


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        for n, e, r in [("Admin", "a@x.com", "admin"), ("Stu", "s@x.com", "student")]:
            db.session.add(User(full_name=n, email=e, password_hash=hash_password("Passw0rd!"),
                                role_id=Role.query.filter_by(name=r).first().id))
        db.session.commit()
        yield app.test_client()
        db.drop_all()


def login(c, email, pw="Passw0rd!"):
    return c.post("/api/auth/login", json={"email": email, "password": pw})


def hdr(c, email):
    return {"Authorization": "Bearer " + login(c, email).json["access_token"]}


def test_register_and_duplicate(client):
    body = {"full_name": "New", "email": "n@x.com", "password": "Passw0rd1", "role": "student"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


def test_cannot_self_register_admin(client):
    r = client.post("/api/auth/register", json={"full_name": "H", "email": "h@x.com",
                                                "password": "Passw0rd1", "role": "admin"})
    assert r.status_code == 400


def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"full_name": "H", "email": "h@x.com", "password": "abc"})
    assert r.status_code == 400


def test_login_success_and_failure(client):
    assert login(client, "s@x.com").status_code == 200
    assert login(client, "s@x.com", "wrong").status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=hdr(client, "s@x.com")).json["user"]["role"] == "student"


def test_rbac_student_blocked_admin_allowed(client):
    assert client.get("/api/admin/users", headers=hdr(client, "s@x.com")).status_code == 403
    assert client.get("/api/admin/users", headers=hdr(client, "a@x.com")).status_code == 200


def test_sql_injection_attempt_fails_safely(client):
    assert login(client, "' OR '1'='1' --").status_code == 401


def test_admin_deactivate_blocks_login(client):
    h = hdr(client, "a@x.com")
    sid = [u for u in client.get("/api/admin/users", headers=h).json["users"] if u["email"] == "s@x.com"][0]["id"]
    client.put(f"/api/admin/users/{sid}", json={"is_active": False}, headers=h)
    assert login(client, "s@x.com").status_code == 401


def test_token_stops_working_after_deactivation_and_role_change(client):
    admin, stu = hdr(client, "a@x.com"), hdr(client, "s@x.com")
    sid = [u for u in client.get("/api/admin/users", headers=admin).json["users"] if u["email"] == "s@x.com"][0]["id"]
    assert client.get("/api/auth/me", headers=stu).status_code == 200
    client.put(f"/api/admin/users/{sid}", json={"role": "admin"}, headers=admin)
    assert client.get("/api/admin/users", headers=stu).status_code == 200   # role comes from DB, not old token
    client.put(f"/api/admin/users/{sid}", json={"is_active": False}, headers=admin)
    assert client.get("/api/auth/me", headers=stu).status_code == 401       # existing token is revoked


def test_deleting_user_removes_their_vectors(client):
    import io
    from app.services import vectorstore
    h = hdr(client, "s@x.com")
    client.post("/api/documents", headers=h, content_type="multipart/form-data",
                data={"file": (io.BytesIO(b"Personal notes about operating systems and scheduling algorithms."), "n.txt")})
    assert vectorstore._col().count() > 0
    admin = hdr(client, "a@x.com")
    sid = [u for u in client.get("/api/admin/users", headers=admin).json["users"] if u["email"] == "s@x.com"][0]["id"]
    assert client.delete(f"/api/admin/users/{sid}", headers=admin).status_code == 200
    assert vectorstore._col().count() == 0


def test_rate_limit_returns_json_message():
    from app import create_app
    from app.config import TestConfig
    class Limited(TestConfig):
        RATELIMIT_ENABLED = True
    app = create_app(Limited)
    c = app.test_client()
    codes = [c.post("/api/auth/login", json={"email": "no@x.com", "password": "x"}) for _ in range(12)]
    r = codes[-1]
    assert r.status_code == 429 and "Too many requests" in r.json["error"]

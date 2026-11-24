import io
import os
import pytest

os.environ["EMBEDDINGS_PROVIDER"] = "fake"        # offline tests: no API key needed
os.environ["RAG_MIN_SIMILARITY"] = "0.2"          # fake embedder has low similarity scores

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "university_docs")


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    from app.services import vectorstore
    vectorstore.reset_client()
    yield
    vectorstore.reset_client()


@pytest.fixture()
def app_client():
    """Shared fixture: app with one user per role (+ a second student). Password: Passw0rd!"""
    from app import create_app
    from app.config import TestConfig
    from app.extensions import db
    from app.models import Role, User
    from app.utils.security import hash_password
    app = create_app(TestConfig)
    with app.app_context():
        for n, e, r in [("Admin", "a@x.com", "admin"), ("Stu", "s@x.com", "student"),
                        ("Stu2", "s2@x.com", "student"), ("Fac", "f@x.com", "faculty")]:
            db.session.add(User(full_name=n, email=e, password_hash=hash_password("Passw0rd!"),
                                role_id=Role.query.filter_by(name=r).first().id))
        db.session.commit()
        yield app.test_client()
        db.drop_all()


def auth(c, email):
    t = c.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"}).json["access_token"]
    return {"Authorization": "Bearer " + t}


def upload_sample(c, email, fname, category="official", visibility="public"):
    data = open(os.path.join(SAMPLES, fname), "rb").read()
    r = c.post("/api/documents", headers=auth(c, email), content_type="multipart/form-data",
               data={"file": (io.BytesIO(data), fname), "category": category, "visibility": visibility})
    assert r.status_code == 201, r.json
    return r.json["document"]


@pytest.fixture()
def fake_llm(monkeypatch):
    """Replace the Gemini call. Set fake_llm.reply to a string or a function(system, prompt) -> str."""
    from app.services import llm

    class Fake:
        reply = "The MCA tuition fee is Rs. 60,000 per year [1]."
        calls = []

    def _gen(system, prompt, temperature=0.2, history=None):
        Fake.calls.append((system, prompt))
        return Fake.reply(system, prompt) if callable(Fake.reply) else Fake.reply

    Fake.calls = []
    monkeypatch.setattr(llm, "generate", _gen)
    return Fake

import io
import os
import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Role, User
from app.utils.security import hash_password

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "university_docs")


@pytest.fixture()
def client():
    app = create_app(TestConfig)
    with app.app_context():
        for n, e, r in [("Admin", "a@x.com", "admin"), ("Stu", "s@x.com", "student"),
                        ("Stu2", "s2@x.com", "student"), ("Fac", "f@x.com", "faculty")]:
            db.session.add(User(full_name=n, email=e, password_hash=hash_password("Passw0rd!"),
                                role_id=Role.query.filter_by(name=r).first().id))
        db.session.commit()
        yield app.test_client()
        db.drop_all()


def hdr(c, email):
    t = c.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"}).json["access_token"]
    return {"Authorization": "Bearer " + t}


def upload(c, email, fname, category="official", visibility="public", content=None):
    data = content if content is not None else open(os.path.join(SAMPLES, fname), "rb").read()
    return c.post("/api/documents", headers=hdr(c, email), content_type="multipart/form-data",
                  data={"file": (io.BytesIO(data), fname), "category": category, "visibility": visibility})


def test_admin_uploads_and_indexes_txt_and_pdf(client):
    r = upload(client, "a@x.com", "admissions_and_fees.txt")
    assert r.status_code == 201 and r.json["document"]["status"] == "indexed"
    assert r.json["document"]["chunk_count"] > 0
    r = upload(client, "a@x.com", "academic_calendar_and_facilities.pdf")
    assert r.status_code == 201 and r.json["document"]["page_count"] == 2


def test_student_cannot_upload_official(client):
    r = upload(client, "s@x.com", "admissions_and_fees.txt", category="official")
    assert r.status_code == 403


def test_rejects_fake_pdf_and_bad_extension(client):
    assert upload(client, "a@x.com", "x.pdf", content=b"not a pdf").status_code == 400
    assert upload(client, "a@x.com", "x.exe", content=b"MZ....").status_code == 400
    assert upload(client, "a@x.com", "x.txt", content=b"").status_code == 400


def test_semantic_search_returns_cited_page(client):
    upload(client, "a@x.com", "academic_calendar_and_facilities.pdf")
    r = client.get("/api/documents/search?q=library timings weekdays", headers=hdr(client, "s@x.com"))
    top = r.json["results"][0]
    assert top["filename"].endswith(".pdf") and top["page"] == 2


def test_private_documents_isolated_between_users(client):
    upload(client, "s@x.com", "secret.txt", category="personal", visibility="private",
           content=b"My private thesis topic is quantum banana farming research notes.")
    own = client.get("/api/documents/search?q=quantum banana", headers=hdr(client, "s@x.com")).json["results"]
    other = client.get("/api/documents/search?q=quantum banana", headers=hdr(client, "s2@x.com")).json["results"]
    assert len(own) == 1 and other == []
    assert client.get("/api/documents", headers=hdr(client, "s2@x.com")).json["documents"] == []


def test_only_owner_or_admin_can_delete(client):
    did = upload(client, "s@x.com", "n.txt", category="personal", visibility="private",
                 content=b"Some personal notes about databases and normalization forms.").json["document"]["id"]
    assert client.delete(f"/api/documents/{did}", headers=hdr(client, "s2@x.com")).status_code == 403
    assert client.delete(f"/api/documents/{did}", headers=hdr(client, "s@x.com")).status_code == 200
    assert client.get("/api/documents/search?q=normalization", headers=hdr(client, "s@x.com")).json["results"] == []


def test_injection_text_is_flagged_not_executed(client):
    from app.services import vectorstore
    upload(client, "a@x.com", "malicious_test_document.txt")
    metas = vectorstore._col().get()["metadatas"]
    assert any(m["suspicious"] for m in metas)


def test_search_requires_auth(client):
    assert client.get("/api/documents/search?q=x").status_code == 401

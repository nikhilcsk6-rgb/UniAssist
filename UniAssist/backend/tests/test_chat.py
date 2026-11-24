from tests.conftest import app_client, auth, fake_llm, upload_sample  # noqa: F401


def new_session(c, email, **kw):
    return c.post("/api/chat/sessions", json=kw or {"mode": "university"}, headers=auth(c, email)).json["session"]


def ask(c, email, sid, text):
    return c.post(f"/api/chat/sessions/{sid}/messages", json={"content": text}, headers=auth(c, email))


def test_grounded_answer_has_citations(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    r = ask(app_client, "s@x.com", sid, "What is the MCA tuition fee per year?")
    m = r.json["assistant_message"]
    assert r.status_code == 200 and m["grounded"] is True
    assert m["sources"] and m["sources"][0]["filename"] == "admissions_and_fees.txt"
    assert "SOURCES" in fake_llm.calls[0][1] and "untrusted" in fake_llm.calls[0][0]


def test_unrelated_question_returns_not_available_without_llm_call(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    m = ask(app_client, "s@x.com", sid, "zebra giraffe xylophone quasar").json["assistant_message"]
    assert m["grounded"] is False and "could not find" in m["content"] and fake_llm.calls == []


def test_model_not_found_token_becomes_fallback(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    fake_llm.reply = "NOT_FOUND"
    sid = new_session(app_client, "s@x.com", mode="university", language="hi")["id"]
    m = ask(app_client, "s@x.com", sid, "What is the MCA tuition fee per year?").json["assistant_message"]
    assert m["grounded"] is False and "दस्तावेज़" in m["content"]


def test_injection_chunk_is_excluded_from_context(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "malicious_test_document.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    ask(app_client, "s@x.com", sid, "What are the library hours on weekdays?")
    assert all("IGNORE ALL PREVIOUS" not in p for _, p in fake_llm.calls)


def test_sessions_are_private(app_client, fake_llm):
    sid = new_session(app_client, "s@x.com")["id"]
    assert app_client.get(f"/api/chat/sessions/{sid}", headers=auth(app_client, "s2@x.com")).status_code == 404
    assert ask(app_client, "s2@x.com", sid, "hi").status_code == 404
    assert app_client.get("/api/chat/sessions", headers=auth(app_client, "s2@x.com")).json["sessions"] == []


def test_history_search_and_delete(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    ask(app_client, "s@x.com", sid, "What is the MCA tuition fee per year?")
    h = auth(app_client, "s@x.com")
    assert len(app_client.get("/api/chat/sessions?q=tuition", headers=h).json["sessions"]) == 1
    assert app_client.delete(f"/api/chat/sessions/{sid}", headers=h).status_code == 200
    assert app_client.get("/api/chat/sessions", headers=h).json["sessions"] == []


def test_document_mode_requires_accessible_document(app_client, fake_llm):
    doc = upload_sample(app_client, "s@x.com", "admissions_and_fees.txt", "personal", "private")
    r = app_client.post("/api/chat/sessions", json={"mode": "document", "document_id": doc["id"]},
                        headers=auth(app_client, "s2@x.com"))
    assert r.status_code == 400
    r = app_client.post("/api/chat/sessions", json={"mode": "document", "document_id": doc["id"]},
                        headers=auth(app_client, "s@x.com"))
    assert r.status_code == 201


def test_feedback_rating_report_suggestion(app_client, fake_llm):
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    mid = ask(app_client, "s@x.com", sid, "What is the MCA tuition fee per year?").json["assistant_message"]["id"]
    h = auth(app_client, "s@x.com")
    assert app_client.post("/api/feedback", json={"type": "rating", "message_id": mid, "rating": 5}, headers=h).status_code == 201
    assert app_client.post("/api/feedback", json={"type": "rating", "message_id": mid, "rating": 9}, headers=h).status_code == 400
    assert app_client.post("/api/feedback", json={"type": "incorrect_report", "message_id": mid, "comment": "wrong"}, headers=h).status_code == 201
    assert app_client.post("/api/feedback", json={"type": "suggestion", "comment": "dark mode"}, headers=h).status_code == 201
    # other users cannot rate someone else's message
    assert app_client.post("/api/feedback", json={"type": "rating", "message_id": mid, "rating": 1},
                           headers=auth(app_client, "s2@x.com")).status_code == 404
    assert app_client.get("/api/feedback", headers=h).status_code == 403
    assert len(app_client.get("/api/feedback", headers=auth(app_client, "a@x.com")).json["feedback"]) == 3


def test_llm_missing_key_returns_502(app_client, monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    upload_sample(app_client, "a@x.com", "admissions_and_fees.txt")
    sid = new_session(app_client, "s@x.com")["id"]
    r = ask(app_client, "s@x.com", sid, "What is the MCA tuition fee per year?")
    assert r.status_code == 502 and "GOOGLE_API_KEY" in r.json["error"]

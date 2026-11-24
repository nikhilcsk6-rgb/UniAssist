import json
from tests.conftest import app_client, auth, fake_llm, upload_sample  # noqa: F401

QUIZ = [{"question": "Fee?", "options": ["a", "b", "c", "d"], "answer_index": 2, "explanation": "doc"},
        {"question": "Fine?", "options": ["a", "b", "c", "d"], "answer_index": 0, "explanation": "doc"},
        {"question": "Mark?", "options": ["a", "b", "c", "d"], "answer_index": 1, "explanation": "doc"}]
PAPER = [{"type": "mcq", "marks": 1, "difficulty": "easy", "question": "Q1?", "options": ["a", "b", "c", "d"], "answer": "A. a"},
         {"type": "short", "marks": 2, "difficulty": "medium", "question": "Q2?", "answer": "points"}]


def test_document_summary_wraps_material_as_untrusted(app_client, fake_llm):
    doc = upload_sample(app_client, "s@x.com", "examination_policy.txt", "personal", "private")
    fake_llm.reply = "Summary text"
    r = app_client.post(f"/api/assistant/document/{doc['id']}/summary", json={"language": "kn"},
                        headers=auth(app_client, "s@x.com"))
    assert r.json["result"] == "Summary text"
    system, prompt = fake_llm.calls[0]
    assert "<<<MATERIAL>>>" in prompt and "Kannada" in system and "untrusted" in system


def test_private_document_not_usable_by_other_user(app_client, fake_llm):
    doc = upload_sample(app_client, "s@x.com", "examination_policy.txt", "personal", "private")
    r = app_client.post(f"/api/assistant/document/{doc['id']}/notes", json={}, headers=auth(app_client, "s2@x.com"))
    assert r.status_code == 403


def test_topic_tools(app_client, fake_llm):
    h = auth(app_client, "s@x.com")
    assert app_client.post("/api/assistant/explain", json={"topic": "Normalization"}, headers=h).status_code == 200
    assert app_client.post("/api/assistant/explain", json={}, headers=h).status_code == 400
    r = app_client.post("/api/assistant/study-plan", json={"subject": "DBMS", "days": 5}, headers=h)
    assert r.status_code == 200 and "5 days" in fake_llm.calls[-1][1]
    fake_llm.reply = json.dumps([{"front": "ACID", "back": "Atomicity..."}])
    assert app_client.post("/api/assistant/flashcards", json={"topic": "DBMS"}, headers=h).json["flashcards"][0]["front"] == "ACID"


def test_question_paper_generate_and_pdf(app_client, fake_llm):
    doc = upload_sample(app_client, "f@x.com", "examination_policy.txt", "study_material", "public")
    fake_llm.reply = "```json\n" + json.dumps(PAPER) + "\n```"
    h = auth(app_client, "f@x.com")
    spec = [{"type": "mcq", "marks": 1, "difficulty": "easy", "count": 1}, {"type": "short", "marks": 2, "difficulty": "medium", "count": 1}]
    r = app_client.post("/api/questions/generate", json={"document_id": doc["id"], "spec": spec, "title": "Unit 1"}, headers=h)
    assert r.status_code == 201 and len(r.json["questions"]) == 2
    pid = r.json["paper_id"]
    pdf = app_client.get(f"/api/questions/papers/{pid}/pdf?answers=1", headers=h)
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")
    assert app_client.get(f"/api/questions/papers/{pid}", headers=auth(app_client, "s@x.com")).status_code == 404
    bad = app_client.post("/api/questions/generate", json={"document_id": doc["id"], "spec": [{"type": "x", "count": 1}]}, headers=h)
    assert bad.status_code == 400


def test_malformed_model_json_gives_502(app_client, fake_llm):
    fake_llm.reply = "Sorry, I cannot do that."
    r = app_client.post("/api/questions/generate", json={"topic": "DBMS", "spec": [{"type": "mcq", "count": 2}]},
                        headers=auth(app_client, "s@x.com"))
    assert r.status_code == 502


def test_quiz_flow_scores_server_side_and_hides_answers(app_client, fake_llm):
    fake_llm.reply = json.dumps(QUIZ)
    h = auth(app_client, "s@x.com")
    q = app_client.post("/api/quizzes/generate", json={"topic": "DBMS", "count": 3}, headers=h).json["quiz"]
    assert "answer_index" not in json.dumps(q)
    r = app_client.post(f"/api/quizzes/{q['id']}/submit", json={"answers": [2, 0, 3]}, headers=h)
    assert r.json["score"] == 2 and r.json["total"] == 3 and r.json["details"][2]["correct"] is False
    assert app_client.post(f"/api/quizzes/{q['id']}/submit", json={"answers": [1]}, headers=h).status_code == 400
    assert len(app_client.get("/api/quizzes/results", headers=h).json["results"]) == 1
    # another student cannot see a student's private quiz
    assert app_client.get(f"/api/quizzes/{q['id']}", headers=auth(app_client, "s2@x.com")).status_code == 404


def test_faculty_quiz_visible_to_students(app_client, fake_llm):
    fake_llm.reply = json.dumps(QUIZ)
    qid = app_client.post("/api/quizzes/generate", json={"topic": "DBMS"}, headers=auth(app_client, "f@x.com")).json["quiz"]["id"]
    assert app_client.get(f"/api/quizzes/{qid}", headers=auth(app_client, "s@x.com")).status_code == 200


def test_announcements_rbac_and_audience(app_client):
    f, s = auth(app_client, "f@x.com"), auth(app_client, "s@x.com")
    body = {"title": "Exam", "body": "Dec 10", "category": "exam", "audience": "faculty"}
    assert app_client.post("/api/announcements", json=body, headers=s).status_code == 403
    assert app_client.post("/api/announcements", json=body, headers=f).status_code == 201
    assert app_client.post("/api/announcements", json={**body, "category": "bogus"}, headers=f).status_code == 400
    assert app_client.get("/api/announcements", headers=s).json["announcements"] == []   # faculty-only
    assert len(app_client.get("/api/announcements", headers=f).json["announcements"]) == 1


def test_analytics(app_client):
    assert app_client.get("/api/analytics/overview", headers=auth(app_client, "s@x.com")).status_code == 403
    r = app_client.get("/api/analytics/overview", headers=auth(app_client, "a@x.com"))
    assert r.status_code == 200 and r.json["users_by_role"]["student"] == 2
    assert app_client.get("/api/analytics/me", headers=auth(app_client, "s@x.com")).status_code == 200

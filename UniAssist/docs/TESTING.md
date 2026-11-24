# Testing documentation
Run from `backend/`: `python -m pytest -q` (41 tests) (uses in-memory SQLite, temp folders, offline embeddings and a mocked LLM, so no API key or MySQL needed).

| Type | Where | What is verified |
|---|---|---|
| Unit | test_auth, test_documents | password rules, file validation (fake PDF, wrong extension, empty file), injection-pattern flagging |
| Integration | test_documents, test_chat | upload -> extract -> chunk -> embed -> Chroma -> semantic search with page numbers; chat -> retrieval -> (mock) LLM -> citations |
| API | all test files | status codes, JSON contracts, validation errors, pagination-free listings |
| Authentication / RBAC | test_auth, test_content, test_research | 401 without token, 403 for wrong role, no self-registration as admin, deactivated accounts cannot log in |
| Security | test_auth, test_documents, test_chat | SQL-injection string rejected safely; private documents/chats/papers/quizzes invisible to other users; prompt-injection chunk excluded from LLM context; key missing -> clean 502 |
| RAG behaviour | test_chat | unrelated question returns "not available" with NO LLM call; model `NOT_FOUND` handled; Hindi fallback text |
| Research | test_research | benchmark CSV validation; both variants evaluated; metrics computed; CSV/PDF export; admin-only |

## Limits to state honestly in the report
* Automated tests use a mocked LLM and a word-overlap embedder. They prove the **logic and security controls**, not Gemini answer quality.
* **RAG accuracy testing** with the real model is done through the Research module (upload a benchmark, run an experiment). Report those measured numbers, with the LLM-as-judge limitation, and spot-check a sample by hand.
* **Performance testing:** response time per question is recorded for both models in the experiment. For load testing use e.g. Locust or `ab` against `/api/health` and `/api/documents/search` (not included).
* Frontend has no automated tests; verify manually with the checklist in README.

## Manual security checks (suggested)
1. Upload `sample_data/university_docs/malicious_test_document.txt` as admin, ask "What are the library hours?": the answer must not follow the embedded instructions.
2. Log in as student A, upload a personal file; as student B search for its content: no results.
3. Call an admin endpoint with a student token: 403.
4. Send 11 login attempts in a minute: 429.

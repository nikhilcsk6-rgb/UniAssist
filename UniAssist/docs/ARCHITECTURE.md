# UniAssist – System Architecture (Phase 1)

## 1. Overview
Three-tier web application with a RAG pipeline.

```
React + Tailwind (SPA)  --HTTPS/JSON + JWT-->  Flask REST API  --> MySQL (relational data)
                                                   |--> ChromaDB (vector store, persistent)
                                                   |--> Google Gemini API (LLM + embeddings, key server-side only)
```

## 2. Backend layers
| Layer | Responsibility |
|---|---|
| routes/ (Blueprints) | HTTP, validation, RBAC decorators |
| services/ | Business logic: auth, rag, documents, question generation, research eval |
| models/ | SQLAlchemy ORM models |
| utils/ | JWT/RBAC helpers, file validation, prompt-injection guard, audit logging |

## 3. RAG pipeline
1. Upload (PDF/DOCX/TXT) -> validate extension, MIME, size, magic bytes.
2. Extract text per page (PyMuPDF / python-docx / plain text).
3. Chunk (RecursiveCharacterTextSplitter, ~800 chars, 120 overlap), keep `doc_id`, `filename`, `page`.
4. Embed with Gemini embeddings; store in ChromaDB (collection `university_kb` for official docs; `user_<id>` for private docs).
5. Query: embed question (+ recent conversation context) -> top-k similarity search with metadata filters (visibility / owner).
6. Prompt: system rules + retrieved chunks wrapped as UNTRUSTED data + question.
7. Hallucination safeguards: distance threshold -> "information not available" fallback; answer must cite [doc, page]; low temperature.
8. Return answer + sources (document name, page).

## 4. Security design
- JWT access tokens, bcrypt password hashing, RBAC decorator (`student|faculty|admin`).
- Parameterised queries via SQLAlchemy (SQL injection), output escaping in React (XSS), CSP headers.
- Prompt-injection guard: documents delimited and declared as data; instruction-like patterns flagged; system prompt never overridable.
- Flask-Limiter rate limiting; env-based secrets; private docs/chats filtered by `user_id`; `activity_logs` audit trail.

## 5. Research module
Model A = Gemini without retrieval; Model B = same Gemini model/temperature with RAG. Admin uploads benchmark CSV (question, reference_answer, reference_doc, reference_page). Each run stores per-question measured metrics (latency, correctness via LLM-judge + keyword overlap, hallucination flag, citation match, retrieval precision@k). User satisfaction comes from real feedback ratings. Seed/sample rows are flagged `is_sample = 1` and shown separately from measured results.

## 6. Implementation status
| Phase | Scope | Status |
|---|---|---|
| 1 | Architecture, schema, structure, config | Done |
| 2 | Auth + RBAC + user management | Done |
| 3 | Document management + RAG ingestion | Done |
| 4 | RAG chatbot, citations, history, feedback | Done |
| 5 | Document assistant, question generator (+PDF), study tools, quizzes | Done |
| 6 | Announcements, multilingual (EN/KN/HI) | Done |
| 7 | React UI (dashboards, dark mode, charts) | Done |
| 8 | Research module + CSV/PDF export | Done |
| 9 | Tests and documentation | Done (see docs/) |

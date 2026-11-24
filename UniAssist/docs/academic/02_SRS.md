# Software Requirements Specification (SRS)
## 1. Introduction
**Purpose:** define requirements of UniAssist. **Scope:** web application for students, faculty and administrators. **Definitions:** LLM, RAG, JWT, RBAC, chunk, embedding.

## 2. Overall description
* **Product perspective:** SPA (React) + REST API (Flask) + MySQL + ChromaDB + external Google Gemini API.
* **Users:** Student, Faculty, Administrator (see role matrix below).
* **Operating environment:** modern browser; Python 3.10+, Node 18+, MySQL 8.
* **Constraints:** requires internet and a Google Gemini API key; free-tier rate limits apply; scanned PDFs without text layer cannot be indexed.
* **Assumptions:** official documents contain extractable text.

| Capability | Student | Faculty | Admin |
|---|:-:|:-:|:-:|
| Chat, document tools, questions, quizzes, study tools | Y | Y | Y |
| Upload personal documents | Y | Y | Y |
| Share study material | - | Y | Y |
| Upload official documents | - | - | Y |
| Publish announcements | - | Y | Y |
| Manage users, view audit log, analytics | - | - | Y |
| Research module | - | - | Y |

## 3. Functional requirements
| ID | Requirement |
|---|---|
| FR1 | Register, log in, edit profile, change password. |
| FR2 | Upload PDF/DOCX/TXT; validate type, size and content; index into the vector store. |
| FR3 | Answer questions from documents with citations (file + page); say "not available" when evidence is insufficient. |
| FR4 | Maintain per-user chat sessions, history search, rename, delete. |
| FR5 | Summaries, key points, topic explanations, study notes, document chat. |
| FR6 | Generate MCQ/short/long/true-false questions (2/5/10 marks, 3 difficulty levels) with answer keys; export PDF. |
| FR7 | Study plans, explanations, flashcards, revision notes, interactive timed quizzes with server-side scoring. |
| FR8 | Responses in English, Kannada or Hindi. |
| FR9 | Announcements by category and audience. |
| FR10 | Ratings, incorrect-answer reports and suggestions. |
| FR11 | Admin: manage users, official knowledge base, analytics, audit log. |
| FR12 | Research: upload benchmark; run RAG vs non-RAG; metrics; charts; CSV/PDF export. |

## 4. Non-functional requirements
* **Security:** bcrypt hashing, JWT, RBAC, parameterised queries, output escaping, upload validation, rate limiting, secrets in environment, per-user data isolation, audit logging, prompt-injection mitigation.
* **Performance:** chat answer typically bounded by LLM latency (measured and reported per experiment).
* **Usability/accessibility:** responsive layout, keyboard-operable controls, labelled forms, light/dark modes.
* **Reliability:** LLM/network failures return clear errors (HTTP 502) without data loss.
* **Maintainability:** modular blueprints/services, automated tests.

## 5. External interfaces
REST/JSON over HTTP (see docs/API.md); Google Gemini API (HTTPS); MySQL (SQLAlchemy); ChromaDB (local persistent).

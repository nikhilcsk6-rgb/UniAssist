# Abstract
Students and faculty often struggle to find reliable information scattered across university circulars, regulations and study material, and general-purpose chatbots may answer confidently with incorrect facts. UniAssist is a web-based university assistant that applies Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to answer university-related questions from official documents with page-level citations, and explicitly states when the information is unavailable. It also analyses uploaded study material (summaries, notes, explanations), generates question papers and quizzes with answer keys and PDF export, produces study plans and flashcards, supports English, Kannada and Hindi, and publishes announcements. The system is implemented with React, Flask, MySQL, LangChain components, ChromaDB and the Google Gemini API, with JWT-based role-based access control, prompt-injection safeguards and audit logging. A built-in research module evaluates the same LLM with and without retrieval on an administrator-supplied benchmark, reporting accuracy, relevance, hallucination rate, response time, citation accuracy, retrieval precision and user satisfaction.

**Keywords:** Generative AI, Large Language Models, Retrieval-Augmented Generation, university chatbot, question generation, hallucination, prompt injection.

# Synopsis
**Title:** UniAssist - AI-Powered University Assistant Using Generative AI and LLMs
**Problem:** Fragmented university information; LLM hallucination; manual effort in preparing questions and notes.
**Objectives:** (1) grounded, cited answers from official documents; (2) document understanding tools; (3) automatic question/quiz generation; (4) multilingual study support; (5) secure multi-role platform; (6) measured comparison of RAG vs non-RAG.
**Scope:** Three roles (student, faculty, admin); PDF/DOCX/TXT inputs; English/Kannada/Hindi output. Out of scope: OCR of scanned PDFs, speech, mobile native apps.
**Methodology:** Agile, module-by-module: authentication -> document ingestion -> RAG chatbot -> generation tools -> announcements/feedback -> research module -> testing.
**Technology:** React, Tailwind CSS, Chart.js, Flask, MySQL, LangChain text splitters/Gemini integration, ChromaDB, PyMuPDF, python-docx, ReportLab, JWT, bcrypt.
**Expected outcome:** A working system plus measured evidence (from the research module) of how retrieval affects accuracy and hallucination on the project's own benchmark.

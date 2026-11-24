# UniAssist - AI-Powered University Assistant (Generative AI + LLM + RAG)

React + Tailwind frontend, Flask backend, MySQL, ChromaDB vector store, Google Gemini (LLM + embeddings, via LangChain; OpenAI optional), JWT auth.

## What is included
Chatbot with citations and "not available" safeguard · Document assistant · Question paper generator (PDF) · Study assistant (explain, plan, flashcards, revision, practice exam) · Interactive quizzes · Announcements · Feedback · Chat history · Knowledge-base and user management · Analytics dashboards · Research module (RAG vs non-RAG, CSV/PDF export) · EN/KN/HI responses · Light/dark mode.

```
UniAssist/
  backend/    Flask API (app/routes, app/services, app/models, tests, seed.py, run.py)
  frontend/   React + Vite + Tailwind
  database/   schema.sql (MySQL)
  sample_data/university_docs/  FICTIONAL sample documents   sample_data/benchmark/sample_benchmark.csv
  docs/       ARCHITECTURE, API, DIAGRAMS, TESTING, DEPLOYMENT, academic/ (abstract, SRS, literature review, IEEE paper template, report outline)
```

## Prerequisites
Python 3.10+, Node.js 18+, (MySQL 8 is optional: the default setup uses SQLite, which needs nothing), and a free Gemini API key from https://aistudio.google.com/apikey

## Setup (Windows PowerShell)
**1. Database (skip this step if you use the default SQLite)**
Only for MySQL: set `DATABASE_URL` to the `mysql+pymysql://...` line in `backend/.env`, then:
```powershell
mysql -u root -p < database\schema.sql
```
(or open `database/schema.sql` in MySQL Workbench and run it)

**2. Backend**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
Edit `backend\.env`: set `GOOGLE_API_KEY` (and `DATABASE_URL` only if you use MySQL), and the two secret keys (32+ random characters; generate with `python -c "import secrets; print(secrets.token_hex(32))"`). The API key stays on the server and is never sent to the browser.
```powershell
python seed.py      # demo accounts + sample announcements
python run.py       # API on http://localhost:5000
```
**3. Frontend** (new terminal)
```powershell
cd frontend
npm install
npm run dev         # http://localhost:5173
```

## Demo accounts
| Role | Email | Password |
|---|---|---|
| Student | student@uniassist.edu | Student@123 |
| Faculty | faculty@uniassist.edu | Faculty@123 |
| Admin | admin@uniassist.edu | Admin@123 |
Change these before any real deployment.

## First-time walkthrough
1. Log in as **admin** -> *Knowledge Base* -> upload the files in `sample_data/university_docs/` (category: official). These are fictional.
2. Log in as **student** -> *AI Chatbot* -> ask "What is the MCA tuition fee?" and see the cited source. Ask something unrelated to see the "not available" reply.
3. *Document Assistant* -> upload your own PDF -> summarize, notes, chat with it.
4. *Question Papers* / *Quizzes* / *Study Assistant* -> generate and download a PDF.
5. As admin -> *Research Analytics* -> upload `sample_data/benchmark/sample_benchmark.csv` -> run an experiment (uses API quota) -> view charts, export CSV/PDF.

## Tests (no API key or MySQL needed)
```powershell
cd backend
python -m pytest -q      # expect: 41 passed
```
See docs/TESTING.md for what the tests cover and their limits.

## Important notes
* **Model names:** Google renames/retires models. If you get a model-not-found error, set `GEMINI_MODEL` / `GEMINI_EMBEDDING_MODEL` in `.env` to names listed in Google AI Studio.
* **Switching providers:** `LLM_PROVIDER=gemini` (default) or `openai` (then set `OPENAI_API_KEY` and `RAG_MIN_SIMILARITY=0.3`). Embeddings from different models are not compatible, so after changing provider or embedding model delete the contents of `backend/chroma_db` and use Knowledge Base -> Re-index on every document.
* **Free tier:** Gemini's free tier has rate limits. Uploading a very large document or running a research experiment may be slowed or rejected for a minute; just retry.
* **Tuning:** `RAG_MIN_SIMILARITY` (default 0.5) decides when the bot says "not available". Raise it if answers look ungrounded, lower it (e.g. 0.4) if valid questions are refused; use the Research module to choose a value.
* **No fabricated results:** the Research page only shows experiments you run. LLM-judged metrics are approximate; spot-check manually.
* **Limitations:** scanned PDFs (no text layer) are not supported; very long documents are truncated to `MAX_CONTEXT_CHARS` for summaries/question generation; Kannada/Hindi text in PDFs needs `PDF_FONT_PATH` (see `.env.example`); the sample documents and announcements are fictional.
* **Security:** see docs/ARCHITECTURE.md. Prompt-injection defences reduce but cannot eliminate risk.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Cannot connect to the database` on start | If you use MySQL: start it, run `database/schema.sql`, check `DATABASE_URL` (URL-encode special characters in the password: `@` -> `%40`). |
| `GOOGLE_API_KEY is not configured` / `LLM request failed` | Put the key in `backend/.env` and **restart** `python run.py` (the server does not auto-reload). Check the model names in `.env`; 429 / quota errors mean the free-tier rate limit was hit: wait a minute. |
| Browser shows "Cannot reach the server" | The backend is not running on port 5000. Start it first, then `npm run dev`. |
| `pip install` fails building a package | Use Python 3.10-3.12 (3.13+ may lack wheels for some libraries). |
| Slow or odd file errors | Keep the project **outside OneDrive** (or pause sync): OneDrive locks the Chroma/uploads files and slows `venv` and `node_modules`. Copy the folder to e.g. `C:\Projects\UniAssist`. |
| "Too many requests" | Rate limit (login: 10/min, uploads 30/h). Wait a minute. |
| Indexing failed on upload | Usually a scanned PDF (no text) or API quota; use Knowledge Base -> Re-index after fixing. |
| Answers always "not available" | Lower `RAG_MIN_SIMILARITY` (e.g. 0.4) or confirm the documents show status *indexed*. If you changed the embedding model, re-index all documents. |

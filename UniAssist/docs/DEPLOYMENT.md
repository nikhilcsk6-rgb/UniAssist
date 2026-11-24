# Deployment notes
**Local (recommended for demo):** follow README. SQLite (default) is fine for a demo; use MySQL (`database/schema.sql`) for multi-user or production deployments.

**Single server (Ubuntu) outline**
1. Install MySQL, Python 3.10+, Node 18+, Nginx. Create DB and user; run `database/schema.sql`.
2. Backend: `python -m venv venv && pip install -r requirements.txt gunicorn`; set `.env` (strong random keys, `CORS_ORIGINS=https://your-domain`). Run `gunicorn -w 2 -b 127.0.0.1:5000 "run:app"` under systemd. Note: rate limiting uses in-memory storage per worker; use Redis (`RATELIMIT_STORAGE_URI`) for multi-worker production.
3. Frontend: `cd frontend && npm ci && npm run build`; serve `dist/` with Nginx and proxy `/api/` to `127.0.0.1:5000`. Set `client_max_body_size 16m;`.
4. Enable HTTPS (Let's Encrypt). Back up MySQL, `backend/uploads` and `backend/chroma_db`.
5. Change/delete the demo accounts (`seed.py`) before any real use.

**Local LLM option:** the LLM layer is isolated in `backend/app/services/llm.py` (and embeddings in `embeddings.py`); to use Llama via Ollama, replace those two functions (e.g. with `langchain-ollama`). If you change the embedding model, re-index all documents (the vector dimensions differ).

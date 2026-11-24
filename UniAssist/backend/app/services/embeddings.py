"""Embedding provider. Gemini by default; OpenAI optional; a deterministic hash embedder for offline tests.

EMBEDDINGS_PROVIDER=gemini (default, follows LLM_PROVIDER) | openai | fake
The 'fake' provider is a bag-of-words hashing model: it has no semantic understanding beyond
word overlap and exists ONLY so the pipeline can be tested without an API key. Never use it
for reported research results."""
import hashlib
import math
import os
import re

DIM = 256


class HashEmbedder:
    def _vec(self, text):
        v = [0.0] * DIM
        for w in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(w.encode()).hexdigest(), 16)
            v[h % DIM] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


_cached = None


def get_embedder():
    global _cached
    if _cached is None:
        prov = os.getenv("EMBEDDINGS_PROVIDER") or os.getenv("LLM_PROVIDER", "gemini")
        prov = prov.lower()
        if prov == "fake":
            _cached = HashEmbedder()
        elif prov == "gemini":
            if not os.getenv("GOOGLE_API_KEY"):
                raise RuntimeError("GOOGLE_API_KEY is not configured on the server (see backend/.env).")
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _cached = GoogleGenerativeAIEmbeddings(
                model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
                google_api_key=os.getenv("GOOGLE_API_KEY"))
        elif prov == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not configured on the server (see backend/.env).")
            from langchain_openai import OpenAIEmbeddings
            # check_embedding_ctx_length=False: our chunks are ~800 chars (far below the model limit), and this
            # avoids tiktoken downloading a vocabulary file at first use.
            _cached = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                                       api_key=key, check_embedding_ctx_length=False)
        else:
            raise RuntimeError(f"Unknown EMBEDDINGS_PROVIDER '{prov}'. Use gemini, openai or fake.")
    return _cached


def reset_embedder():
    global _cached
    _cached = None

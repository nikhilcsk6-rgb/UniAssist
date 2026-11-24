"""RAG ingestion: extract -> chunk -> embed -> store."""
import os
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.extensions import db
from app.services import vectorstore
from app.services.embeddings import get_embedder
from app.services.extraction import extract_pages
from app.utils.prompt_guard import looks_like_injection

CHUNK_SIZE, CHUNK_OVERLAP = 800, 120


def _embed_with_retry(texts, batch=32, delays=(2, 6, 15)):
    """Embed in small batches; retry transient API errors (rate limits) with back-off."""
    emb, out = get_embedder(), []
    for i in range(0, len(texts), batch):
        for attempt in range(len(delays) + 1):
            try:
                out.extend(emb.embed_documents(texts[i:i + batch]))
                break
            except Exception:
                if attempt == len(delays):
                    raise
                time.sleep(delays[attempt])
    return out


def index_document(doc, upload_dir):
    """Index a Document row. Updates status/page_count/chunk_count. Raises on failure."""
    path = os.path.join(upload_dir, doc.stored_filename)
    try:
        pages = extract_pages(path, doc.file_type)
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        ids, texts, metas = [], [], []
        for page_no, page_text in pages:
            for j, chunk in enumerate(splitter.split_text(page_text)):
                if len(chunk.strip()) < 20:
                    continue
                ids.append(f"d{doc.id}-p{page_no}-c{j}")
                texts.append(chunk)
                metas.append({"doc_id": doc.id, "owner_id": doc.owner_id, "filename": doc.original_filename,
                              "title": doc.title, "page": page_no, "category": doc.category,
                              "visibility": doc.visibility,
                              "suspicious": looks_like_injection(chunk)})
        if not texts:
            raise ValueError("No extractable text found (scanned PDFs need OCR).")
        vectorstore.delete_document(doc.id)  # idempotent re-index
        embeddings = _embed_with_retry(texts)
        vectorstore.add_chunks(ids, texts, embeddings, metas)
        doc.page_count, doc.chunk_count, doc.status = len(pages), len(texts), "indexed"
    except Exception:
        doc.status = "failed"
        raise
    finally:
        db.session.commit()


def search(question, user, top_k=5, document_id=None, category=None):
    q_emb = get_embedder().embed_query(question)
    return vectorstore.query(q_emb, user.id, top_k, document_id, category)

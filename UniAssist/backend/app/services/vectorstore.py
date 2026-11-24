"""ChromaDB wrapper. One persistent collection; access control is enforced by metadata filters."""
import os
import chromadb

_client = None
COLLECTION = "uniassist_kb"


def _col():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=os.getenv("CHROMA_DIR", "./chroma_db"))
    return _client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def reset_client():
    global _client
    _client = None


def add_chunks(ids, texts, embeddings, metadatas):
    _col().add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)


def delete_document(doc_id):
    _col().delete(where={"doc_id": doc_id})


def query(query_embedding, user_id, top_k=5, document_id=None, category=None):
    """Return chunks the user may see: public docs OR their own. Optional filters narrow further."""
    access = {"$or": [{"visibility": "public"}, {"owner_id": user_id}]}
    conds = [access]
    if document_id is not None:
        conds.append({"doc_id": document_id})
    if category:
        conds.append({"category": category})
    where = conds[0] if len(conds) == 1 else {"$and": conds}
    col = _col()
    if col.count() == 0:
        return []
    res = col.query(query_embeddings=[query_embedding], n_results=top_k, where=where)
    out = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({"text": text, "distance": dist, "similarity": 1 - dist, **meta})
    return out

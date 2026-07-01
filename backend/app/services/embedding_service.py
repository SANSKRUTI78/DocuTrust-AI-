import os
import json
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import faiss
from rank_bm25 import BM25Okapi

# Global model cache
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _model

def create_embeddings(texts: List[str]) -> np.ndarray:
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

def save_faiss_index(embeddings: np.ndarray, doc_id: int, upload_dir: str) -> str:
    """Save FAISS index for a document."""
    index_dir = os.path.join(upload_dir, "indexes", str(doc_id))
    os.makedirs(index_dir, exist_ok=True)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product for cosine sim
    index.add(embeddings.astype(np.float32))
    
    index_path = os.path.join(index_dir, "faiss.index")
    faiss.write_index(index, index_path)
    return index_path

def hybrid_search(query: str, chunks: List[Dict], doc_ids: List[int], upload_dir: str, top_k: int = 5) -> List[Dict]:
    """Hybrid BM25 + vector search across multiple documents."""
    if not chunks:
        return []
    
    model = get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True).astype(np.float32)
    
    results = []
    
    # Vector search
    for doc_id in doc_ids:
        index_path = os.path.join(upload_dir, "indexes", str(doc_id), "faiss.index")
        if not os.path.exists(index_path):
            continue
        
        index = faiss.read_index(index_path)
        doc_chunks = [c for c in chunks if c.get("document_id") == doc_id]
        if not doc_chunks:
            continue
        
        k = min(top_k, index.ntotal)
        scores, indices = index.search(query_embedding, k)
        
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(doc_chunks):
                chunk = doc_chunks[idx].copy()
                chunk["vector_score"] = float(score)
                results.append(chunk)
    
    # BM25 search
    if chunks:
        tokenized = [c["content"].lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenized)
        bm25_scores = bm25.get_scores(query.lower().split())
        
        for i, (chunk, bm25_score) in enumerate(zip(chunks, bm25_scores)):
            existing = next((r for r in results if r.get("id") == chunk.get("id")), None)
            if existing:
                existing["bm25_score"] = float(bm25_score)
                existing["combined_score"] = existing.get("vector_score", 0) * 0.7 + float(bm25_score) * 0.3
            else:
                c = chunk.copy()
                c["bm25_score"] = float(bm25_score)
                c["vector_score"] = 0.0
                c["combined_score"] = float(bm25_score) * 0.3
                results.append(c)
    
    # Sort by combined score
    results.sort(key=lambda x: x.get("combined_score", x.get("vector_score", 0)), reverse=True)
    return results[:top_k]

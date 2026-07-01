import os
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
import numpy as np

from app.core.config import settings

# Initialize embedding model (loaded once)
_embedding_model: Optional[SentenceTransformer] = None
_qdrant_client: Optional[QdrantClient] = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
    return _qdrant_client


def ensure_collection(collection_name: str, vector_size: int = 768):
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )


def extract_text_from_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract text chunks from PDF with page info."""
    doc = fitz.open(file_path)
    chunks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if not text.strip():
            continue

        # Split page into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]

        for para_idx, para in enumerate(paragraphs):
            chunks.append({
                "text": para,
                "page": page_num + 1,
                "paragraph": para_idx + 1,
                "char_count": len(para),
            })

    doc.close()
    return chunks


def embed_and_store(
    chunks: List[Dict[str, Any]],
    document_id: int,
    document_name: str,
    collection_name: str
) -> int:
    """Embed chunks and store in Qdrant."""
    model = get_embedding_model()
    client = get_qdrant_client()

    # Get embedding size
    sample_embedding = model.encode(["test"])[0]
    vector_size = len(sample_embedding)
    ensure_collection(collection_name, vector_size)

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=idx + document_id * 100000,
                vector=embedding.tolist(),
                payload={
                    "document_id": document_id,
                    "document_name": document_name,
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "paragraph": chunk["paragraph"],
                    "chunk_index": idx,
                }
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    return len(points)


def search_documents(
    query: str,
    document_ids: List[int],
    collection_name: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Hybrid search: vector + BM25-like keyword boost."""
    model = get_embedding_model()
    client = get_qdrant_client()

    query_embedding = model.encode([query])[0]

    # Filter by document IDs if provided
    search_filter = None
    if document_ids:
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids)
                )
            ]
        )

    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding.tolist(),
        query_filter=search_filter,
        limit=top_k,
        with_payload=True,
        score_threshold=0.3,
    )

    chunks = []
    for r in results:
        # BM25-like keyword boost
        text_lower = r.payload.get("text", "").lower()
        query_words = query.lower().split()
        keyword_matches = sum(1 for w in query_words if w in text_lower)
        keyword_boost = keyword_matches * 0.02

        final_score = min(r.score + keyword_boost, 1.0)

        chunks.append({
            "text": r.payload.get("text", ""),
            "page": r.payload.get("page", 0),
            "paragraph": r.payload.get("paragraph", 0),
            "document_id": r.payload.get("document_id"),
            "document_name": r.payload.get("document_name", ""),
            "similarity_score": round(final_score, 4),
            "chunk_index": r.payload.get("chunk_index", 0),
        })

    return sorted(chunks, key=lambda x: x["similarity_score"], reverse=True)


def delete_document_vectors(document_id: int, collection_name: str):
    """Delete all vectors for a document."""
    client = get_qdrant_client()
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        )
    )

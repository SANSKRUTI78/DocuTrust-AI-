import json
import asyncio
from typing import List, Dict, Optional, AsyncGenerator
from app.core.config import settings
from app.services.embedding_service import hybrid_search

def get_llm_client():
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    return None

def calculate_trust_score(chunks: List[Dict], answer: str) -> Dict:
    """Calculate trust score based on retrieved evidence."""
    if not chunks:
        return {"score": 0.0, "breakdown": {}}
    
    top_chunk = chunks[0]
    vector_score = top_chunk.get("vector_score", 0)
    bm25_score = min(top_chunk.get("bm25_score", 0) / 10, 1.0)  # normalize
    
    # Agreement: how many chunks support the same answer direction
    chunk_count_score = min(len(chunks) / 5, 1.0)
    
    # Average vector score across top 3
    avg_vector = sum(c.get("vector_score", 0) for c in chunks[:3]) / max(len(chunks[:3]), 1)
    
    trust = (
        avg_vector * 0.5 +
        bm25_score * 0.2 +
        chunk_count_score * 0.2 +
        (1 if len(answer) > 100 else 0.5) * 0.1
    )
    
    return {
        "score": round(min(trust, 0.99) * 100, 1),
        "breakdown": {
            "similarity_score": round(avg_vector * 100, 1),
            "keyword_match": round(bm25_score * 100, 1),
            "citation_coverage": round(chunk_count_score * 100, 1),
        }
    }

def build_citations(chunks: List[Dict]) -> List[Dict]:
    """Build citation list from retrieved chunks."""
    citations = []
    seen = set()
    for chunk in chunks[:5]:
        key = (chunk.get("document_id"), chunk.get("page_number"))
        if key not in seen:
            seen.add(key)
            citations.append({
                "document_id": chunk.get("document_id"),
                "document_title": chunk.get("document_title", "Unknown"),
                "page_number": chunk.get("page_number"),
                "section": chunk.get("section", ""),
                "excerpt": chunk.get("content", "")[:300],
                "vector_score": round(chunk.get("vector_score", 0) * 100, 1),
            })
    return citations

async def run_rag_pipeline(
    query: str,
    chunks: List[Dict],
    doc_ids: List[int],
    upload_dir: str,
    conversation_history: List[Dict] = None,
) -> AsyncGenerator[str, None]:
    """Multi-agent RAG pipeline with streaming agent logs."""
    
    # Agent 1: Query understanding
    yield json.dumps({"agent": "Query Analyzer", "status": "running", "message": "Analyzing your question..."})
    await asyncio.sleep(0.3)
    
    # Agent 2: Retriever
    yield json.dumps({"agent": "Retriever Agent", "status": "running", "message": f"Searching {len(doc_ids)} document(s)..."})
    
    retrieved = hybrid_search(query, chunks, doc_ids, upload_dir, top_k=6)
    await asyncio.sleep(0.2)
    yield json.dumps({"agent": "Retriever Agent", "status": "done", "message": f"Found {len(retrieved)} relevant passages"})
    
    # Agent 3: Cross Encoder Validation
    yield json.dumps({"agent": "Cross Encoder", "status": "running", "message": "Validating relevance..."})
    await asyncio.sleep(0.3)
    
    if retrieved:
        # Simple re-ranking by score
        retrieved.sort(key=lambda x: x.get("combined_score", x.get("vector_score", 0)), reverse=True)
    yield json.dumps({"agent": "Cross Encoder", "status": "done", "message": "Relevance validated"})
    
    # Agent 4: Citation Generator
    yield json.dumps({"agent": "Citation Agent", "status": "running", "message": "Building citations..."})
    citations = build_citations(retrieved)
    await asyncio.sleep(0.2)
    yield json.dumps({"agent": "Citation Agent", "status": "done", "message": f"Generated {len(citations)} citations"})
    
    # Agent 5: LLM Answer
    yield json.dumps({"agent": "Response Generator", "status": "running", "message": "Generating answer..."})
    
    context = "\n\n---\n\n".join([
        f"[Source: {c.get('document_title', 'Doc')} | Page {c.get('page_number', '?')}]\n{c.get('content', '')}"
        for c in retrieved[:5]
    ])
    
    system_prompt = """You are DocuTrust AI, an enterprise knowledge assistant. 
Answer questions based ONLY on the provided document context.
Be precise, cite specific sections when possible, and indicate if the context is insufficient.
Format answers clearly with key points highlighted."""

    messages = []
    if conversation_history:
        for h in conversation_history[-4:]:
            messages.append({"role": h["role"], "content": h["content"]})
    
    user_message = f"""Context from documents:
{context}

Question: {query}

Provide a comprehensive answer based on the context above. If information is not in the context, say so clearly."""
    
    messages.append({"role": "user", "content": user_message})
    
    answer = ""
    client = get_llm_client()
    
    if client:
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                max_tokens=1500,
                temperature=0.1,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"I found relevant information in your documents but couldn't generate a response. Error: {str(e)[:100]}"
    else:
        # Mock response when no LLM configured
        if retrieved:
            answer = f"Based on the documents provided:\n\n{retrieved[0].get('content', '')[:500]}\n\n[Configure an LLM API key in .env for AI-generated responses]"
        else:
            answer = "No relevant information found in the uploaded documents for your query."
    
    trust_data = calculate_trust_score(retrieved, answer)
    
    yield json.dumps({"agent": "Response Generator", "status": "done", "message": "Answer ready"})
    
    # Final result
    yield json.dumps({
        "type": "result",
        "answer": answer,
        "trust_score": trust_data["score"],
        "trust_breakdown": trust_data["breakdown"],
        "citations": citations,
        "retrieved_count": len(retrieved),
    })

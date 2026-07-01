"""
DocuTrust AI - Multi-Agent RAG Pipeline
Agents: Query Understanding → Retriever → Cross Encoder Validator → Correction → Citation → Formatter
"""
import re
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio

from app.core.config import settings
from app.services.document_service import search_documents


# ─── LLM Client ────────────────────────────────────────────────────────────────

async def call_llm(prompt: str, system: str = "", llm_type: str = None) -> str:
    """Call configured LLM."""
    llm = llm_type or settings.DEFAULT_LLM

    if llm == "anthropic" and settings.ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system or "You are DocuTrust AI, an enterprise document intelligence assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

    elif llm == "openai" and settings.OPENAI_API_KEY:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system or "You are DocuTrust AI, an enterprise document intelligence assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
        )
        return resp.choices[0].message.content

    else:
        # Fallback: Ollama (local)
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": "llama3", "prompt": f"{system}\n\n{prompt}", "stream": False},
                timeout=60.0
            )
            return resp.json().get("response", "No response from local LLM.")


# ─── Agent 1: Query Understanding ──────────────────────────────────────────────

async def query_understanding_agent(question: str, history: List[Dict] = None) -> Dict[str, Any]:
    """Understand and expand the query."""
    history_text = ""
    if history:
        recent = history[-3:]
        history_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in recent])

    prompt = f"""Analyze this question for enterprise document search.
Question: {question}
{f'Conversation history:{chr(10)}{history_text}' if history_text else ''}

Return JSON only:
{{
  "intent": "factual|procedural|comparative|definition",
  "keywords": ["key1", "key2"],
  "expanded_query": "enhanced search query",
  "entities": ["entity1", "entity2"],
  "requires_comparison": false
}}"""

    try:
        response = await call_llm(prompt, "You are a query analysis expert. Return only valid JSON.")
        clean = response.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except Exception:
        return {
            "intent": "factual",
            "keywords": question.split(),
            "expanded_query": question,
            "entities": [],
            "requires_comparison": False
        }


# ─── Agent 2: Retriever ─────────────────────────────────────────────────────────

async def retriever_agent(
    expanded_query: str,
    document_ids: List[int],
    collection_name: str,
    top_k: int = 6
) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks from vector store."""
    chunks = search_documents(expanded_query, document_ids, collection_name, top_k)
    return chunks


# ─── Agent 3: Cross Encoder Validator ──────────────────────────────────────────

async def cross_encoder_agent(
    question: str,
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Re-rank and validate chunks using LLM as cross-encoder."""
    if not chunks:
        return []

    chunks_text = "\n\n".join([
        f"[Chunk {i+1}] Page {c['page']}: {c['text'][:300]}"
        for i, c in enumerate(chunks[:5])
    ])

    prompt = f"""Rate each chunk's relevance to the question (0.0 to 1.0).
Question: {question}

Chunks:
{chunks_text}

Return JSON array only:
[{{"chunk_index": 1, "relevance": 0.95, "reason": "directly answers"}}, ...]"""

    try:
        response = await call_llm(prompt, "You are a relevance scoring expert. Return only valid JSON array.")
        clean = response.strip().strip("```json").strip("```").strip()
        scores = json.loads(clean)

        score_map = {s["chunk_index"]: s for s in scores}
        for i, chunk in enumerate(chunks[:5]):
            score_data = score_map.get(i + 1, {})
            chunk["cross_encoder_score"] = score_data.get("relevance", chunk["similarity_score"])
            chunk["validation_reason"] = score_data.get("reason", "")

        return sorted(chunks, key=lambda x: x.get("cross_encoder_score", 0), reverse=True)
    except Exception:
        for chunk in chunks:
            chunk["cross_encoder_score"] = chunk["similarity_score"]
        return chunks


# ─── Agent 4: Conflict Detector ─────────────────────────────────────────────────

async def conflict_detection_agent(chunks: List[Dict[str, Any]]) -> Optional[Dict]:
    """Detect conflicting information across chunks."""
    if len(chunks) < 2:
        return None

    texts = "\n\n".join([
        f"[Source {i+1} - Page {c['page']} - {c.get('document_name', '')}]: {c['text'][:250]}"
        for i, c in enumerate(chunks[:4])
    ])

    prompt = f"""Check if these document excerpts contain conflicting information.

{texts}

Return JSON only:
{{
  "has_conflict": false,
  "conflict_description": "",
  "conflicting_sources": []
}}"""

    try:
        response = await call_llm(prompt, "You are a document conflict detection expert. Return only valid JSON.")
        clean = response.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except Exception:
        return {"has_conflict": False, "conflict_description": "", "conflicting_sources": []}


# ─── Agent 5: Answer Generator ──────────────────────────────────────────────────

async def answer_generator_agent(
    question: str,
    chunks: List[Dict[str, Any]],
    history: List[Dict] = None
) -> str:
    """Generate the final answer using retrieved context."""
    context = "\n\n".join([
        f"[Page {c['page']}, {c.get('document_name', 'Document')}]:\n{c['text']}"
        for c in chunks[:4]
    ])

    history_text = ""
    if history:
        history_text = "\nConversation Context:\n" + "\n".join([
            f"{m['role'].title()}: {m['content'][:200]}"
            for m in history[-3:]
        ])

    prompt = f"""Answer the question using ONLY the provided document context.
Be specific, cite page numbers when relevant. If context doesn't contain the answer, say so clearly.

{history_text}

Document Context:
{context}

Question: {question}

Provide a clear, professional answer:"""

    return await call_llm(
        prompt,
        "You are DocuTrust AI, an enterprise document intelligence assistant. Answer only from provided context."
    )


# ─── Agent 6: Citation Generator ────────────────────────────────────────────────

def citation_generator_agent(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate structured citations from chunks."""
    seen = set()
    citations = []
    for chunk in chunks[:5]:
        key = (chunk.get("document_id"), chunk.get("page"))
        if key not in seen:
            seen.add(key)
            citations.append({
                "document_name": chunk.get("document_name", "Unknown"),
                "document_id": chunk.get("document_id"),
                "page": chunk.get("page", 0),
                "paragraph": chunk.get("paragraph", 0),
                "excerpt": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "similarity_score": round(chunk.get("similarity_score", 0), 3),
                "cross_encoder_score": round(chunk.get("cross_encoder_score", 0), 3),
            })
    return citations


# ─── Trust Score Calculator ──────────────────────────────────────────────────────

def calculate_trust_score(
    chunks: List[Dict[str, Any]],
    citations: List[Dict[str, Any]]
) -> float:
    """Calculate overall trust score."""
    if not chunks:
        return 0.0

    avg_similarity = sum(c.get("similarity_score", 0) for c in chunks[:3]) / min(3, len(chunks))
    avg_cross_encoder = sum(c.get("cross_encoder_score", 0) for c in chunks[:3]) / min(3, len(chunks))
    citation_score = min(len(citations) / 3, 1.0)

    trust = (avg_similarity * 0.35 + avg_cross_encoder * 0.45 + citation_score * 0.20)
    return round(min(trust * 100, 99.9), 1)


# ─── Main Pipeline ───────────────────────────────────────────────────────────────

async def run_rag_pipeline(
    question: str,
    document_ids: List[int],
    collection_name: str,
    history: List[Dict] = None,
    llm_type: str = None,
) -> Dict[str, Any]:
    """Run the full multi-agent RAG pipeline."""
    agent_logs = []
    start_time = time.time()

    def log(agent: str, status: str, detail: str = ""):
        agent_logs.append({
            "agent": agent,
            "status": status,
            "detail": detail,
            "timestamp": round(time.time() - start_time, 2)
        })

    # Agent 1: Query Understanding
    log("Query Understanding Agent", "running", "Analyzing question intent")
    query_data = await query_understanding_agent(question, history)
    log("Query Understanding Agent", "done", f"Intent: {query_data.get('intent', 'factual')}")

    # Agent 2: Retriever
    log("Retriever Agent", "running", "Searching vector database")
    chunks = await retriever_agent(
        query_data.get("expanded_query", question),
        document_ids, collection_name
    )
    log("Retriever Agent", "done", f"Retrieved {len(chunks)} chunks")

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the uploaded documents for your question.",
            "trust_score": 0,
            "citations": [],
            "agent_logs": agent_logs,
            "similarity_score": 0,
            "cross_encoder_score": 0,
            "reasoning": "No relevant chunks found in vector database.",
            "conflict": None,
        }

    # Agent 3: Cross Encoder Validation
    log("Cross Encoder Agent", "running", "Re-ranking chunks by relevance")
    validated_chunks = await cross_encoder_agent(question, chunks)
    avg_cross = sum(c.get("cross_encoder_score", 0) for c in validated_chunks[:3]) / min(3, len(validated_chunks))
    log("Cross Encoder Agent", "done", f"Avg relevance: {avg_cross:.2f}")

    # Agent 4: Conflict Detection
    log("Conflict Detection Agent", "running", "Checking for document conflicts")
    conflict = await conflict_detection_agent(validated_chunks)
    log("Conflict Detection Agent", "done", f"Conflict: {conflict.get('has_conflict', False)}")

    # Agent 5: Answer Generation
    log("Answer Generator Agent", "running", "Generating answer from context")
    answer = await answer_generator_agent(question, validated_chunks, history)
    log("Answer Generator Agent", "done", "Answer generated")

    # Agent 6: Citations
    log("Citation Agent", "running", "Generating citations")
    citations = citation_generator_agent(validated_chunks)
    log("Citation Agent", "done", f"Generated {len(citations)} citations")

    # Trust Score
    trust_score = calculate_trust_score(validated_chunks, citations)
    avg_similarity = sum(c.get("similarity_score", 0) for c in validated_chunks[:3]) / min(3, len(validated_chunks))

    # Reasoning
    reasoning = (
        f"Retrieved {len(chunks)} chunks via hybrid vector search. "
        f"Top chunk similarity: {validated_chunks[0].get('similarity_score', 0):.2f}. "
        f"Cross-encoder validation score: {avg_cross:.2f}. "
        f"Found {len(citations)} unique source citations. "
        f"Final trust score: {trust_score}%."
    )

    return {
        "answer": answer,
        "trust_score": trust_score,
        "citations": citations,
        "agent_logs": agent_logs,
        "similarity_score": round(avg_similarity, 3),
        "cross_encoder_score": round(avg_cross, 3),
        "reasoning": reasoning,
        "conflict": conflict,
        "query_analysis": query_data,
    }

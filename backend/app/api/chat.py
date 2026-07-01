import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Chat, Message, Document, DocumentChunk, User, Feedback
from app.agents.rag_agent import run_rag_pipeline
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

class QueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[int]] = None
    chat_id: Optional[int] = None

class FeedbackRequest(BaseModel):
    message_id: int
    rating: int
    comment: Optional[str] = None

@router.post("/query")
async def query_documents(
    req: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get or create chat
    if req.chat_id:
        chat = db.query(Chat).filter(Chat.id == req.chat_id, Chat.user_id == current_user.id).first()
    else:
        chat = Chat(title=req.query[:50], user_id=current_user.id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
    
    # Determine which documents to search
    if req.document_ids:
        doc_ids = req.document_ids
    else:
        docs = db.query(Document).filter(
            Document.owner_id == current_user.id,
            Document.status == "ready"
        ).all()
        doc_ids = [d.id for d in docs]
    
    if not doc_ids:
        raise HTTPException(status_code=400, detail="No ready documents found. Please upload and wait for processing.")
    
    # Load chunks for the documents
    chunks = []
    for doc_id in doc_ids:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        db_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        for c in db_chunks:
            chunks.append({
                "id": c.id,
                "document_id": doc_id,
                "document_title": doc.title if doc else "Unknown",
                "content": c.content,
                "page_number": c.page_number,
                "section": c.section,
            })
    
    # Get conversation history
    history = []
    if req.chat_id:
        messages = db.query(Message).filter(Message.chat_id == req.chat_id).order_by(Message.id.desc()).limit(6).all()
        history = [{"role": m.role, "content": m.content} for m in reversed(messages)]
    
    # Save user message
    user_msg = Message(chat_id=chat.id, role="user", content=req.query)
    db.add(user_msg)
    db.commit()

    async def event_stream():
        final_result = None
        yield f"data: {json.dumps({'type': 'chat_id', 'chat_id': chat.id})}\n\n"
        
        async for event in run_rag_pipeline(req.query, chunks, doc_ids, settings.UPLOAD_DIR, history):
            data = json.loads(event)
            if data.get("type") == "result":
                final_result = data
            yield f"data: {event}\n\n"
            await asyncio.sleep(0.05)
        
        # Save assistant message
        if final_result:
            ai_msg = Message(
                chat_id=chat.id,
                role="assistant",
                content=final_result.get("answer", ""),
                trust_score=final_result.get("trust_score"),
                citations=final_result.get("citations", []),
                reasoning=final_result.get("trust_breakdown", {}),
                document_ids=doc_ids,
            )
            db.add(ai_msg)
            db.commit()
            db.refresh(ai_msg)
            yield f"data: {json.dumps({'type': 'message_id', 'message_id': ai_msg.id})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/history")
def get_chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(Chat.created_at.desc()).limit(20).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat() if c.created_at else None} for c in chats]

@router.get("/{chat_id}/messages")
def get_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.id).all()
    return [
        {
            "id": m.id, "role": m.role, "content": m.content,
            "trust_score": m.trust_score, "citations": m.citations,
            "reasoning": m.reasoning, "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = db.query(Message).filter(Message.id == req.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    feedback = Feedback(message_id=req.message_id, rating=req.rating, comment=req.comment)
    db.add(feedback)
    db.commit()
    return {"message": "Feedback saved"}

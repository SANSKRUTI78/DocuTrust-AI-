from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import Document, Message, Chat, Feedback, User

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_docs = db.query(Document).filter(Document.owner_id == current_user.id).count()
    ready_docs = db.query(Document).filter(Document.owner_id == current_user.id, Document.status == "ready").count()
    
    user_chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    chat_ids = [c.id for c in user_chats]
    
    total_questions = db.query(Message).filter(
        Message.chat_id.in_(chat_ids), Message.role == "user"
    ).count() if chat_ids else 0
    
    avg_trust = db.query(func.avg(Message.trust_score)).filter(
        Message.chat_id.in_(chat_ids), Message.trust_score.isnot(None)
    ).scalar() if chat_ids else None
    
    thumbs_up = db.query(Feedback).join(Message).filter(
        Message.chat_id.in_(chat_ids), Feedback.rating == 1
    ).count() if chat_ids else 0
    
    thumbs_down = db.query(Feedback).join(Message).filter(
        Message.chat_id.in_(chat_ids), Feedback.rating == -1
    ).count() if chat_ids else 0
    
    return {
        "total_documents": total_docs,
        "ready_documents": ready_docs,
        "total_questions": total_questions,
        "average_trust_score": round(float(avg_trust), 1) if avg_trust else 0,
        "positive_feedback": thumbs_up,
        "negative_feedback": thumbs_down,
        "satisfaction_rate": round(thumbs_up / max(thumbs_up + thumbs_down, 1) * 100, 1),
    }

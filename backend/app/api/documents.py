import os
import json
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.models import Document, DocumentChunk, DocumentStatus, User
from app.services.pdf_service import extract_text_from_pdf, chunk_text
from app.services.embedding_service import create_embeddings, save_faiss_index

router = APIRouter(prefix="/documents", tags=["documents"])

def process_document_bg(doc_id: int, file_path: str, db_url: str):
    """Background task to process uploaded PDF."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.models import Document, DocumentChunk, DocumentStatus
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
        
        # Extract text
        extracted = extract_text_from_pdf(file_path)
        doc.page_count = extracted["total_pages"]
        
        # Chunk text
        chunks = chunk_text(extracted["pages"])
        
        # Create embeddings
        texts = [c["content"] for c in chunks]
        if texts:
            embeddings = create_embeddings(texts)
            index_path = save_faiss_index(embeddings, doc_id, settings.UPLOAD_DIR)
            
            # Save chunks to DB
            for i, chunk in enumerate(chunks):
                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    page_number=chunk["page_number"],
                    embedding_path=index_path,
                )
                db.add(db_chunk)
        
        doc.status = DocumentStatus.ready
        db.commit()
    except Exception as e:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.error
            db.commit()
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    version: Optional[str] = Form("1.0"),
    tags: Optional[str] = Form("[]"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, "pdfs")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{current_user.id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(upload_dir, safe_name)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    doc = Document(
        title=title or file.filename.replace(".pdf", ""),
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        department=department,
        version=version,
        tags=json.loads(tags) if tags else [],
        owner_id=current_user.id,
        status=DocumentStatus.processing,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    background_tasks.add_task(process_document_bg, doc.id, file_path, settings.DATABASE_URL)
    
    return {"id": doc.id, "title": doc.title, "status": doc.status, "message": "Processing started"}

@router.get("/")
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.owner_id == current_user.id).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id, "title": d.title, "filename": d.filename,
            "status": d.status, "page_count": d.page_count,
            "department": d.department, "version": d.version,
            "tags": d.tags, "file_size": d.file_size,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]

@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
    return {
        "id": doc.id, "title": doc.title, "filename": doc.filename,
        "status": doc.status, "page_count": doc.page_count,
        "chunk_count": chunk_count, "department": doc.department,
        "version": doc.version, "tags": doc.tags,
    }

@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.owner_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}

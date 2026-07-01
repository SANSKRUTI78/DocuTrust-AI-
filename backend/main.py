import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, documents, chat, analytics, users
from app.core.database import engine, Base
from app.models import models

Base.metadata.create_all(bind=engine)
# Create tables
Base.metadata.create_all(bind=engine)

# Create upload directories
os.makedirs(os.path.join(settings.UPLOAD_DIR, "pdfs"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "indexes"), exist_ok=True)

app = FastAPI(
    title="DocuTrust AI",
    description="Enterprise Knowledge Intelligence Platform with Multi-Agent RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(users.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "DocuTrust AI Backend Running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

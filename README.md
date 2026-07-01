# 🛡️ DocuTrust AI
### Enterprise Knowledge Intelligence Platform with Multi-Agent RAG

A full-stack AI-powered document Q&A platform with Trust Scoring, Citations, Hybrid Search, and Real-time Agent Monitoring.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite + Tailwind CSS + Recharts + Framer Motion |
| **Backend** | FastAPI + Python 3.11 |
| **AI Framework** | LangGraph-inspired Multi-Agent Pipeline |
| **LLM** | OpenAI GPT-4o-mini (configurable) |
| **Embeddings** | sentence-transformers/all-mpnet-base-v2 |
| **Vector DB** | FAISS (local, no cloud needed) |
| **Search** | Hybrid BM25 + Dense Vector |
| **Database** | MySQL 8 via SQLAlchemy |
| **Auth** | JWT (access + refresh tokens) |
| **PDF Parsing** | PyMuPDF + pdfplumber |

---

## 🚀 Quick Start (Manual Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- An OpenAI API key (or other LLM)

### Step 1: MySQL Database
```sql
CREATE DATABASE docutrust_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Backend
```bash
cd backend
cp .env.example .env
# Edit .env - set DATABASE_URL and OPENAI_API_KEY

python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Step 3: Frontend
```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:5173
```

### Step 4: Open App
- Go to http://localhost:5173
- Register an account (first user becomes Admin)
- Upload PDF documents
- Start asking questions!

---

## ⚙️ Configuration (`backend/.env`)

```env
# MySQL
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/docutrust_ai

# JWT
SECRET_KEY=your-super-secret-key-change-this

# LLM (pick one)
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
```

---

## 🤖 How the AI Works

```
User Question
     ↓
Query Understanding Agent  →  Parses intent
     ↓
Retriever Agent            →  Hybrid BM25 + FAISS vector search
     ↓
Cross Encoder Agent        →  Re-ranks results by relevance
     ↓
Citation Agent             →  Builds page/section references
     ↓
Response Generator         →  LLM answers using retrieved context
     ↓
Trust Score Calculator     →  Confidence = similarity + keyword + coverage
     ↓
Formatted Output with Citations
```

---

## ✨ Key Features

- **Trust Score** — Every answer rated 0-100% with breakdown
- **Hybrid Search** — BM25 + Dense Vector for better recall
- **Multi-Document** — Query across all your uploaded PDFs simultaneously
- **Real-time Agent Log** — See each AI agent working live
- **Source Citations** — Click to see the exact passage used
- **Conversation Memory** — Remembers previous questions in a chat
- **Feedback Loop** — 👍 / 👎 collected for quality monitoring
- **Analytics Dashboard** — Trust distribution, department breakdown, satisfaction

---

## 🐳 Docker Deployment

```bash
# Edit backend/.env first
docker-compose up --build
```

---

## 📁 Project Structure

```
docutrust-ai/
├── backend/
│   ├── app/
│   │   ├── agents/        # RAG pipeline agents
│   │   ├── api/           # FastAPI routes (auth, docs, chat, analytics)
│   │   ├── core/          # Config, database, security
│   │   ├── models/        # SQLAlchemy MySQL models
│   │   └── services/      # PDF parsing, embeddings, search
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/         # Dashboard, Workspace, Upload, Analytics
│       ├── components/    # Layout, UI components
│       ├── store/         # Zustand auth store
│       └── utils/         # Axios API client
├── docker-compose.yml
├── setup.sh              # Linux/Mac setup
└── setup.bat             # Windows setup
```

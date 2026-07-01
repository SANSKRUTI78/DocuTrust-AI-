#!/bin/bash
set -e

echo "========================================"
echo " DocuTrust AI - Linux/Mac Setup"
echo "========================================"

command -v python3 >/dev/null 2>&1 || { echo "Python 3.10+ required. Install it first."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 18+ required. Install it first."; exit 1; }
command -v mysql >/dev/null 2>&1 || echo "⚠ MySQL not found in PATH - make sure MySQL 8 is installed"

echo "[1/4] Setting up Backend..."
cd backend
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

echo "[2/4] Setting up Frontend..."
cd frontend
npm install
cd ..

echo "[3/4] Creating MySQL database..."
echo "Run this SQL in MySQL:"
echo "  CREATE DATABASE docutrust_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo ""
echo "========================================"
echo " Setup Complete!"
echo ""
echo " NEXT STEPS:"
echo " 1. Edit backend/.env with your MySQL password and OpenAI key"
echo " 2. Create the MySQL DB if not done yet"
echo " 3. Start backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"  
echo " 4. Start frontend: cd frontend && npm run dev"
echo " 5. Open: http://localhost:5173"
echo "========================================"

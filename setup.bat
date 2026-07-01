@echo off
echo ========================================
echo  DocuTrust AI - Windows Setup
echo ========================================

echo [1/5] Checking Python...
python --version || (echo Python 3.10+ required. Download: https://python.org && pause && exit)

echo [2/5] Checking Node.js...
node --version || (echo Node.js 18+ required. Download: https://nodejs.org && pause && exit)

echo [3/5] Setting up Backend...
cd backend
copy .env.example .env
echo.
echo *** IMPORTANT: Edit backend\.env and set your DATABASE_URL and LLM API key ***
echo.
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
cd ..

echo [4/5] Setting up Frontend...
cd frontend
npm install
cd ..

echo [5/5] Creating MySQL database...
echo Run this in MySQL: CREATE DATABASE docutrust_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

echo.
echo ========================================
echo  Setup Complete!
echo  
echo  NEXT STEPS:
echo  1. Edit backend\.env with your MySQL password and OpenAI key
echo  2. Start backend:  cd backend && venv\Scripts\activate && uvicorn main:app --reload
echo  3. Start frontend: cd frontend && npm run dev
echo  4. Open: http://localhost:5173
echo ========================================
pause

@echo off
REM One-click local start for Windows: sets up and launches backend + frontend in two windows.

cd /d %~dp0backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
if not exist .env copy .env.example .env >nul
call venv\Scripts\activate
pip install -r requirements.txt
start "LinkSense API" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python run.py"

cd /d %~dp0frontend
if not exist node_modules call npm install
start "LinkSense UI" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173  (demo login: demo@linksense.dev / Demo@1234)

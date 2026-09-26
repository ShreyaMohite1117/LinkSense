#!/usr/bin/env bash
# Local start for macOS / Linux. Ctrl+C stops both servers.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT/backend"
[ -d venv ] || python3 -m venv venv
[ -f .env ] || cp .env.example .env
source venv/bin/activate
pip install -q -r requirements.txt
python run.py &
API_PID=$!

cd "$ROOT/frontend"
[ -d node_modules ] || npm install
trap "kill $API_PID" EXIT
npm run dev

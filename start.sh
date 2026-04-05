#!/bin/bash

# Start the Basketball Predictor locally
# Usage: ./start.sh  (or double-click it in Finder)

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  Basketball Predictor"
echo "  ─────────────────────────────────"
echo "  Backend  →  http://localhost:8000"
echo "  Frontend →  http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

# Install Python deps if needed
pip install -r "$ROOT/requirements.txt" -q

# Install frontend deps if node_modules is missing
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install --prefix "$ROOT/frontend"
fi

# Start backend in background
cd "$ROOT/backend"
uvicorn app.main:app --reload &
BACKEND_PID=$!

# Start frontend in background
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Open browser after a short delay
sleep 3
open http://localhost:5173

# Wait — Ctrl+C kills both
wait $BACKEND_PID $FRONTEND_PID

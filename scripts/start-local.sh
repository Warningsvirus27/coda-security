#!/bin/bash
set -e

echo "========================================"
echo " Starting SecureCoda Development Services"
echo "========================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/3] Running migrations..."
python backend/manage.py migrate

echo "[2/3] Launching backend Daphne/Django server..."
(cd backend && python manage.py runserver 0.0.0.0:8000) &
BACKEND_PID=$!

echo "[3/3] Launching frontend React dev server..."
(cd frontend && npm start) &
FRONTEND_PID=$!

echo "Services started (Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID)"
wait

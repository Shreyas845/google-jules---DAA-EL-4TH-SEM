#!/bin/bash
# Start FastAPI backend
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

# Start React frontend
cd frontend
PORT=3000 npm start &
FRONTEND_PID=$!

echo "Dashboard running."
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:3000"
echo "To stop, kill $BACKEND_PID and $FRONTEND_PID"

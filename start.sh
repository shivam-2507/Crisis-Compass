#!/bin/bash

echo "Starting Crisis-Compass..."
echo

echo "Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 3

echo "Starting frontend server..."
cd ..
npm run dev &
FRONTEND_PID=$!

echo
echo "Crisis-Compass is starting up!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:5173"
echo
echo "Press Ctrl+C to stop both servers"

# Function to cleanup processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait

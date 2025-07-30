#!/bin/bash

# Clean Python cache files
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Start the backend
echo "Starting backend server..."
cd backend
python -m venv venv
source venv/bin/activate  # Use 'venv\Scripts\activate' on Windows
pip install -r requirements.txt
# Create necessary directories
mkdir -p temp pdfs text_files
python api/application.py &
BACKEND_PID=$!

# Start the frontend
echo "Starting frontend server..."
cd ../frontend
# Use Python's built-in HTTP server
python3 -m http.server --directory . 8080 &
FRONTEND_PID=$!

echo "Servers started!"
echo "Frontend: http://localhost:8080"
echo "Backend: http://localhost:5000"
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 
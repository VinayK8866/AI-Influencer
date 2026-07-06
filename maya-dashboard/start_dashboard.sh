#!/bin/bash
echo "===================================================="
echo "🚀 STARTING MAYA ROSSI'S ULTIMATE INFLUENCER COMMAND ROOM"
echo "===================================================="

# Flask Python API starting on port 5328
echo "📡 Starting Python API backend on port 5328..."
python3 api/index.py &
PYTHON_PID=$!

# Next.js frontend starting on port 3000
echo "🎨 Starting Next.js frontend on port 3000..."
npm run dev &
NEXT_PID=$!

# Handle exit cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $PYTHON_PID 2>/dev/null
    kill $NEXT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait

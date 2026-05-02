#!/bin/bash
# Quick fix script for database initialization issue

echo "=========================================="
echo "NFC Campus Wallet - Server Fix Script"
echo "=========================================="

# Stop existing processes
echo ""
echo "🛑 Stopping existing processes..."
pkill -f "uvicorn.*app.main:app" || echo "No uvicorn process found"
pkill -f "python.*start_server.py" || echo "No start_server process found"
sleep 2

# Pull latest code
echo ""
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Start server
echo ""
echo "🚀 Starting server..."
python start_server.py


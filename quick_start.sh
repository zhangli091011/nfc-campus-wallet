#!/bin/bash

# NFC Campus Event System - Quick Start Script
# This script automates the setup process for development

set -e  # Exit on error

echo "=========================================="
echo "NFC Campus Event System - Quick Start"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python 3.9 or higher is required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}ℹ️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your database credentials${NC}"
    echo -e "${YELLOW}   Then run this script again${NC}"
    exit 0
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Check MySQL connection
echo ""
echo "🔍 Checking database connection..."
python3 -c "
from core.config import load_settings, get_settings
try:
    load_settings()
    settings = get_settings()
    print('✅ Configuration loaded')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
" || exit 1

# Run database migration
echo ""
echo "🗄️  Running database migration..."
python3 scripts/migrate_cash_reconciliation.py
echo -e "${GREEN}✅ Database migration completed${NC}"

# Ask if user wants to create admin
echo ""
read -p "Do you want to create an admin user? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 scripts/create_admin.py
fi

# Ask if user wants to setup demo data
echo ""
read -p "Do you want to setup demo data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🎬 Setting up demo data..."
    python3 scripts/demo_setup.py
    echo -e "${GREEN}✅ Demo data created${NC}"
fi

# Final instructions
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "🚀 To start the server, run:"
echo "   source .venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📚 Documentation:"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Deployment Guide: DEPLOYMENT_GUIDE.md"
echo "   - Demo Flow: DEMO_FLOW.md"
echo ""
echo "🎉 Happy coding!"
echo ""

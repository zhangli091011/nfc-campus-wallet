#!/usr/bin/env python3
"""
Production server startup script.

Ensures proper initialization before starting the server.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.config import load_settings, get_settings
from core.database import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize and start the server."""
    print("=" * 60)
    print("NFC Campus Wallet - Server Startup")
    print("=" * 60)
    
    # Load configuration
    print("\n⚙️  Loading configuration...")
    try:
        load_settings()
        settings = get_settings()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize database
    print("\n📦 Initializing database...")
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    
    # Start server
    print(f"\n🚀 Starting server on {settings.server_host}:{settings.server_port}...")
    print("=" * 60)
    
    import uvicorn
    
    # Import app after initialization
    from app.main import app
    
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to run Yo Store without Telegram bot
"""

import uvicorn
from api import app
from database import init_database

def main():
    print("🛍️  Starting Yo Store (API only)...")
    print("=" * 50)
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    print("\n🚀 Yo Store API is running!")
    print("=" * 50)
    print("📱 API Server: http://localhost:8000")
    print("🛍️  Web App: http://localhost:8000/webapp")
    print("📊 Health Check: http://localhost:8000/health")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("\nPress Ctrl+C to stop the application")
    
    # Run the API server
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

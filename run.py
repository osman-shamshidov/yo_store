#!/usr/bin/env python3
"""
Quick start script for Electronics Store Mini App
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import telegram
        import sqlalchemy
        import schedule
        print("✅ All requirements are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing requirement: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("Creating .env file from template...")
        
        env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook

# Database Configuration
DATABASE_URL=sqlite:///./yo_store.db

# App Configuration
SECRET_KEY=your-secret-key-change-this
DEBUG=True
HOST=0.0.0.0
PORT=8000
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your Telegram bot token")
        return False
    else:
        print("✅ .env file found")
        return True

def main():
    """Main function"""
    print("🛍️  Yo Store Mini App - Quick Start")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check .env file
    env_ok = check_env_file()
    
    if not env_ok:
        print("\n⚠️  Please configure your .env file before running the app")
        print("1. Get a bot token from @BotFather in Telegram")
        print("2. Add the token to TELEGRAM_BOT_TOKEN in .env file")
        print("3. Run this script again")
        sys.exit(1)
    
    print("\n🚀 Starting Yo Store Mini App...")
    print("=" * 50)
    
    # Import and run the main application
    try:
        from main import main as run_app
        run_app()
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


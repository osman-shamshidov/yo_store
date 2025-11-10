#!/usr/bin/env python3
"""
Yo Store Telegram Mini App
Main application entry point with quick start features
"""

import asyncio
import threading
import signal
import sys
import os
import time
from config import Config
from database import init_database
from init_db_for_production import create_full_product_catalog
from init_promo_codes import init_promo_codes
# from telegram_bot import ElectronicsStoreBot  # Отключено для тестирования
import uvicorn
from api import app

def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import telegram
        import sqlalchemy
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
DATABASE_URL=sqlite:///./electronics_store.db

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

class ElectronicsStoreApp:
    def __init__(self):
        self.bot = None
        self.api_server = None
        self.running = False
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_api_server(self):
        """Start the FastAPI server"""
        port = int(os.environ.get('PORT', Config.PORT))
        host = os.environ.get('HOST', Config.HOST)
        print(f"Starting API server on {host}:{port}")
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info"
        )
        self.api_server = uvicorn.Server(config)
        
        # Run in a separate thread
        api_thread = threading.Thread(target=self.api_server.run, daemon=True)
        api_thread.start()
        
        return api_thread
    
    def start_telegram_bot(self):
        """Start the Telegram bot"""
        if not Config.TELEGRAM_BOT_TOKEN:
            print("⚠️  TELEGRAM_BOT_TOKEN not set, skipping Telegram bot")
            return None
        
        # print("Starting Telegram bot...")
        # self.bot = ElectronicsStoreBot()
        # 
        # # Run bot in a separate thread
        # bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        # bot_thread.start()
        print("Telegram bot отключен для тестирования")
        
        return None
    
    def run(self):
        """Run the application"""
        print("🛍️  Starting Yo Store Mini App...")
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Initialize database
        print("Initializing database...")
        init_database()
        
        # Create full product catalog for production
        print("Creating full product catalog...")
        create_full_product_catalog()
        
        # Initialize promo codes
        print("Initializing promo codes...")
        init_promo_codes()
        
        # Start components
        api_thread = self.start_api_server()
        bot_thread = self.start_telegram_bot()
        
        self.running = True
        
        print("\n" + "="*50)
        print("🚀 Yo Store Mini App is running!")
        print("="*50)
        print(f"📱 API Server: http://{Config.HOST}:{Config.PORT}")
        print(f"🛍️  Web App: http://{Config.HOST}:{Config.PORT}/webapp")
        print(f"📊 Health Check: http://{Config.HOST}:{Config.PORT}/health")
        print(f"🤖 Telegram Bot: {'Running' if bot_thread else 'Not configured'}")
        print(f"💰 Price Management: Manual via Excel API only")
        print("="*50)
        print("\nPress Ctrl+C to stop the application")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        if not self.running:
            return
        
        print("\n🛑 Shutting down application...")
        self.running = False
        
        # Stop API server
        if self.api_server:
            self.api_server.should_exit = True
            print("✅ API server stopped")
        
        print("✅ Application shutdown complete")

def main():
    """Main function with quick start checks"""
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
    
    # Create and run the application
    try:
        app = ElectronicsStoreApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


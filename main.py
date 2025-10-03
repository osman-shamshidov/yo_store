#!/usr/bin/env python3
"""
Electronics Store Telegram Mini App
Main application entry point
"""

import asyncio
import threading
import signal
import sys
import os
from config import Config
from database import init_database
# from price_updater import price_updater  # Удалено автоматическое обновление цен
from telegram_bot import ElectronicsStoreBot
import uvicorn
from api import app

class ElectronicsStoreApp:
    def __init__(self):
        self.bot = None
        self.api_server = None
        # self.price_updater = price_updater  # Удалено автоматическое обновление цен
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
        
        print("Starting Telegram bot...")
        self.bot = ElectronicsStoreBot()
        
        # Run bot in a separate thread
        bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        bot_thread.start()
        
        return bot_thread
    
    # def start_price_updater(self):
    #     """Start the price updater"""
    #     print("Starting price updater...")
    #     self.price_updater.start_scheduler()
    # Удалено автоматическое обновление цен - теперь только через Excel API
    
    def run(self):
        """Run the application"""
        print("🛍️  Starting Yo Store Mini App...")
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Initialize database
        print("Initializing database...")
        init_database()
        
        # Start components
        api_thread = self.start_api_server()
        bot_thread = self.start_telegram_bot()
        # self.start_price_updater()  # Удалено автоматическое обновление цен
        
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
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the application gracefully"""
        if not self.running:
            return
        
        print("\n🛑 Shutting down application...")
        self.running = False
        
        # Price updater removed - no automatic updates
        # print("✅ Price updater stopped")
        
        # Stop API server
        if self.api_server:
            self.api_server.should_exit = True
            print("✅ API server stopped")
        
        print("✅ Application shutdown complete")

def main():
    """Main entry point"""
    app = ElectronicsStoreApp()
    app.run()

if __name__ == "__main__":
    main()


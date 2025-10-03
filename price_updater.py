import random
import schedule
import time
import threading
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, CurrentPrice, PriceHistory
import json

class PriceUpdater:
    def __init__(self):
        self.is_running = False
        self.thread = None
    
    def update_prices(self):
        """Update prices for all products"""
        db = SessionLocal()
        try:
            products = db.query(Product).filter(Product.is_available == True).all()
            
            for product in products:
                # Get current price
                current_price = db.query(CurrentPrice).filter(
                    CurrentPrice.product_id == product.id
                ).first()
                
                if current_price:
                    old_price = current_price.price
                    
                    # Simulate price change (random between -5% and +5%)
                    change_percentage = random.uniform(-0.05, 0.05)
                    new_price = old_price * (1 + change_percentage)
                    
                    # Ensure price doesn't go below 1000 rubles
                    new_price = max(new_price, 1000.0)
                    
                    # Update current price
                    current_price.old_price = old_price
                    current_price.price = new_price
                    current_price.last_updated = datetime.utcnow()
                    
                    # Calculate discount percentage
                    if old_price > new_price:
                        current_price.discount_percentage = ((old_price - new_price) / old_price) * 100
                    else:
                        current_price.discount_percentage = 0.0
                    
                    # Add to price history
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=new_price,
                        old_price=old_price,
                        updated_at=datetime.utcnow()
                    )
                    db.add(price_history)
                    
                    print(f"Updated price for {product.name}: {old_price:.2f} -> {new_price:.2f} RUB")
            
            db.commit()
            print(f"Price update completed at {datetime.utcnow()}")
            
        except Exception as e:
            print(f"Error updating prices: {e}")
            db.rollback()
        finally:
            db.close()
    
    def load_prices_from_file(self, file_path):
        """Load prices from external file (JSON format)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                price_data = json.load(f)
            
            db = SessionLocal()
            try:
                for item in price_data:
                    product_id = item.get('product_id')
                    new_price = item.get('price')
                    
                    if product_id and new_price:
                        current_price = db.query(CurrentPrice).filter(
                            CurrentPrice.product_id == product_id
                        ).first()
                        
                        if current_price:
                            old_price = current_price.price
                            current_price.old_price = old_price
                            current_price.price = new_price
                            current_price.last_updated = datetime.utcnow()
                            
                            # Calculate discount
                            if old_price > new_price:
                                current_price.discount_percentage = ((old_price - new_price) / old_price) * 100
                            else:
                                current_price.discount_percentage = 0.0
                            
                            # Add to history
                            price_history = PriceHistory(
                                product_id=product_id,
                                price=new_price,
                                old_price=old_price,
                                updated_at=datetime.utcnow()
                            )
                            db.add(price_history)
                
                db.commit()
                print(f"Prices loaded from file: {file_path}")
                
            except Exception as e:
                print(f"Error loading prices from file: {e}")
                db.rollback()
            finally:
                db.close()
                
        except FileNotFoundError:
            print(f"Price file not found: {file_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in price file: {file_path}")
    
    def start_scheduler(self):
        """Start the price update scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Schedule price updates every 10 minutes
        schedule.every(10).minutes.do(self.update_prices)
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        print("Price updater started - updates every 10 minutes")
    
    def stop_scheduler(self):
        """Stop the price update scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        schedule.clear()
        print("Price updater stopped")

# Global price updater instance
price_updater = PriceUpdater()


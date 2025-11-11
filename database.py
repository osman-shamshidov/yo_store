from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import Config

# Create database engine
engine = create_engine(Config.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with sample data"""
    create_tables()
    
    from sqlalchemy.orm import Session
    from models import Category, Product
    from price_storage import set_price
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        # Check if categories already exist
        if db.query(Category).count() == 0:
            # Create categories
            categories_data = [
                {"name": "Смартфоны", "description": "Мобильные телефоны", "icon": "📱"},
                {"name": "Ноутбуки", "description": "Портативные компьютеры", "icon": "💻"},
                {"name": "Игровые приставки", "description": "Игровые консоли", "icon": "🎮"},
                {"name": "Наушники", "description": "Аудио устройства", "icon": "🎧"},
                {"name": "Планшеты", "description": "Планшетные компьютеры", "icon": "📱"},
                {"name": "Умные колонки", "description": "Голосовые помощники", "icon": "🔊"},
            ]
            
            for cat_data in categories_data:
                category = Category(**cat_data)
                db.add(category)
            
            db.commit()
            
            # Create sample products
            sample_products = [
                {
                    "sku": "APPIP15PRO",
                    "name": "iPhone 15 Pro",
                    "brand": "Apple",
                    "level_0": "Смартфоны",
                    "level_1": "iPhone",
                    "level_2": "iPhone 15 Pro",
                    "specifications": '{"storage": "256GB", "color": "Natural Titanium", "screen": "6.1 inch"}',
                    "price": 99990.0
                },
                {
                    "sku": "APPMBAIRM2",
                    "name": "MacBook Air M2",
                    "brand": "Apple",
                    "level_0": "Ноутбуки",
                    "level_1": "MacBook",
                    "level_2": "MacBook Air M2",
                    "specifications": '{"storage": "256GB", "memory": "8GB", "screen": "13.6 inch"}',
                    "price": 119990.0
                },
                {
                    "sku": "SONYPS5",
                    "name": "PlayStation 5",
                    "brand": "Sony",
                    "level_0": "Игровые приставки",
                    "level_1": "PlayStation",
                    "level_2": "PS5",
                    "specifications": '{"storage": "825GB", "controller": "DualSense"}',
                    "price": 59990.0
                },
                {
                    "sku": "APPAPRO2",
                    "name": "AirPods Pro 2",
                    "brand": "Apple",
                    "level_0": "Наушники",
                    "level_1": "AirPods",
                    "level_2": "AirPods Pro 2",
                    "specifications": '{"battery": "6 hours", "case": "MagSafe"}',
                    "price": 24990.0
                },
                {
                    "sku": "APPIPADAIR",
                    "name": "iPad Air",
                    "brand": "Apple",
                    "level_0": "Планшеты",
                    "level_1": "iPad",
                    "level_2": "iPad Air",
                    "specifications": '{"storage": "64GB", "screen": "10.9 inch"}',
                    "price": 59990.0
                },
                {
                    "sku": "APPHPMINI",
                    "name": "HomePod mini",
                    "brand": "Apple",
                    "level_0": "Умные колонки",
                    "level_1": "HomePod",
                    "level_2": "HomePod mini",
                    "specifications": '{"color": "Space Gray", "power": "20W"}',
                    "price": 9990.0
                }
            ]
            
            for prod_data in sample_products:
                price = prod_data.pop('price')
                product = Product(**prod_data)
                db.add(product)
                db.flush()  # Get the product ID
                
                # Create current price in JSON file
                old_price = price * 1.1  # 10% higher old price
                # discount_percentage вычисляется автоматически из old_price и price
                set_price(
                    sku=product.sku,
                    price=price,
                    old_price=old_price,
                    currency="RUB",
                    is_parse=True
                )
            
            db.commit()
            print("Yo Store database initialized with sample data")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


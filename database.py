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
    from models import Category, Product, CurrentPrice
    
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
                    "name": "iPhone 15 Pro",
                    "description": "Новейший смартфон от Apple с титановым корпусом",
                    "brand": "Apple",
                    "model": "iPhone 15 Pro",
                    "category_id": 1,
                    "image_url": "https://example.com/iphone15pro.jpg",
                    "specifications": '{"storage": "256GB", "color": "Natural Titanium", "screen": "6.1 inch"}',
                    "price": 99990.0
                },
                {
                    "name": "MacBook Air M2",
                    "description": "Ультратонкий ноутбук с чипом M2",
                    "brand": "Apple",
                    "model": "MacBook Air M2",
                    "category_id": 2,
                    "image_url": "https://example.com/macbookair.jpg",
                    "specifications": '{"storage": "256GB", "memory": "8GB", "screen": "13.6 inch"}',
                    "price": 119990.0
                },
                {
                    "name": "PlayStation 5",
                    "description": "Игровая консоль нового поколения",
                    "brand": "Sony",
                    "model": "PS5",
                    "category_id": 3,
                    "image_url": "https://example.com/ps5.jpg",
                    "specifications": '{"storage": "825GB", "controller": "DualSense"}',
                    "price": 59990.0
                },
                {
                    "name": "AirPods Pro 2",
                    "description": "Беспроводные наушники с активным шумоподавлением",
                    "brand": "Apple",
                    "model": "AirPods Pro 2",
                    "category_id": 4,
                    "image_url": "https://example.com/airpods.jpg",
                    "specifications": '{"battery": "6 hours", "case": "MagSafe"}',
                    "price": 24990.0
                },
                {
                    "name": "iPad Air",
                    "description": "Планшет с чипом M1",
                    "brand": "Apple",
                    "model": "iPad Air",
                    "category_id": 5,
                    "image_url": "https://example.com/ipad.jpg",
                    "specifications": '{"storage": "64GB", "screen": "10.9 inch"}',
                    "price": 59990.0
                },
                {
                    "name": "HomePod mini",
                    "description": "Умная колонка с Siri",
                    "brand": "Apple",
                    "model": "HomePod mini",
                    "category_id": 6,
                    "image_url": "https://example.com/homepod.jpg",
                    "specifications": '{"color": "Space Gray", "power": "20W"}',
                    "price": 9990.0
                }
            ]
            
            for prod_data in sample_products:
                price = prod_data.pop('price')
                product = Product(**prod_data)
                db.add(product)
                db.flush()  # Get the product ID
                
                # Create current price
                current_price = CurrentPrice(
                    product_id=product.id,
                    price=price,
                    old_price=price * 1.1,  # 10% higher old price
                    discount_percentage=10.0
                )
                db.add(current_price)
            
            db.commit()
            print("Yo Store database initialized with sample data")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


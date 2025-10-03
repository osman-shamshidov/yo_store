from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(Text)
    icon = Column(String(50))  # emoji or icon name
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    is_subcategory = Column(Boolean, default=False)
    
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id], backref="subcategories")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True)  # Уникальный SKU товара
    name = Column(String(200), index=True)
    description = Column(Text)
    brand = Column(String(100))
    model = Column(String(100))
    category_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(String(500))  # Основное изображение (для совместимости)
    images = Column(Text)  # JSON массив изображений
    specifications = Column(Text)  # JSON string
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    prices = relationship("PriceHistory", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    old_price = Column(Float)  # previous price for comparison
    currency = Column(String(3), default="RUB")
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="prices")

class CurrentPrice(Base):
    __tablename__ = "current_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    price = Column(Float)
    old_price = Column(Float)
    currency = Column(String(3), default="RUB")
    discount_percentage = Column(Float)  # calculated discount
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")

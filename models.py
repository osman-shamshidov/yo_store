#!/usr/bin/env python3
"""SQLAlchemy models for Yo Store app"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, index=True)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    description = Column(Text)
    # Иерархические уровни категорий
    level0 = Column(String(100), nullable=True, index=True)  # Основная категория (смартфоны)
    level1 = Column(String(100), nullable=True, index=True)  # Подкатегория (16 series)
    level2 = Column(String(100), nullable=True, index=True)  # Детальная категория (16 pro max)
    specifications = Column(Text)  # JSON string
    image_url = Column(String(500))  # Legacy field
    images = Column(Text)  # JSON array of image URLs
    stock = Column(Integer, default=0)  # Количество на складе
    is_available = Column(Boolean, default=True)  # Доступность товара
    # Legacy поле для совместимости
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="products")
    prices = relationship("CurrentPrice", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(10))
    parent_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    is_subcategory = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    old_price = Column(Float)  # previous price for comparison
    currency = Column(String(3), default="RUB")
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")

class CurrentPrice(Base):
    __tablename__ = "current_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    price = Column(Float)
    old_price = Column(Float)
    currency = Column(String(3), default="RUB")
    discount_percentage = Column(Float)  # calculated discount
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", overlaps="prices")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    variant_name = Column(String(100))  # Например: "128GB Black Single SIM"
    memory_quantity = Column(String(50))  # Например: "128GB", "256GB", "512GB", "1TB"
    color = Column(String(50))  # Например: "Black", "White", "Blue", "Red"
    sim_type = Column(String(50))  # Например: "Single SIM", "Dual SIM", "eSIM"
    price_modifier = Column(Float, default=0.0)  # Дополнительная стоимость варианта
    sku_suffix = Column(String(50))  # Суффикс для полного SKU
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)  # Количество на складе
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="variants")

class ModelColorScheme(Base):
    __tablename__ = "model_color_schemes"
    
    id = Column(Integer, primary_key=True, index=True)
    model_key = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=False)
    colors_json = Column(Text, nullable=False)
    default_color = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelVariantScheme(Base):
    __tablename__ = "model_variant_schemes"
    
    id = Column(Integer, primary_key=True, index=True)
    model_key = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=False)
    variants_json = Column(Text, nullable=False)  # JSON с доступными вариантами товара
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelImageInfo(Base):
    __tablename__ = "model_image_info"
    
    id = Column(Integer, primary_key=True, index=True)
    model_key = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=False)
    folder_name = Column(String(200), nullable=False)  # Название папки изображений
    image_count_per_color = Column(Integer, default=4)  # Количество изображений для каждого цвета
    images_info_json = Column(Text)  # JSON с информацией об изображениях для каждого цвета
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
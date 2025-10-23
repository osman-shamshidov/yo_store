#!/usr/bin/env python3
"""SQLAlchemy models for Yo Store app - Refactored Architecture"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    """
    Товары с уникальным SKU (только конкретные конфигурации)
    Общие карточки получаются через GROUP BY level_2
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)  # Уникальный SKU
    name = Column(String(200), nullable=False)
    brand = Column(String(100), nullable=False)
    
    # Иерархия категорий
    level_0 = Column(String(100), nullable=False, index=True)  # Смартфоны, Ноутбуки
    level_1 = Column(String(100))  # 16 Series, MacBook
    level_2 = Column(String(100), index=True)  # iPhone 16, iPhone 16 Pro, Air M2
    
    # Дополнительно
    specifications = Column(Text)  # JSON с характеристиками (color, disk, sim_config и др.)
    stock = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    @property
    def color(self):
        """Извлечь цвет из specifications"""
        if self.specifications:
            try:
                specs = json.loads(self.specifications) if isinstance(self.specifications, str) else self.specifications
                return specs.get('color', '')
            except (json.JSONDecodeError, TypeError):
                return ''
        return ''
    
    @property
    def disk(self):
        """Извлечь объем памяти из specifications"""
        if self.specifications:
            try:
                specs = json.loads(self.specifications) if isinstance(self.specifications, str) else self.specifications
                return specs.get('disk', '')
            except (json.JSONDecodeError, TypeError):
                return ''
        return ''
    
    @property
    def sim_config(self):
        """Извлечь конфигурацию SIM из specifications"""
        if self.specifications:
            try:
                specs = json.loads(self.specifications) if isinstance(self.specifications, str) else self.specifications
                return specs.get('sim_config', '')
            except (json.JSONDecodeError, TypeError):
                return ''
        return ''
    
    @property
    def memory(self):
        """Алиас для disk (для обратной совместимости)"""
        return self.disk

    
    # Связь с ценой
    price = relationship("CurrentPrice", back_populates="product", uselist=False, cascade="all, delete-orphan")

class ProductImage(Base):
    """
    Изображения товаров (связь по level_2 + color)
    Один набор изображений для всех вариантов одного цвета одной модели
    """
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    level_2 = Column(String(100), nullable=False, index=True)  # iPhone 16, iPhone 16 Pro
    color = Column(String(50), nullable=False, index=True)     # Black, Teal, Titanium Desert
    img_list = Column(Text, nullable=False)  # JSON массив изображений
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Уникальный составной индекс
    __table_args__ = (
        UniqueConstraint('level_2', 'color', name='uix_level2_color'),
    )

class Category(Base):
    """
    Иерархия категорий
    Описывает структуру level_0 → level_1 → level_2
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    level_0 = Column(String(100), nullable=False, index=True)
    level_1 = Column(String(100))
    level_2 = Column(String(100))
    description = Column(Text)
    icon = Column(String(50))

class SkuVariant(Base):
    """
    Определяет какие поля используются для создания вариантов для каждой категории
    Например: Смартфоны используют ["color", "disk", "sim_config"]
              Ноутбуки используют ["color", "ram", "disk"]
    """
    __tablename__ = "sku_variant"
    
    id = Column(Integer, primary_key=True, index=True)
    level_0 = Column(String(100), unique=True, nullable=False)  # Категория верхнего уровня
    variant_fields = Column(Text, nullable=False)  # JSON массив полей
    created_at = Column(DateTime, default=datetime.utcnow)

class CurrentPrice(Base):
    """
    Текущие цены для товаров (привязка по SKU)
    """
    __tablename__ = "current_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), ForeignKey('products.sku', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    old_price = Column(Float)
    currency = Column(String(3), default="RUB")
    discount_percentage = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с продуктом
    product = relationship("Product", back_populates="price")

class Level2Description(Base):
    """
    Описания и характеристики для level_2 (моделей товаров)
    Один набор описаний для всех вариантов одной модели
    """
    __tablename__ = "level2_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    level_2 = Column(String(100), unique=True, nullable=False, index=True)  # iPhone 16, iPhone 16 Pro
    description = Column(Text, nullable=False)  # Основное описание товара
    details = Column(Text, nullable=False)  # JSON с характеристиками (процессор, память, экран и т.д.)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

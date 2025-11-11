#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с полными данными товаров для продакшена
"""

import os
import sys
import json

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, create_tables, SessionLocal
from models import Category, Product
from price_storage import set_price
from datetime import datetime

def create_full_product_catalog():
    """Создает полный каталог товаров"""
    
    # Создаем таблицы
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже данные
        if db.query(Product).count() > 0:
            print("Базa данных уже содержит товары")
            return
        
        # Создаем категории
        categories_data = [
            {"name": "Смартфоны", "description": "Мобильные телефоны", "icon": "📱"},
            {"name": "Ноутбуки", "description": "Портативные компьютеры", "icon": "💻"},
            {"name": "Наушники", "description": "Аудио устройства", "icon": "🎧"},
            {"name": "Планшеты", "description": "Планшетные компьютеры", "icon": "📱"},
            {"name": "Умные колонки", "description": "Голосовые помощники", "icon": "🔊"},
            {"name": "Другое", "description": "Прочее электронное оборудование", "icon": "⚙️"},
        ]
        
        categories = []
        for cat_data in categories_data:
            category = Category(**cat_data)
            db.add(category)
            categories.append(category)
        
        db.commit()
        
        # Получаем ID категорий
        smartphon_category_id = categories[0].id  # Смартфоны
        laptop_category_id = categories[1].id      # Ноутбуки
        headphones_category_id = categories[2].id # Наушники
        tablet_category_id = categories[3].id      # Планшеты
        speaker_category_id = categories[4].id     # Колонки
        other_category_id = categories[5].id      # Другое
        
        # Создаем товары с правильными характеристиками
        products_data = [
            # iPhone 16
            {
                "name": "iPhone 16",
                "description": "Новейший смартфон Apple с чипом A18",
                "brand": "Apple",
                "model": "iPhone 16",
                "category_id": smartphon_category_id,
                "level0": "Смартфоны Apple",
                "level1": "iPhone",
                "level2": "iPhone 16",
                "sku": "IPHONE16-001",
                "image_url": "/static/images/products/IPHONE16/black/0nezbz8sc7xr6vzyjmw7tjzx9al17n95.jpg",
                "images": json.dumps(["/static/images/products/IPHONE16/black/0nezbz8sc7xr6vzyjmw7tjzx9al17n95.jpg"]),
                "specifications": json.dumps({
                    "color": "Black",
                    "storage": "128GB",
                    "screen": "6.1 inch",
                    "camera": "48MP",
                    "connector": "USB-C"
                }),
                "is_available": True,
                "price": 89990.0
            },
            # iPhone 17 Pro Max
            {
                "name": "iPhone 17 Pro Max",
                "description": "Флагманский смартфон Apple с продвинутой камерой",
                "brand": "Apple",
                "model": "iPhone 17 Pro Max",
                "category_id": smartphon_category_id,
                "level0": "Смартфоны Apple",
                "level1": "iPhone",
                "level2": "iPhone 17 Pro Max",
                "sku": "IPHONE17ProMax-001",
                "image_url": "/static/images/products/IPHONE17ProMax/cosmic-orange/1v3gv6779mtz9d5vp32dzy1f5jh59yz1s.jpg",
                "images": json.dumps(["/static/images/products/IPHONE17ProMax/cosmic-orange/1v3gv6779mtz9d5vp32dzy1f5jh59yz1s.jpg"]),
                "specifications": json.dumps({
                    "color": "Cosmic Orange",
                    "storage": "256GB",
                    "screen": "6.9 inch",
                    "camera": "60MP Pro Max",
                    "processor": "A19 Pro"
                }),
                "is_available": True,
                "price": 129990.0
            },
            # MacBook Air M2
            {
                "name": "MacBook Air M2",
                "description": "Ультратонкий ноутбук с чипом M2",
                "brand": "Apple",
                "model": "MacBook Air M2",
                "category_id": laptop_category_id,
                "level0": "Ноутбуки Apple",
                "level1": "MacBook",
                "level2": "MacBook Air M2",
                "sku": "MACBOOKAIRM2-001",
                "image_url": "/static/images/products/MACBOOKAirM2/silver/1.jpg",
                "images": json.dumps(["/static/images/products/MACBOOKAirM2/silver/1.jpg"]),
                "specifications": json.dumps({
                    "color": "Silver",
                    "storage": "256GB SSD",
                    "screen": "13.6 inch Liquid Retina",
                    "processor": "Apple M2",
                    "memory": "8GB Unified Memory"
                }),
                "is_available": True,
                "price": 119990.0
            }
        ]
        
        for prod_data in products_data:
            price = prod_data.pop('price')
            product = Product(**prod_data)
            db.add(product)
            db.flush()  # Получаем ID товара
            
            # Создаем текущую цену в JSON файле
            old_price = price * 1.15  # Старая цена на 15% выше
            # discount_percentage вычисляется автоматически из old_price и price
            set_price(
                sku=product.sku,
                price=price,
                old_price=old_price,
                currency="RUB",
                is_parse=True
            )
        
        db.commit()
        print("✅ Успешно создан каталог товаров")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании каталога: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_full_product_catalog()

#!/usr/bin/env python3
"""
Скрипт для обновления описаний и изображений товаров
"""

from database import SessionLocal
from models import Product
import json

def update_product_descriptions():
    """Обновить описания и изображения товаров"""
    
    db = SessionLocal()
    
    # Данные для обновления товаров
    product_updates = [
        {
            "name": "iPhone 15 Pro",
            "description": """
            Новейший iPhone 15 Pro с титановым корпусом и чипом A17 Pro. 
            Оснащен профессиональной камерой с 5-кратным оптическим зумом,
            дисплеем Super Retina XDR и поддержкой USB-C.
            """,
            "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab",
            "images": [
                "https://images.unsplash.com/photo-1592750475338-74b7b21085ab",
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
                "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5",
                "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c"
            ],
            "specifications": {
                "display": "6.1 inch Super Retina XDR",
                "processor": "A17 Pro",
                "storage": "128GB/256GB/512GB/1TB",
                "camera": "48MP Main + 12MP Ultra Wide + 12MP Telephoto",
                "battery": "Up to 23 hours video playback",
                "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", "Black Titanium"]
            }
        },
        {
            "name": "MacBook Pro M3",
            "description": """
            Мощный ноутбук MacBook Pro M3 для профессионалов. 
            14-дюймовый дисплей Liquid Retina XDR, до 22 часов работы от батареи,
            чип M3 с 8-ядерным CPU и 10-ядерным GPU.
            """,
            "image_url": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef",
            "images": [
                "https://images.unsplash.com/photo-1541807084-5c52b6b3adef",
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
                "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853"
            ],
            "specifications": {
                "display": "14.2 inch Liquid Retina XDR",
                "processor": "Apple M3",
                "memory": "8GB/16GB/24GB unified memory",
                "storage": "512GB/1TB/2TB/4TB/8TB SSD",
                "graphics": "10-core GPU",
                "ports": ["3x Thunderbolt 4", "SDXC card slot", "HDMI", "MagSafe 3"]
            }
        },
        {
            "name": "PlayStation 5",
            "description": """
            Новейшая игровая консоль PlayStation 5 от Sony. 
            Мощный процессор AMD Zen 2, SSD накопитель для быстрой загрузки,
            поддержка 4K и ray tracing, DualSense контроллер с тактильной обратной связью.
            """,
            "image_url": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3",
            "images": [
                "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3",
                "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8",
                "https://images.unsplash.com/photo-1511512578047-dfb367046420",
                "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3"
            ],
            "specifications": {
                "cpu": "AMD Zen 2-based CPU",
                "gpu": "AMD RDNA 2-based GPU",
                "memory": "16GB GDDR6",
                "storage": "825GB SSD",
                "resolution": "4K at 120fps",
                "features": ["Ray tracing", "3D Audio", "DualSense controller"]
            }
        },
        {
            "name": "AirPods Pro 2",
            "description": """
            Беспроводные наушники AirPods Pro 2 с активным шумоподавлением. 
            Чип H2 для улучшенного звука, адаптивная прозрачность,
            до 6 часов работы с кейсом до 30 часов.
            """,
            "image_url": "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb",
            "specifications": {
                "chip": "Apple H2",
                "battery": "Up to 6 hours listening time",
                "case_battery": "Up to 30 hours total",
                "features": ["Active Noise Cancellation", "Adaptive Transparency", "Spatial Audio"],
                "water_resistance": "IPX4"
            }
        },
        {
            "name": "iPad Pro 12.9\" M2",
            "description": """
            Профессиональный планшет iPad Pro 12.9" с чипом M2. 
            Дисплей Liquid Retina XDR с технологией mini-LED,
            поддержка Apple Pencil 2 и Magic Keyboard.
            """,
            "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0",
            "specifications": {
                "display": "12.9 inch Liquid Retina XDR",
                "processor": "Apple M2",
                "storage": "128GB/256GB/512GB/1TB/2TB",
                "connectivity": ["Wi-Fi", "Wi-Fi + Cellular"],
                "accessories": ["Apple Pencil 2", "Magic Keyboard"],
                "cameras": ["12MP Wide", "10MP Ultra Wide", "LiDAR Scanner"]
            }
        }
    ]
    
    try:
        for update_data in product_updates:
            # Найти товар по названию
            product = db.query(Product).filter(Product.name == update_data["name"]).first()
            
            if product:
                # Обновить данные
                product.description = update_data["description"].strip()
                product.image_url = update_data["image_url"]
                product.specifications = json.dumps(update_data["specifications"], ensure_ascii=False)
                
                # Добавить множественные изображения
                if "images" in update_data:
                    product.images = json.dumps(update_data["images"], ensure_ascii=False)
                
                print(f"✅ Обновлен товар: {product.name}")
            else:
                print(f"❌ Товар не найден: {update_data['name']}")
        
        db.commit()
        print("🎉 Все товары успешно обновлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

def add_sample_images():
    """Добавить примеры изображений для товаров без фото"""
    
    db = SessionLocal()
    
    # Примеры изображений с Unsplash
    sample_images = {
        "Samsung Galaxy S24 Ultra": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
        "ASUS ROG Strix G15": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
        "Xbox Series X": "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3",
        "Sony WH-1000XM5": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        "Samsung Galaxy Tab S9 Ultra": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0",
        "Amazon Echo Dot 5": "https://images.unsplash.com/photo-1543512214-318c7553f230",
        "Apple HomePod mini": "https://images.unsplash.com/photo-1543512214-318c7553f230",
        "Samsung QLED 4K 55\"": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1",
        "LG OLED 4K 65\"": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1",
        "Apple Watch Series 9": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d",
        "Samsung Galaxy Watch 6 Classic": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d"
    }
    
    try:
        for product_name, image_url in sample_images.items():
            product = db.query(Product).filter(Product.name == product_name).first()
            
            if product and not product.image_url:
                product.image_url = image_url
                print(f"✅ Добавлено изображение для: {product.name}")
        
        db.commit()
        print("🎉 Изображения добавлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🛍️ Обновление товаров Yo Store")
    print("=" * 50)
    
    print("\n1. Обновление описаний и изображений...")
    update_product_descriptions()
    
    print("\n2. Добавление изображений для остальных товаров...")
    add_sample_images()
    
    print("\n✅ Готово! Товары обновлены.")

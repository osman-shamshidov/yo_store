#!/usr/bin/env python3
"""
Миграция для добавления поля SKU в таблицу products
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_sku():
    """Добавить поле SKU в таблицу products"""
    db_path = "electronics_store.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверим, есть ли уже поле sku
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sku' in columns:
            print("✅ Поле SKU уже существует")
            return True
        
        # Добавим поле sku
        print("🔄 Добавляем поле SKU...")
        cursor.execute("ALTER TABLE products ADD COLUMN sku VARCHAR(50)")
        
        # Создадим индекс для поля sku
        print("🔄 Создаем индекс для поля SKU...")
        cursor.execute("CREATE INDEX idx_products_sku ON products(sku)")
        
        # Обновим существующие товары с SKU
        print("🔄 Обновляем существующие товары с SKU...")
        
        # Получим все товары
        cursor.execute("SELECT id, name, brand FROM products")
        products = cursor.fetchall()
        
        for product_id, name, brand in products:
            # Создадим SKU на основе ID, бренда и названия
            sku = f"{brand.upper()[:3]}-{product_id:03d}-{name.replace(' ', '').upper()[:10]}" if brand else f"PROD-{product_id:03d}-{name.replace(' ', '').upper()[:10]}"
            
            cursor.execute("UPDATE products SET sku = ? WHERE id = ?", (sku, product_id))
            print(f"  ✅ Товар {product_id}: {name} -> SKU: {sku}")
        
        # Сделаем поле sku обязательным (NOT NULL)
        print("🔄 Делаем поле SKU обязательным...")
        
        # Создадим новую таблицу с полем sku NOT NULL
        cursor.execute("""
            CREATE TABLE products_new (
                id INTEGER PRIMARY KEY,
                sku VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(200),
                description TEXT,
                brand VARCHAR(100),
                model VARCHAR(100),
                category_id INTEGER,
                image_url VARCHAR(500),
                images TEXT,
                specifications TEXT,
                is_available BOOLEAN DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # Скопируем данные
        cursor.execute("""
            INSERT INTO products_new 
            SELECT id, sku, name, description, brand, model, category_id, 
                   image_url, images, specifications, is_available, created_at, updated_at
            FROM products
        """)
        
        # Удалим старую таблицу и переименуем новую
        cursor.execute("DROP TABLE products")
        cursor.execute("ALTER TABLE products_new RENAME TO products")
        
        # Создадим индексы
        cursor.execute("CREATE INDEX idx_products_name ON products(name)")
        cursor.execute("CREATE INDEX idx_products_sku ON products(sku)")
        
        conn.commit()
        print("✅ Миграция завершена успешно!")
        
        # Покажем результат
        cursor.execute("SELECT id, sku, name FROM products LIMIT 5")
        products = cursor.fetchall()
        print("\n📋 Примеры товаров с SKU:")
        for product_id, sku, name in products:
            print(f"  {product_id}: {sku} - {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Начинаем миграцию для добавления поля SKU...")
    success = migrate_add_sku()
    if success:
        print("✅ Миграция завершена успешно!")
    else:
        print("❌ Миграция завершилась с ошибкой!")

#!/usr/bin/env python3
"""
Миграция: добавление полей promo_code и discount_amount в таблицу orders
"""

import os
import sys
import sqlite3

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def migrate_add_promo_code_to_orders():
    """Добавить поля promo_code и discount_amount в таблицу orders"""
    
    # Получаем путь к базе данных
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    # Создаем резервную копию
    backup_path = f"{db_path}.backup_before_promo_migration_{os.path.getmtime(db_path)}"
    print(f"💾 Создание резервной копии: {backup_path}")
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Резервная копия создана")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существуют ли уже эти колонки
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'promo_code' in columns and 'discount_amount' in columns:
            print("✅ Колонки promo_code и discount_amount уже существуют")
            return
        
        print("🔄 Добавление колонок promo_code и discount_amount...")
        
        # Добавляем колонку promo_code
        if 'promo_code' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN promo_code VARCHAR(50)")
            print("  ✅ Добавлена колонка promo_code")
        
        # Добавляем колонку discount_amount
        if 'discount_amount' not in columns:
            cursor.execute("ALTER TABLE orders ADD COLUMN discount_amount FLOAT DEFAULT 0.0")
            print("  ✅ Добавлена колонка discount_amount")
        
        conn.commit()
        print("✅ Миграция успешно выполнена")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при выполнении миграции: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_promo_code_to_orders()


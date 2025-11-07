#!/usr/bin/env python3
"""
Миграция для добавления поля ram в таблицу order_items
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_ram():
    """Добавить поле ram в таблицу order_items"""
    db_path = "electronics_store.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверим, есть ли уже поле ram
        cursor.execute("PRAGMA table_info(order_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ram' in columns:
            print("✅ Поле ram уже существует в таблице order_items")
            return True
        
        # Добавим поле ram
        print("🔄 Добавляем поле ram в таблицу order_items...")
        cursor.execute("ALTER TABLE order_items ADD COLUMN ram VARCHAR(50)")
        
        conn.commit()
        print("✅ Поле ram успешно добавлено в таблицу order_items")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Запуск миграции для добавления поля ram в order_items...\n")
    success = migrate_add_ram()
    if success:
        print("\n✅ Миграция завершена успешно")
    else:
        print("\n❌ Миграция завершена с ошибками")


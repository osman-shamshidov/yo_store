#!/usr/bin/env python3
"""
Миграция: добавление поля final_total в таблицу orders
"""

import os
import sys
import sqlite3

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config

def migrate_add_final_total_to_orders():
    """Добавить поле final_total в таблицу orders"""
    
    # Получаем путь к базе данных
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    # Создаем резервную копию
    import shutil
    import time
    backup_path = f"{db_path}.backup_before_final_total_migration_{int(time.time())}"
    print(f"💾 Создание резервной копии: {backup_path}")
    
    shutil.copy2(db_path, backup_path)
    print(f"✅ Резервная копия создана")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже эта колонка
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'final_total' in columns:
            print("✅ Колонка final_total уже существует")
            return
        
        print("🔄 Добавление колонки final_total...")
        
        # Добавляем колонку final_total
        cursor.execute("ALTER TABLE orders ADD COLUMN final_total FLOAT NOT NULL DEFAULT 0.0")
        print("  ✅ Добавлена колонка final_total")
        
        # Обновляем существующие заказы: final_total = total - discount_amount
        print("🔄 Обновление существующих заказов...")
        cursor.execute("""
            UPDATE orders 
            SET final_total = CASE 
                WHEN discount_amount IS NULL THEN total
                ELSE MAX(0, total - discount_amount)
            END
        """)
        updated_count = cursor.rowcount
        print(f"  ✅ Обновлено {updated_count} заказов")
        
        conn.commit()
        print("✅ Миграция успешно выполнена")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при выполнении миграции: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_final_total_to_orders()


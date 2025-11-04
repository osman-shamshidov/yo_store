#!/usr/bin/env python3
"""
Скрипт для обновления названий SIM конфигураций в поле name таблицы products
Single SIM -> SIM
eSIM -> Dual eSIM
Dual SIM -> Dual SIM (остается как есть)
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config

# Создаем подключение к БД
DATABASE_URL = os.getenv('DATABASE_URL', Config.DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_sim_names():
    """
    Обновить названия SIM конфигураций в поле name таблицы products
    """
    db = SessionLocal()
    
    try:
        print("🔄 Начало обновления названий SIM конфигураций...")
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Создаем резервную копию перед изменениями
        backup_name = f"electronics_store.db.backup_before_sim_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Создание резервной копии: {backup_name}")
        
        # Для SQLite просто копируем файл
        if DATABASE_URL.startswith('sqlite'):
            import shutil
            db_path = DATABASE_URL.replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
        
        # Обновляем названия
        replacements = [
            ("Single SIM", "SIM"),
            ("eSIM", "Dual eSIM"),
            # Dual SIM остается как есть
        ]
        
        total_updated = 0
        
        for old_name, new_name in replacements:
            # Используем SQL для обновления
            # Заменяем в поле name, если оно содержит старое название
            query = text("""
                UPDATE products 
                SET name = REPLACE(name, :old_name, :new_name),
                    updated_at = :updated_at
                WHERE name LIKE :pattern
            """)
            
            # Подсчитываем количество записей для обновления
            count_query = text("""
                SELECT COUNT(*) FROM products 
                WHERE name LIKE :pattern
            """)
            
            pattern = f"%{old_name}%"
            count_result = db.execute(count_query, {"pattern": pattern})
            count = count_result.scalar()
            
            if count > 0:
                print(f"\n📝 Обновление: '{old_name}' -> '{new_name}'")
                print(f"   Найдено записей для обновления: {count}")
                
                result = db.execute(query, {
                    "old_name": old_name,
                    "new_name": new_name,
                    "pattern": pattern,
                    "updated_at": datetime.utcnow()
                })
                
                updated_count = result.rowcount
                total_updated += updated_count
                print(f"   ✅ Обновлено записей: {updated_count}")
                
                # Показываем примеры обновленных названий
                examples_query = text("""
                    SELECT id, name FROM products 
                    WHERE name LIKE :pattern AND name LIKE :new_pattern
                    LIMIT 5
                """)
                examples_result = db.execute(examples_query, {
                    "pattern": f"%{new_name}%",
                    "new_pattern": f"%{new_name}%"
                })
                examples = examples_result.fetchall()
                
                if examples:
                    print(f"   Примеры обновленных названий:")
                    for example_id, example_name in examples:
                        print(f"      - ID {example_id}: {example_name}")
            else:
                print(f"\n⚠️  '{old_name}' не найдено в названиях товаров")
        
        # Сохраняем изменения
        db.commit()
        
        print(f"\n📊 Итоги обновления:")
        print(f"   Всего обновлено записей: {total_updated}")
        print(f"✅ Обновление завершено успешно")
        
        return total_updated
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        update_sim_names()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


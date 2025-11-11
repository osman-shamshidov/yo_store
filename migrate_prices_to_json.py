#!/usr/bin/env python3
"""
Скрипт для миграции цен из таблицы current_prices в JSON файл
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from price_storage import update_prices, get_all_prices
from config import Config

# Конфигурация из переменных окружения
DATABASE_URL = os.getenv('DATABASE_URL', Config.DATABASE_URL)

# Создаем подключение к БД
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def migrate_prices():
    """
    Мигрировать цены из БД в JSON файл
    """
    print("🔄 Начало миграции цен из БД в JSON файл...")
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли таблица current_prices
        try:
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='current_prices'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                print("⚠️  Таблица current_prices не найдена в БД. Возможно, она уже была удалена.")
                return
        except Exception as e:
            # Для других БД (PostgreSQL, MySQL) используем другой способ проверки
            try:
                result = db.execute(text("SELECT 1 FROM current_prices LIMIT 1"))
                table_exists = True
            except Exception:
                print("⚠️  Таблица current_prices не найдена в БД. Возможно, она уже была удалена.")
                return
        
        # Получаем все цены из БД через прямой SQL запрос
        query = text("""
            SELECT sku, price, old_price, currency, discount_percentage, 
                   COALESCE(is_parse, 1) as is_parse, updated_at
            FROM current_prices
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        if not rows:
            print("⚠️  В таблице current_prices нет данных для миграции")
            return
        
        print(f"📦 Найдено {len(rows)} записей в таблице current_prices")
        
        # Формируем словарь для обновления
        prices_dict = {}
        
        for row in rows:
            sku = row[0]
            price = float(row[1])
            old_price = float(row[2]) if row[2] is not None else price
            currency = row[3] or "RUB"
            discount_percentage = float(row[4]) if row[4] is not None else 0.0
            is_parse = bool(row[5]) if row[5] is not None else True
            
            # Обрабатываем updated_at - может быть datetime объектом или строкой
            updated_at_value = row[6]
            if updated_at_value:
                if hasattr(updated_at_value, 'isoformat'):
                    # Это datetime объект
                    updated_at = updated_at_value.isoformat()
                elif isinstance(updated_at_value, str):
                    # Уже строка
                    updated_at = updated_at_value
                else:
                    updated_at = None
            else:
                updated_at = None
            
            prices_dict[sku] = {
                "price": price,
                "old_price": old_price,
                "currency": currency,
                "discount_percentage": discount_percentage,
                "is_parse": is_parse,
                "updated_at": updated_at
            }
        
        # Обновляем JSON файл
        if prices_dict:
            update_prices(prices_dict)
            print(f"✅ Успешно мигрировано {len(prices_dict)} записей в JSON файл")
            
            # Проверяем результат
            all_prices = get_all_prices()
            print(f"📊 Всего записей в JSON файле: {len(all_prices)}")
        else:
            print("⚠️  Нет данных для миграции")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_prices()


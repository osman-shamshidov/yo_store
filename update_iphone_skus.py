#!/usr/bin/env python3
"""
Скрипт для обновления SKU для iPhone товаров
Новый формат SKU: name в нижнем регистре, без пробелов, без "gb", без "iphone"
Также обновляет SKU в таблице current_prices
"""

import sys
import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import Product, CurrentPrice

# Создаем подключение к БД
DATABASE_URL = os.getenv('DATABASE_URL', Config.DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_new_sku(name: str) -> str:
    """
    Генерирует новый SKU из названия товара
    Формат: name в нижнем регистре, без пробелов, без "gb", без "iphone"
    Цвета: вместо сдвоенных оставлять одно слово (Cosmic Orange -> Orange)
    
    Args:
        name: Название товара (например, "iPhone 16 128GB Black SIM")
        
    Returns:
        Новый SKU (например, "16128blacksim")
    """
    # Приводим к нижнему регистру
    sku = name.lower()
    
    # Убираем "iphone" (но оставляем модель)
    sku = re.sub(r'\biphone\s+', '', sku, flags=re.IGNORECASE)
    
    # Убираем "gb" но сохраняем числа перед ним (128GB -> 128)
    # Заменяем "128GB" на "128" (убираем только "gb", числа остаются)
    sku = re.sub(r'(\d+)\s*gb\b', r'\1', sku, flags=re.IGNORECASE)
    sku = re.sub(r'\bgb\b', '', sku, flags=re.IGNORECASE)
    
    # Исправляем цвета: убираем префиксы перед цветами
    # Список префиксов, которые нужно убирать перед цветами
    color_prefixes = [
        r'\bcosmic\s+',      # Cosmic Orange -> Orange
        r'\btitanium\s+',    # Titanium White -> White, Titanium Desert -> Desert, Titanium Natural -> Natural
        r'\bspace\s+',       # Space Gray -> Gray
        r'\bdeep\s+',        # Deep Blue -> Blue
        r'\bsky\s+',         # Sky Blue -> Blue (для AirPods и MacBook)
        r'\blight\s+',       # Light Gold -> Gold
        r'\bmist\s+',        # Mist Blue -> Blue
    ]
    
    for prefix in color_prefixes:
        sku = re.sub(prefix, '', sku, flags=re.IGNORECASE)
    
    # Убираем все пробелы и специальные символы
    sku = re.sub(r'\s+', '', sku)
    sku = re.sub(r'[^\w]', '', sku)
    
    # Убираем множественные пробелы/подчеркивания, если они остались
    sku = re.sub(r'_+', '', sku)
    
    return sku.strip()

def update_iphone_skus():
    """
    Обновить SKU для всех iPhone товаров
    """
    db = SessionLocal()
    
    try:
        print("🔄 Начало обновления SKU для iPhone товаров...")
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Создаем резервную копию перед изменениями
        backup_name = f"electronics_store.db.backup_before_sku_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Создание резервной копии: {backup_name}")
        
        # Для SQLite просто копируем файл
        if DATABASE_URL.startswith('sqlite'):
            import shutil
            db_path = DATABASE_URL.replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
        
        # Находим все iPhone товары (исключаем MacBook)
        iphone_products = db.query(Product).filter(
            ((Product.name.like('%iPhone%')) | 
             (Product.level_2.like('%iPhone%'))) &
            (~Product.name.like('%MacBook%')) &
            (~Product.name.like('%Macbook%')) &
            (~Product.level_2.like('%MacBook%')) &
            (~Product.level_2.like('%Macbook%'))
        ).all()
        
        print(f"\n📦 Найдено iPhone товаров: {len(iphone_products)}")
        
        updated_count = 0
        errors = []
        sku_mapping = {}  # Старый SKU -> Новый SKU для обновления current_prices
        
        # Сначала собираем все новые SKU и проверяем конфликты
        products_to_update = []  # Список товаров для обновления
        new_sku_to_products = {}  # Новый SKU -> список товаров
        
        print("\n🔍 Проверка конфликтов SKU...")
        
        for product in iphone_products:
            try:
                old_sku = product.sku
                new_sku = generate_new_sku(product.name)
                
                # Проверяем, что новый SKU не пустой
                if not new_sku:
                    print(f"⚠️  Пропущен товар ID {product.id}: пустой SKU после преобразования")
                    errors.append(f"ID {product.id}: пустой SKU")
                    continue
                
                # Проверяем, что новый SKU не совпадает со старым
                if old_sku == new_sku:
                    print(f"ℹ️  Товар ID {product.id} уже имеет правильный SKU: {new_sku}")
                    continue
                
                # Собираем товары с одинаковыми новыми SKU
                if new_sku not in new_sku_to_products:
                    new_sku_to_products[new_sku] = []
                new_sku_to_products[new_sku].append((product, old_sku))
                
            except Exception as e:
                print(f"❌ Ошибка при обработке товара ID {product.id}: {e}")
                errors.append(f"ID {product.id}: {str(e)}")
                continue
        
        # Обрабатываем конфликты: если несколько товаров получают одинаковый SKU,
        # добавляем уникальный суффикс (ID товара)
        print("\n🔧 Разрешение конфликтов SKU...")
        
        for new_sku, products_list in new_sku_to_products.items():
            if len(products_list) == 1:
                # Нет конфликта, можно использовать как есть
                product, old_sku = products_list[0]
                products_to_update.append((product, old_sku, new_sku))
            else:
                # Конфликт: несколько товаров с одинаковым SKU
                print(f"⚠️  Конфликт SKU '{new_sku}': {len(products_list)} товаров")
                for idx, (product, old_sku) in enumerate(products_list):
                    # Добавляем ID товара для уникальности
                    unique_sku = f"{new_sku}{product.id}"
                    products_to_update.append((product, old_sku, unique_sku))
                    print(f"   ID {product.id}: '{old_sku}' -> '{unique_sku}' (добавлен суффикс ID)")
        
        # Теперь обновляем товары
        print(f"\n💾 Обновление {len(products_to_update)} товаров...")
        
        for product, old_sku, new_sku in products_to_update:
            try:
                # Проверяем, что новый SKU не используется другим товаром
                existing_product = db.query(Product).filter(
                    Product.sku == new_sku,
                    Product.id != product.id
                ).first()
                
                if existing_product:
                    # Если все еще конфликт, добавляем ID
                    new_sku = f"{new_sku}{product.id}"
                    print(f"⚠️  Дополнительный конфликт для ID {product.id}, использован SKU с ID: {new_sku}")
                
                # Сохраняем маппинг для обновления current_prices
                sku_mapping[old_sku] = new_sku
                
                # Обновляем SKU в products
                product.sku = new_sku
                product.updated_at = datetime.utcnow()
                
                updated_count += 1
                print(f"✅ ID {product.id}: '{old_sku}' -> '{new_sku}' ({product.name})")
                
            except Exception as e:
                print(f"❌ Ошибка при обновлении товара ID {product.id}: {e}")
                errors.append(f"ID {product.id}: {str(e)}")
                continue
        
        # Сохраняем изменения в products
        if updated_count > 0:
            print(f"\n💾 Сохранение изменений в таблице products...")
            db.commit()
            print(f"✅ Обновлено {updated_count} записей в products")
        
        # Обновляем SKU в current_prices
        print(f"\n🔄 Обновление SKU в таблице current_prices...")
        prices_updated = 0
        
        for old_sku, new_sku in sku_mapping.items():
            try:
                # Находим запись цены по старому SKU
                current_price = db.query(CurrentPrice).filter(
                    CurrentPrice.sku == old_sku
                ).first()
                
                if current_price:
                    # Обновляем SKU
                    current_price.sku = new_sku
                    current_price.updated_at = datetime.utcnow()
                    prices_updated += 1
                    print(f"✅ Обновлена цена: '{old_sku}' -> '{new_sku}'")
                else:
                    print(f"⚠️  Цена для SKU '{old_sku}' не найдена")
                    errors.append(f"Цена не найдена для SKU: {old_sku}")
                    
            except Exception as e:
                print(f"❌ Ошибка при обновлении цены для SKU '{old_sku}': {e}")
                errors.append(f"Ошибка обновления цены для SKU {old_sku}: {str(e)}")
        
        # Сохраняем изменения в current_prices
        if prices_updated > 0:
            db.commit()
            print(f"✅ Обновлено {prices_updated} записей в current_prices")
        
        # Итоги
        print(f"\n📊 Итоги обновления:")
        print(f"   Обновлено товаров (products): {updated_count}")
        print(f"   Обновлено цен (current_prices): {prices_updated}")
        print(f"   Ошибок: {len(errors)}")
        
        if errors:
            print(f"\n⚠️  Ошибки:")
            for error in errors[:10]:  # Показываем первые 10 ошибок
                print(f"   - {error}")
            if len(errors) > 10:
                print(f"   ... и еще {len(errors) - 10} ошибок")
        
        print(f"\n✅ Обновление завершено успешно")
        
        return updated_count, prices_updated
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        update_iphone_skus()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


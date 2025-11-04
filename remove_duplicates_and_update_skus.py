#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов iPhone товаров и обновления SKU
Удаляет товары-дубликаты, оставляя один товар с ценой или более новый
Затем обновляет SKU без добавления ID
"""

import sys
import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from collections import defaultdict

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
    """
    # Приводим к нижнему регистру
    sku = name.lower()
    
    # Убираем "iphone" (но оставляем модель)
    sku = re.sub(r'\biphone\s+', '', sku, flags=re.IGNORECASE)
    
    # Убираем "gb" но сохраняем числа перед ним (128GB -> 128)
    sku = re.sub(r'(\d+)\s*gb\b', r'\1', sku, flags=re.IGNORECASE)
    sku = re.sub(r'\bgb\b', '', sku, flags=re.IGNORECASE)
    
    # Исправляем цвета: убираем префиксы перед цветами
    color_prefixes = [
        r'\bcosmic\s+',
        r'\btitanium\s+',
        r'\bspace\s+',
        r'\bdeep\s+',
        r'\bsky\s+',
        r'\blight\s+',
        r'\bmist\s+',
    ]
    
    for prefix in color_prefixes:
        sku = re.sub(prefix, '', sku, flags=re.IGNORECASE)
    
    # Убираем все пробелы и специальные символы
    sku = re.sub(r'\s+', '', sku)
    sku = re.sub(r'[^\w]', '', sku)
    sku = re.sub(r'_+', '', sku)
    
    return sku.strip()

def remove_duplicates_and_update_skus():
    """
    Удалить дубликаты iPhone товаров и обновить SKU
    """
    db = SessionLocal()
    
    try:
        print("🔄 Начало удаления дубликатов и обновления SKU для iPhone товаров...")
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Создаем резервную копию перед изменениями
        backup_name = f"electronics_store.db.backup_before_remove_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
        
        def normalize_name_for_comparison(name: str) -> str:
            """
            Нормализует название для сравнения (убирает порядок слов в цветах)
            Например: "Titanium White" и "White Titanium" -> одинаковое
            """
            # Приводим к нижнему регистру
            normalized = name.lower()
            words = normalized.split()
            
            # Список цветовых префиксов
            color_prefixes = ['titanium', 'cosmic', 'space', 'deep', 'sky', 'light', 'mist']
            # Список цветов
            colors = ['white', 'black', 'blue', 'orange', 'desert', 'natural', 'gray', 'gold', 'silver', 'pink', 'teal', 'green', 'red', 'purple', 'yellow']
            
            # Находим пары префикс-цвет (в любом порядке)
            used_indices = set()
            color_pairs = []
            
            # Ищем пары: префикс + цвет (в любом порядке)
            for i in range(len(words) - 1):
                if i in used_indices:
                    continue
                    
                word1 = words[i]
                word2 = words[i + 1]
                
                # Проверяем пары: префикс + цвет или цвет + префикс
                if word1 in color_prefixes and word2 in colors:
                    color_pairs.append((word1, word2))
                    used_indices.update([i, i + 1])
                elif word1 in colors and word2 in color_prefixes:
                    # Меняем порядок: цвет + префикс -> префикс + цвет
                    color_pairs.append((word2, word1))
                    used_indices.update([i, i + 1])
            
            # Создаем новую версию с нормализованными парами
            new_words = []
            
            # Добавляем слова, которые не в цветовых парах
            for i, word in enumerate(words):
                if i not in used_indices:
                    new_words.append(word)
            
            # Добавляем цветовые пары в отсортированном виде (префикс + цвет)
            color_pairs_sorted = sorted(color_pairs)
            for prefix, color in color_pairs_sorted:
                new_words.append(prefix)
                new_words.append(color)
            
            # Сортируем все слова для полной нормализации
            normalized = ' '.join(sorted(new_words))
            
            return normalized
        
        # Группируем товары по нормализованному названию
        products_by_name = defaultdict(list)
        for product in iphone_products:
            normalized_name = normalize_name_for_comparison(product.name)
            products_by_name[normalized_name].append(product)
        
        # Находим дубликаты
        duplicates_to_remove = []
        products_to_keep = []
        
        print(f"\n🔍 Поиск дубликатов...")
        
        for name, products_list in products_by_name.items():
            if len(products_list) > 1:
                # Есть дубликаты
                print(f"⚠️  Найдены дубликаты для '{name}': {len(products_list)} товаров")
                
                # Определяем, какой товар оставить
                # Приоритет: товар с ценой > товар без цены, затем по ID (меньший ID обычно старше)
                products_with_price = []
                products_without_price = []
                
                for product in products_list:
                    price = db.query(CurrentPrice).filter(CurrentPrice.sku == product.sku).first()
                    if price:
                        products_with_price.append((product, price))
                    else:
                        products_without_price.append(product)
                
                # Если есть товары с ценой, выбираем первый (с меньшим ID)
                if products_with_price:
                    products_with_price.sort(key=lambda x: x[0].id)
                    keep_product, keep_price = products_with_price[0]
                    products_to_keep.append(keep_product)
                    print(f"   ✅ Оставляем ID {keep_product.id} (с ценой: {keep_price.price} ₽)")
                    
                    # Остальные товары с ценой - удаляем
                    for product, price in products_with_price[1:]:
                        duplicates_to_remove.append((product, f"дубликат ID {keep_product.id}"))
                        print(f"   ❌ Удаляем ID {product.id} (дубликат с ценой: {price.price} ₽)")
                    
                    # Товары без цены - удаляем
                    for product in products_without_price:
                        duplicates_to_remove.append((product, f"дубликат ID {keep_product.id}"))
                        print(f"   ❌ Удаляем ID {product.id} (без цены)")
                else:
                    # Все товары без цены, оставляем первый (с меньшим ID)
                    products_without_price.sort(key=lambda x: x.id)
                    keep_product = products_without_price[0]
                    products_to_keep.append(keep_product)
                    print(f"   ✅ Оставляем ID {keep_product.id} (первый)")
                    
                    # Остальные удаляем
                    for product in products_without_price[1:]:
                        duplicates_to_remove.append((product, f"дубликат ID {keep_product.id}"))
                        print(f"   ❌ Удаляем ID {product.id} (дубликат)")
            else:
                # Нет дубликатов, оставляем товар
                products_to_keep.append(products_list[0])
        
        print(f"\n📊 Статистика дубликатов:")
        print(f"   Всего товаров: {len(iphone_products)}")
        print(f"   Уникальных названий: {len(products_by_name)}")
        print(f"   Товаров для удаления: {len(duplicates_to_remove)}")
        print(f"   Товаров для сохранения: {len(products_to_keep)}")
        
        # Удаляем дубликаты
        if duplicates_to_remove:
            print(f"\n🗑️  Удаление {len(duplicates_to_remove)} дубликатов...")
            
            deleted_count = 0
            for product, reason in duplicates_to_remove:
                try:
                    # Удаляем цену товара
                    db.query(CurrentPrice).filter(CurrentPrice.sku == product.sku).delete()
                    
                    # Удаляем товар
                    db.delete(product)
                    deleted_count += 1
                    print(f"   ✅ Удален ID {product.id}: {product.name} ({reason})")
                except Exception as e:
                    print(f"   ❌ Ошибка при удалении ID {product.id}: {e}")
            
            # Сохраняем удаления
            db.commit()
            print(f"✅ Удалено {deleted_count} дубликатов")
        
        # Теперь обновляем SKU для оставшихся товаров
        print(f"\n🔄 Обновление SKU для {len(products_to_keep)} товаров...")
        
        updated_count = 0
        errors = []
        sku_mapping = {}  # Старый SKU -> Новый SKU для обновления current_prices
        
        # Собираем все новые SKU для проверки конфликтов
        new_sku_to_products = {}
        
        for product in products_to_keep:
            try:
                old_sku = product.sku
                new_sku = generate_new_sku(product.name)
                
                if not new_sku:
                    print(f"⚠️  Пропущен товар ID {product.id}: пустой SKU после преобразования")
                    errors.append(f"ID {product.id}: пустой SKU")
                    continue
                
                # Проверяем, не содержит ли старый SKU ID в конце (например, "16128tealsim5")
                # Если содержит, обновляем даже если новый SKU совпадает с базовым
                sku_has_id_suffix = old_sku.endswith(str(product.id))
                
                if old_sku == new_sku and not sku_has_id_suffix:
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
        
        # Проверяем конфликты после удаления дубликатов
        print(f"\n🔍 Проверка конфликтов SKU после удаления дубликатов...")
        
        for new_sku, products_list in new_sku_to_products.items():
            if len(products_list) > 1:
                print(f"⚠️  Конфликт SKU '{new_sku}': {len(products_list)} товаров")
                for product, old_sku in products_list:
                    print(f"   - ID {product.id}: {product.name}")
        
        # Обновляем SKU по одному с коммитом после каждого
        print(f"\n💾 Обновление SKU по одному товару...")
        
        for new_sku, products_list in new_sku_to_products.items():
            for product, old_sku in products_list:
                try:
                    # Проверяем, что новый SKU не используется другим товаром
                    existing_product = db.query(Product).filter(
                        Product.sku == new_sku,
                        Product.id != product.id
                    ).first()
                    
                    if existing_product:
                        print(f"⚠️  SKU '{new_sku}' уже используется товаром ID {existing_product.id}")
                        errors.append(f"ID {product.id}: SKU конфликт с ID {existing_product.id}")
                        continue
                    
                    # Обновляем SKU в products
                    product.sku = new_sku
                    product.updated_at = datetime.utcnow()
                    
                    # Сохраняем сразу, чтобы избежать конфликтов
                    db.commit()
                    
                    # Сохраняем маппинг для обновления current_prices
                    sku_mapping[old_sku] = new_sku
                    
                    updated_count += 1
                    print(f"✅ ID {product.id}: '{old_sku}' -> '{new_sku}' ({product.name})")
                    
                except Exception as e:
                    print(f"❌ Ошибка при обновлении товара ID {product.id}: {e}")
                    db.rollback()
                    errors.append(f"ID {product.id}: {str(e)}")
                    continue
        
        if updated_count > 0:
            print(f"✅ Обновлено {updated_count} записей в products")
        
        # Обновляем SKU в current_prices
        print(f"\n🔄 Обновление SKU в таблице current_prices...")
        prices_updated = 0
        
        for old_sku, new_sku in sku_mapping.items():
            try:
                current_price = db.query(CurrentPrice).filter(
                    CurrentPrice.sku == old_sku
                ).first()
                
                if current_price:
                    current_price.sku = new_sku
                    current_price.updated_at = datetime.utcnow()
                    prices_updated += 1
                    print(f"✅ Обновлена цена: '{old_sku}' -> '{new_sku}'")
                else:
                    print(f"⚠️  Цена для SKU '{old_sku}' не найдена")
                    
            except Exception as e:
                print(f"❌ Ошибка при обновлении цены для SKU '{old_sku}': {e}")
                errors.append(f"Ошибка обновления цены для SKU {old_sku}: {str(e)}")
        
        # Сохраняем изменения в current_prices
        if prices_updated > 0:
            db.commit()
            print(f"✅ Обновлено {prices_updated} записей в current_prices")
        
        # Итоги
        print(f"\n📊 Итоги обновления:")
        print(f"   Удалено дубликатов: {len(duplicates_to_remove)}")
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
        
        return len(duplicates_to_remove), updated_count, prices_updated
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        remove_duplicates_and_update_skus()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


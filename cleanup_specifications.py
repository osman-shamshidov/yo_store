#!/usr/bin/env python3
"""
Скрипт для очистки specifications в таблице products
Оставляет только: color, ram, sim_config, disk, screen_size
"""

import sys
import os
import json
import shutil
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import Product

# Создаем подключение к БД
DATABASE_URL = os.getenv('DATABASE_URL', Config.DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cleanup_specifications():
    """
    Очистить specifications, оставив только нужные поля
    """
    db = SessionLocal()
    
    try:
        print("🔄 Начало очистки specifications...")
        print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Создаем резервную копию перед изменениями
        backup_name = f"electronics_store.db.backup_before_cleanup_specs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Создание резервной копии: {backup_name}")
        
        # Для SQLite просто копируем файл
        if DATABASE_URL.startswith('sqlite'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
        
        # Получаем все товары
        products = db.query(Product).all()
        print(f"\n📦 Найдено товаров: {len(products)}")
        
        # Поля, которые нужно оставить
        allowed_fields = {'color', 'ram', 'sim_config', 'disk', 'screen_size'}
        
        updated_count = 0
        errors = []
        empty_specs_count = 0
        
        print(f"\n🔍 Обработка товаров...")
        print(f"   Оставляем поля: {', '.join(sorted(allowed_fields))}")
        
        for product in products:
            try:
                if not product.specifications:
                    empty_specs_count += 1
                    continue
                
                # Парсим JSON
                try:
                    if isinstance(product.specifications, str):
                        specs = json.loads(product.specifications)
                    else:
                        specs = product.specifications
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"⚠️  Товар ID {product.id}: ошибка парсинга JSON: {e}")
                    errors.append(f"ID {product.id}: ошибка парсинга JSON")
                    continue
                
                if not isinstance(specs, dict):
                    print(f"⚠️  Товар ID {product.id}: specifications не является словарем")
                    errors.append(f"ID {product.id}: specifications не является словарем")
                    continue
                
                # Создаем новый словарь только с нужными полями
                new_specs = {}
                for field in allowed_fields:
                    if field in specs:
                        new_specs[field] = specs[field]
                
                # Преобразуем обратно в JSON
                new_specs_json = json.dumps(new_specs, ensure_ascii=False)
                
                # Обновляем только если что-то изменилось
                old_specs_json = json.dumps(specs, ensure_ascii=False, sort_keys=True)
                new_specs_json_sorted = json.dumps(new_specs, ensure_ascii=False, sort_keys=True)
                
                if old_specs_json != new_specs_json_sorted:
                    product.specifications = new_specs_json
                    product.updated_at = datetime.utcnow()
                    updated_count += 1
                    
                    if updated_count <= 10:  # Показываем первые 10 примеров
                        removed_fields = set(specs.keys()) - allowed_fields
                        if removed_fields:
                            print(f"   ✅ ID {product.id}: удалены поля {', '.join(removed_fields)}")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке товара ID {product.id}: {e}")
                errors.append(f"ID {product.id}: {str(e)}")
                continue
        
        # Сохраняем изменения
        if updated_count > 0:
            print(f"\n💾 Сохранение изменений...")
            db.commit()
            print(f"✅ Обновлено {updated_count} товаров")
        else:
            print(f"\nℹ️  Нет товаров для обновления")
        
        # Итоги
        print(f"\n📊 Итоги обновления:")
        print(f"   Всего товаров: {len(products)}")
        print(f"   Обновлено товаров: {updated_count}")
        print(f"   Товаров с пустыми specifications: {empty_specs_count}")
        print(f"   Ошибок: {len(errors)}")
        
        if errors:
            print(f"\n⚠️  Ошибки:")
            for error in errors[:10]:  # Показываем первые 10 ошибок
                print(f"   - {error}")
            if len(errors) > 10:
                print(f"   ... и еще {len(errors) - 10} ошибок")
        
        print(f"\n✅ Очистка завершена успешно")
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Критическая ошибка при очистке: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        cleanup_specifications()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


#!/usr/bin/env python3
"""
Скрипт для замены значений sim_config в specifications
Single SIM -> SIM + eSIM
eSIM -> Dual eSIM
Dual SIM -> Dual SIM (без изменений)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Product
from config import Config
import json
from datetime import datetime

def update_sim_config_in_specs():
    """Обновить значения sim_config в specifications"""
    engine = create_engine(Config.DATABASE_URL)
    with Session(engine) as session:
        updated_count = 0
        
        # Маппинг старых значений на новые
        sim_config_mapping = {
            'Single SIM': 'SIM + eSIM',
            'eSIM': 'Dual eSIM',
            'Dual SIM': 'Dual SIM'  # Без изменений, но для полноты
        }
        
        print("🔄 Начинаем обновление sim_config в specifications...\n")
        
        # Получаем все товары
        products = session.query(Product).all()
        total_products = len(products)
        print(f"📦 Найдено товаров: {total_products}\n")
        
        for product in products:
            if not product.specifications:
                continue
            
            try:
                # Парсим JSON
                if isinstance(product.specifications, str):
                    specs = json.loads(product.specifications)
                else:
                    specs = product.specifications
                
                # Проверяем наличие sim_config
                if 'sim_config' in specs:
                    old_value = specs.get('sim_config', '')
                    
                    # Проверяем, нужно ли обновление
                    if old_value in sim_config_mapping:
                        new_value = sim_config_mapping[old_value]
                        
                        # Обновляем только если значение изменилось
                        if old_value != new_value:
                            specs['sim_config'] = new_value
                            product.specifications = json.dumps(specs, ensure_ascii=False)
                            product.updated_at = datetime.utcnow()
                            updated_count += 1
                            print(f"  ✅ Товар ID {product.id}: '{old_value}' -> '{new_value}'")
                        elif old_value == 'Dual SIM':
                            # Dual SIM остается без изменений, но обновим updated_at для консистентности
                            product.updated_at = datetime.utcnow()
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"  ⚠️  Ошибка парсинга JSON для товара ID {product.id}: {e}")
                continue
        
        # Сохраняем изменения
        if updated_count > 0:
            session.commit()
            print(f"\n✅ Обновлено товаров: {updated_count}")
        else:
            print("\nℹ️  Нет товаров для обновления")
        
        return updated_count

if __name__ == "__main__":
    print("🚀 Запуск обновления sim_config в specifications...\n")
    try:
        updated = update_sim_config_in_specs()
        if updated > 0:
            print(f"\n✅ Скрипт завершен успешно. Обновлено: {updated} товаров")
        else:
            print("\n✅ Скрипт завершен. Изменений не требуется")
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении скрипта: {e}")
        import traceback
        traceback.print_exc()


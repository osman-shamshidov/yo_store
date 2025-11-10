#!/usr/bin/env python3
"""
Скрипт для инициализации промокодов в базе данных
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, SessionLocal
from models import PromoCode

def init_promo_codes():
    """Создает промокоды в базе данных"""
    
    # Создаем таблицы
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже промокоды
        existing_codes = db.query(PromoCode).count()
        if existing_codes > 0:
            print(f"В базе данных уже есть {existing_codes} промокодов")
            print("Проверяем наличие нужных промокодов...")
            
            # Проверяем наличие каждого промокода
            codes_to_check = ['test1000', 'test20', 'test_adapter']
            for code in codes_to_check:
                code_upper = code.upper()
                existing = db.query(PromoCode).filter(PromoCode.code == code_upper).first()
                if existing:
                    print(f"  ✅ Промокод {code} уже существует")
                else:
                    print(f"  ⚠️  Промокод {code} отсутствует, создаем...")
                    create_promo_code(db, code)
        else:
            print("Создаем промокоды...")
            # Создаем все промокоды
            create_promo_code(db, 'test1000')
            create_promo_code(db, 'test20')
            create_promo_code(db, 'test_adapter')
        
        db.commit()
        print("✅ Промокоды успешно инициализированы")
        
        # Выводим информацию о созданных промокодах
        print("\n📋 Список промокодов:")
        promo_codes = db.query(PromoCode).all()
        for pc in promo_codes:
            print(f"  • {pc.code}: {pc.description}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании промокодов: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def create_promo_code(db, code: str):
    """Создает промокод по коду"""
    
    if code == 'test1000':
        # test1000 - 1000р скидка
        promo = PromoCode(
            code='TEST1000',
            discount_type='fixed',
            discount_value=1000.0,
            min_order_amount=0.0,
            is_active=True,
            usage_limit=None,  # Безлимит
            used_count=0,
            valid_from=datetime.utcnow(),
            valid_until=None,  # Без срока действия
            description='Скидка 1000 рублей на заказ'
        )
        db.add(promo)
        print(f"  ✅ Создан промокод test1000: скидка 1000 рублей")
        
    elif code == 'test20':
        # test20 - 20% скидка при заказе от 200 тыс
        promo = PromoCode(
            code='TEST20',
            discount_type='percentage',
            discount_value=20.0,
            min_order_amount=200000.0,
            is_active=True,
            usage_limit=None,  # Безлимит
            used_count=0,
            valid_from=datetime.utcnow(),
            valid_until=None,  # Без срока действия
            description='Скидка 20% при заказе от 200 000 рублей'
        )
        db.add(promo)
        print(f"  ✅ Создан промокод test20: скидка 20% при заказе от 200 000 рублей")
        
    elif code == 'test_adapter':
        # test_adapter - бесплатный адаптер adapter20w при заказе смартфона
        promo = PromoCode(
            code='TEST_ADAPTER',
            discount_type='free_item',
            discount_value=0.0,
            min_order_amount=0.0,
            free_item_sku='adapter20w',  # SKU адаптера (будет искаться по частичному совпадению)
            free_item_condition=json.dumps({
                'category': 'Смартфоны',
                'level_0': 'Смартфоны'
            }),
            is_active=True,
            usage_limit=None,  # Безлимит
            used_count=0,
            valid_from=datetime.utcnow(),
            valid_until=None,  # Без срока действия
            description='Бесплатный адаптер adapter20w при заказе смартфона'
        )
        db.add(promo)
        print(f"  ✅ Создан промокод test_adapter: бесплатный адаптер adapter20w при заказе смартфона")

if __name__ == "__main__":
    init_promo_codes()


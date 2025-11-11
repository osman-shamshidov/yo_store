#!/usr/bin/env python3
"""
Модуль для работы с ценами в JSON файле
Заменяет таблицу current_prices в БД
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import threading

# Путь к файлу с ценами
PRICES_FILE = os.getenv('PRICES_FILE', 'current_prices.json')

# Блокировка для потокобезопасности
_lock = threading.Lock()


def _get_prices_file_path() -> str:
    """Получить полный путь к файлу с ценами"""
    if os.path.isabs(PRICES_FILE):
        return PRICES_FILE
    # Относительный путь от директории проекта
    project_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(project_dir, PRICES_FILE)


def _calculate_discount_percentage(old_price: float, price: float) -> float:
    """
    Вычислить процент скидки из old_price и price
    """
    if old_price and old_price > price and old_price > 0:
        return ((old_price - price) / old_price) * 100
    return 0.0


def _load_prices() -> Dict[str, Dict]:
    """
    Загрузить цены из JSON файла
    Возвращает словарь: {sku: {price, old_price, currency, is_parse}}
    """
    file_path = _get_prices_file_path()
    
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Удаляем updated_at и discount_percentage из всех записей при загрузке (для обратной совместимости)
            cleaned_data = {}
            for sku, price_info in data.items():
                cleaned_info = {k: v for k, v in price_info.items() if k not in ['updated_at', 'discount_percentage']}
                cleaned_data[sku] = cleaned_info
            return cleaned_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Ошибка при загрузке цен из {file_path}: {e}")
        return {}


def _save_prices(prices: Dict[str, Dict]) -> bool:
    """
    Сохранить цены в JSON файл
    """
    file_path = _get_prices_file_path()
    
    try:
        # Создаем директорию если нужно
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        # Сохраняем с форматированием
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prices, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        print(f"❌ Ошибка при сохранении цен в {file_path}: {e}")
        return False


def get_price(sku: str) -> Optional[Dict]:
    """
    Получить цену для SKU
    Возвращает словарь с полями: price, old_price, currency, discount_percentage (вычисляется), is_parse
    """
    with _lock:
        prices = _load_prices()
        price_data = prices.get(sku)
        if price_data:
            # Вычисляем discount_percentage динамически
            old_price = price_data.get('old_price', 0.0)
            price = price_data.get('price', 0.0)
            price_data['discount_percentage'] = _calculate_discount_percentage(old_price, price)
        return price_data


def get_all_prices() -> Dict[str, Dict]:
    """
    Получить все цены
    Возвращает словарь всех цен: {sku: {price, old_price, currency, discount_percentage (вычисляется), is_parse}}
    """
    with _lock:
        prices = _load_prices()
        # Вычисляем discount_percentage для всех записей
        for sku, price_data in prices.items():
            old_price = price_data.get('old_price', 0.0)
            price = price_data.get('price', 0.0)
            price_data['discount_percentage'] = _calculate_discount_percentage(old_price, price)
        return prices


def set_price(
    sku: str,
    price: float,
    old_price: Optional[float] = None,
    currency: str = "RUB",
    is_parse: bool = True
) -> bool:
    """
    Установить цену для SKU
    discount_percentage вычисляется автоматически из old_price и price
    """
    with _lock:
        prices = _load_prices()
        
        prices[sku] = {
            "price": float(price),
            "old_price": float(old_price) if old_price else float(price),
            "currency": currency,
            "is_parse": is_parse
        }
        
        return _save_prices(prices)


def update_prices(prices_dict: Dict[str, Dict]) -> bool:
    """
    Обновить несколько цен за раз
    prices_dict: {sku: {price, old_price, currency, ...}}
    """
    with _lock:
        all_prices = _load_prices()
        
        for sku, price_data in prices_dict.items():
            # Сохраняем is_parse если он был
            existing = all_prices.get(sku, {})
            is_parse = price_data.get('is_parse', existing.get('is_parse', True))
            
            all_prices[sku] = {
                "price": float(price_data.get('price', existing.get('price', 0))),
                "old_price": float(price_data.get('old_price', existing.get('old_price', price_data.get('price', 0)))),
                "currency": price_data.get('currency', existing.get('currency', 'RUB')),
                "is_parse": is_parse
            }
        
        return _save_prices(all_prices)


def delete_price(sku: str) -> bool:
    """
    Удалить цену для SKU
    """
    with _lock:
        prices = _load_prices()
        if sku in prices:
            del prices[sku]
            return _save_prices(prices)
        return True


def get_prices_by_parse_flag(is_parse: bool = True) -> List[str]:
    """
    Получить список SKU с флагом is_parse
    """
    with _lock:
        prices = _load_prices()
        return [sku for sku, data in prices.items() if data.get('is_parse', True) == is_parse]


def migrate_from_db(db_session) -> int:
    """
    Мигрировать цены из БД в JSON файл
    Возвращает количество мигрированных записей
    
    ВНИМАНИЕ: Эта функция использует прямой SQL запрос, так как модель CurrentPrice удалена
    """
    try:
        from sqlalchemy import text
        
        # Проверяем, существует ли таблица
        try:
            result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='current_prices'"))
            table_exists = result.fetchone() is not None
        except Exception:
            # Для других БД (PostgreSQL, MySQL) просто пытаемся выполнить запрос
            try:
                result = db_session.execute(text("SELECT 1 FROM current_prices LIMIT 1"))
                table_exists = True
            except Exception:
                print("⚠️  Таблица current_prices не найдена")
                return 0
        
        if not table_exists:
            print("⚠️  Таблица current_prices не найдена")
            return 0
        
        # Получаем все цены через прямой SQL запрос
        query = text("""
            SELECT sku, price, old_price, currency, discount_percentage, 
                   COALESCE(is_parse, 1) as is_parse, updated_at
            FROM current_prices
        """)
        
        result = db_session.execute(query)
        rows = result.fetchall()
        
        prices_dict = {}
        for row in rows:
            sku = row[0]
            price = float(row[1])
            old_price = float(row[2]) if row[2] is not None else price
            currency = row[3] or "RUB"
            is_parse = bool(row[5]) if row[5] is not None else True
            
            prices_dict[sku] = {
                "price": price,
                "old_price": old_price,
                "currency": currency,
                "is_parse": is_parse
            }
        
        if prices_dict:
            update_prices(prices_dict)
            return len(prices_dict)
        return 0
    except Exception as e:
        print(f"❌ Ошибка при миграции цен из БД: {e}")
        import traceback
        traceback.print_exc()
        return 0


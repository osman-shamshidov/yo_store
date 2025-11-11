#!/usr/bin/env python3
"""
Скрипт для автоматического обновления цен из внешнего сервиса
Запускается каждые 30 минут через systemd timer или cron
"""

import os
import sys
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from price_storage import get_prices_by_parse_flag, update_prices

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('price_updater.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
PRICE_SERVICE_URL = os.getenv('PRICE_SERVICE_URL', 'http://0.0.0.0:8005/api/prices')
PRICE_SERVICE_TOKEN = os.getenv('PRICE_SERVICE_TOKEN', None)


def get_all_skus() -> List[str]:
    """
    Получить все SKU из JSON файла, где is_parse == True
    
    Returns:
        List[str]: Список всех SKU для обновления
    """
    try:
        skus = get_prices_by_parse_flag(is_parse=True)
        logger.info(f"📦 Получено {len(skus)} SKU из JSON файла (is_parse=True)")
        return skus
    except Exception as e:
        logger.error(f"❌ Ошибка при получении SKU из JSON файла: {e}")
        return []


def get_prices_from_service(skus: List[str]) -> Optional[Dict]:
    """
    Получить цены из внешнего сервиса
    
    Args:
        skus: Список SKU для запроса
        
    Returns:
        Dict с ценами или None в случае ошибки
    """
    if not skus:
        logger.warning("⚠️  Список SKU пуст, пропускаем запрос к сервису")
        return None
    
    try:
        # Подготавливаем заголовки
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Добавляем токен авторизации, если он указан
        if PRICE_SERVICE_TOKEN:
            headers['Authorization'] = f'Bearer {PRICE_SERVICE_TOKEN}'
        
        # Формируем тело запроса
        payload = {
            "skus": skus
        }
        
        logger.info(f"📡 Отправка запроса к сервису: {PRICE_SERVICE_URL}")
        logger.info(f"📋 Запрашиваем цены для {len(skus)} товаров")
        
        # Отправляем POST запрос
        response = requests.post(
            PRICE_SERVICE_URL,
            json=payload,
            headers=headers,
            timeout=30  # Таймаут 30 секунд
        )
        
        # Проверяем статус ответа
        response.raise_for_status()
        
        # Парсим JSON ответ
        data = response.json()
        
        # Проверяем формат ответа
        if 'prices' in data:
            prices_dict = data['prices']
            logger.info(f"✅ Получено {len(prices_dict)} цен из сервиса")
            return prices_dict
        else:
            logger.error(f"❌ Неожиданный формат ответа: отсутствует поле 'prices'")
            logger.error(f"Ответ: {data}")
            return None
            
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"⚠️  Сервис недоступен: {PRICE_SERVICE_URL}. Оставляем цены без изменений.")
        logger.debug(f"Детали ошибки подключения: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.warning(f"⚠️  Таймаут при запросе к сервису: {PRICE_SERVICE_URL}. Оставляем цены без изменений.")
        logger.debug(f"Детали ошибки таймаута: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️  Ошибка при запросе к сервису: {e}. Оставляем цены без изменений.")
        return None
    except ValueError as e:
        logger.error(f"❌ Ошибка при парсинге JSON ответа: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return None


def update_prices_in_json(prices_dict: Dict) -> Dict[str, int]:
    """
    Обновить цены в JSON файле
    
    Args:
        prices_dict: Словарь с ценами в формате {sku: {price: float, name: str}}
        
    Returns:
        Dict с статистикой обновлений
    """
    stats = {
        'updated': 0,
        'created': 0,
        'not_found': 0,
        'errors': 0
    }
    
    if not prices_dict:
        logger.warning("⚠️  Словарь цен пуст, нет данных для обновления")
        return stats
    
    try:
        # Получаем все существующие цены для сохранения is_parse
        from price_storage import get_all_prices
        all_prices = get_all_prices()
        
        # Формируем словарь для обновления
        update_dict = {}
        
        for sku, price_info in prices_dict.items():
            try:
                # Проверяем формат данных
                if not isinstance(price_info, dict):
                    logger.warning(f"⚠️  Неверный формат данных для SKU {sku}: {price_info}")
                    stats['errors'] += 1
                    continue
                
                price_value = price_info.get('price')
                if price_value is None:
                    logger.warning(f"⚠️  Отсутствует цена для SKU {sku}")
                    stats['errors'] += 1
                    continue
                
                try:
                    price_value = float(price_value)
                except (ValueError, TypeError):
                    logger.warning(f"⚠️  Неверный формат цены для SKU {sku}: {price_value}")
                    stats['errors'] += 1
                    continue
                
                # Проверяем, существует ли цена в JSON файле
                existing_price = all_prices.get(sku)
                
                if not existing_price:
                    logger.warning(f"⚠️  Запись цены с SKU '{sku}' не найдена в JSON файле")
                    stats['not_found'] += 1
                    continue
                
                # Сохраняем старую цену как old_price, если она изменилась
                old_price_value = existing_price.get('price', 0.0)
                if old_price_value != price_value:
                    # Сохраняем is_parse из существующей записи
                    is_parse = existing_price.get('is_parse', True)
                    
                    update_dict[sku] = {
                        'price': price_value,
                        'old_price': old_price_value,
                        'currency': existing_price.get('currency', 'RUB'),
                        'is_parse': is_parse
                    }
                    stats['updated'] += 1
                    logger.info(f"✅ Обновлена цена для {sku}: {old_price_value} → {price_value} RUB")
                else:
                    logger.debug(f"ℹ️  Цена для {sku} не изменилась: {price_value} RUB")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке SKU {sku}: {e}")
                stats['errors'] += 1
                continue
        
        # Обновляем цены в JSON файле
        if update_dict:
            update_prices(update_dict)
            logger.info("💾 Изменения сохранены в JSON файл")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении цен в JSON файле: {e}")
        stats['errors'] += 1
    
    return stats


def main():
    """
    Основная функция для обновления цен
    """
    start_time = datetime.now()
    logger.info(f"🔄 Начало обновления цен - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📍 URL сервиса: {PRICE_SERVICE_URL}")
    
    try:
        # Получаем все SKU из JSON файла
        skus = get_all_skus()
        
        if not skus:
            logger.warning("⚠️  Не найдено ни одного SKU в JSON файле")
            return
        
        # Получаем цены из внешнего сервиса
        prices_dict = get_prices_from_service(skus)
        
        if not prices_dict:
            logger.warning("⚠️  Не удалось получить цены из сервиса. Цены остаются без изменений.")
            return
        
        # Обновляем цены в JSON файле
        stats = update_prices_in_json(prices_dict)
        
        # Выводим статистику
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("📊 Итоги обновления:")
        logger.info(f"   Обновлено: {stats['updated']}")
        logger.info(f"   Создано: {stats['created']}")
        logger.info(f"   Не найдено продуктов: {stats['not_found']}")
        logger.info(f"   Ошибок: {stats['errors']}")
        logger.info(f"⏱️  Время выполнения: {duration:.2f} секунд")
        logger.info(f"✅ Обновление цен завершено успешно")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        # Не завершаем процесс с ошибкой, чтобы шедулер мог продолжить работу
        return


if __name__ == "__main__":
    main()


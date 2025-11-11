#!/usr/bin/env python3
"""
Шедулер для автоматического обновления цен из внешнего сервиса
Запускает обновление каждые 30 минут
"""

import os
import sys
import time
import schedule
import logging
from datetime import datetime

# Добавляем путь к проекту для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('price_updater_scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Импортируем функцию main из скрипта обновления цен
from update_prices_from_service import main as update_prices


def run_price_update():
    """Запустить обновление цен"""
    logger.info("=" * 60)
    logger.info(f"🔄 Запуск обновления цен - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        update_prices()
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении обновления цен: {e}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("")


def main():
    """Основная функция шедулера"""
    logger.info("🚀 Запуск шедулера обновления цен")
    logger.info(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("⏰ Расписание: каждые 30 минут")
    logger.info("")
    
    # Настраиваем расписание: каждые 30 минут
    schedule.every(30).minutes.do(run_price_update)
    
    # Запускаем сразу при старте (опционально)
    logger.info("🔄 Запуск первого обновления при старте...")
    run_price_update()
    
    # Основной цикл шедулера
    logger.info("✅ Шедулер запущен. Ожидание следующего обновления...")
    logger.info("")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)  # Проверяем расписание каждую секунду
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Получен сигнал остановки (Ctrl+C)")
        logger.info("🛑 Остановка шедулера...")
        logger.info("✅ Шедулер остановлен")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в шедулере: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()


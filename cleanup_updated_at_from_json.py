#!/usr/bin/env python3
"""
Скрипт для удаления поля updated_at из current_prices.json
"""

import json
import os
from price_storage import _get_prices_file_path, _save_prices, _load_prices

def cleanup_updated_at():
    """Удалить поле updated_at из всех записей в JSON файле"""
    print("🔄 Начало очистки поля updated_at из current_prices.json...")
    
    file_path = _get_prices_file_path()
    
    if not os.path.exists(file_path):
        print("⚠️  Файл current_prices.json не найден")
        return
    
    try:
        # Загружаем данные
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Удаляем updated_at из всех записей
        cleaned_count = 0
        for sku, price_info in data.items():
            if 'updated_at' in price_info:
                del price_info['updated_at']
                cleaned_count += 1
        
        # Сохраняем очищенные данные
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Успешно удалено поле updated_at из {cleaned_count} записей")
        print(f"📊 Всего записей в файле: {len(data)}")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    cleanup_updated_at()


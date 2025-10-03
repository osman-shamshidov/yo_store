#!/usr/bin/env python3
"""
Скрипт для проверки различий между изображениями товаров
"""

import os
import hashlib
from PIL import Image
import requests

def get_file_hash(filepath):
    """Получить хеш файла"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_image_info(filepath):
    """Получить информацию об изображении"""
    try:
        with Image.open(filepath) as img:
            return {
                'size': img.size,
                'mode': img.mode,
                'format': img.format
            }
    except Exception as e:
        return {'error': str(e)}

def check_product_images(sku):
    """Проверить изображения товара"""
    product_dir = f"static/images/products/{sku}"
    
    if not os.path.exists(product_dir):
        print(f"❌ Папка {product_dir} не найдена")
        return
    
    print(f"🔍 Проверка изображений для {sku}:")
    print("=" * 50)
    
    images = []
    for filename in sorted(os.listdir(product_dir)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.svg')):
            filepath = os.path.join(product_dir, filename)
            file_hash = get_file_hash(filepath)
            file_size = os.path.getsize(filepath)
            image_info = get_image_info(filepath)
            
            images.append({
                'filename': filename,
                'hash': file_hash,
                'size': file_size,
                'info': image_info
            })
            
            print(f"📸 {filename}:")
            print(f"   Размер файла: {file_size:,} байт")
            print(f"   Хеш: {file_hash}")
            if 'error' not in image_info:
                print(f"   Размер изображения: {image_info['size']}")
                print(f"   Формат: {image_info['format']}")
                print(f"   Режим: {image_info['mode']}")
            else:
                print(f"   Ошибка: {image_info['error']}")
            print()
    
    # Проверим на дубликаты
    hashes = [img['hash'] for img in images]
    unique_hashes = set(hashes)
    
    if len(unique_hashes) == len(images):
        print("✅ Все изображения уникальны!")
    else:
        print("⚠️  Найдены дубликаты:")
        for i, img in enumerate(images):
            if hashes.count(img['hash']) > 1:
                print(f"   {img['filename']} (дубликат)")

def main():
    """Основная функция"""
    print("🖼️  Проверка изображений товаров")
    print("=" * 50)
    
    # Проверим основные товары
    products = [
        'APP-001-IPHONE15PR',
        'APP-002-MACBOOKAIR',
        'SON-003-PLAYSTATIO',
        'APP-004-AIRPODSPRO'
    ]
    
    for sku in products:
        check_product_images(sku)
        print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Создать пример Excel файла с товарами, описаниями и изображениями
"""

from excel_handler import ExcelHandler
import json

def create_sample_products_excel():
    """Создать Excel файл с примерами товаров"""
    
    excel_handler = ExcelHandler()
    
    # Создать шаблон
    template_data = excel_handler.create_products_template()
    
    # Сохранить в файл
    with open('sample_products_with_descriptions.xlsx', 'wb') as f:
        f.write(template_data)
    
    print("✅ Создан файл: sample_products_with_descriptions.xlsx")
    print("📋 Откройте файл и заполните данные согласно примерам")

if __name__ == "__main__":
    create_sample_products_excel()

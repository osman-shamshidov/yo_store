#!/usr/bin/env python3
"""
Проверка структуры Excel файла для диагностики проблем с загрузкой
"""
import pandas as pd
import sys
import os

def check_excel_file(file_path):
    """Проверить структуру Excel файла"""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return
    
    print(f"📄 Проверка файла: {file_path}\n")
    
    try:
        # Читаем все листы
        excel_file = pd.ExcelFile(file_path)
        print(f"📋 Листы в файле: {excel_file.sheet_names}\n")
        
        # Проверяем каждый лист
        for sheet_name in excel_file.sheet_names:
            print(f"━━━ Лист: {sheet_name} ━━━")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"Количество строк: {len(df)}")
            print(f"Количество колонок: {len(df.columns)}\n")
            
            print("Колонки в файле:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")
            
            print("\nОжидаемые колонки для товаров:")
            expected_cols = [
                'Название товара*',
                'Основная категория (level0)*',
                'Подкатегория (level1)*',
                'Детальная категория (level2)*',
                'Цена*'
            ]
            for col in expected_cols:
                status = "✅" if col in df.columns else "❌"
                print(f"  {status} {col}")
            
            print("\nПервые 3 строки данных:")
            print(df.head(3).to_string())
            print("\n" + "="*80 + "\n")
            
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ищем файл с похожим именем
    file_name = "Фид_для_сайта__с25_ультра,_с24_ультра.xlsx"
    
    # Проверяем текущую директорию
    if os.path.exists(file_name):
        check_excel_file(file_name)
    else:
        # Ищем файлы с похожими именами
        current_dir = os.getcwd()
        files = [f for f in os.listdir(current_dir) if f.endswith('.xlsx') and 'фид' in f.lower()]
        if files:
            print(f"Найдены файлы: {files}\n")
            for f in files:
                check_excel_file(f)
        else:
            print(f"❌ Файл {file_name} не найден в текущей директории")
            print(f"Текущая директория: {current_dir}")


"""
Модуль для работы с Excel файлами (XLSX) в Yo Store
"""

import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import io

class ExcelHandler:
    """Класс для работы с Excel файлами"""
    
    def __init__(self):
        self.product_columns = [
            'name', 'category_id', 'description', 'brand', 'model', 
            'price', 'currency', 'stock', 'image_url', 'specifications'
        ]
        
        self.price_columns = [
            'product_id', 'name', 'price', 'old_price', 'currency'
        ]
    
    def create_products_template(self) -> bytes:
        """Создать шаблон Excel файла для добавления товаров"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Товары"
        
        # Заголовки
        headers = [
            'Название товара*', 'ID категории*', 'Описание', 'Бренд', 'Модель',
            'Цена*', 'Валюта', 'Количество на складе', 'URL изображения', 'Характеристики (JSON)'
        ]
        
        # Добавить заголовки
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Добавить примеры данных
        examples = [
            ['iPhone 15 Pro', 1, 'Новейший iPhone с титановым корпусом', 'Apple', 'iPhone 15 Pro', 
             89990, 'RUB', 10, 'https://example.com/iphone.jpg', '{"color": "Titanium", "storage": "256GB"}'],
            ['MacBook Pro M3', 2, 'Мощный ноутбук для профессионалов', 'Apple', 'MacBook Pro M3', 
             199990, 'RUB', 5, 'https://example.com/macbook.jpg', '{"screen": "14 inch", "ram": "16GB"}']
        ]
        
        for row, example in enumerate(examples, 2):
            for col, value in enumerate(example, 1):
                ws.cell(row=row, column=col, value=value)
        
        # Добавить лист с категориями
        categories_ws = wb.create_sheet("Категории")
        categories_ws.append(['ID', 'Название', 'Описание', 'Иконка'])
        
        categories_data = [
            [1, 'Телефоны', 'Смартфоны и мобильные телефоны', '📱'],
            [2, 'Ноутбуки', 'Портативные компьютеры', '💻'],
            [3, 'Игровые приставки', 'Игровые консоли', '🎮'],
            [4, 'Наушники', 'Аудио устройства', '🎧'],
            [5, 'Планшеты', 'Планшетные компьютеры', '📱'],
            [6, 'Умные колонки', 'Голосовые помощники', '🔊'],
            [7, 'Телевизоры', 'Телевизионные панели', '📺'],
            [8, 'Умные часы', 'Носимые устройства', '⌚']
        ]
        
        for category in categories_data:
            categories_ws.append(category)
        
        # Стилизация листа категорий
        for col in range(1, 5):
            cell = categories_ws.cell(row=1, column=col)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Автоподбор ширины колонок
        for ws in wb.worksheets:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Сохранить в байты
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def create_prices_template(self) -> bytes:
        """Создать шаблон Excel файла для обновления цен"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Цены"
        
        # Заголовки
        headers = [
            'ID товара*', 'Название товара', 'Новая цена*', 'Старая цена', 'Валюта'
        ]
        
        # Добавить заголовки
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Добавить примеры данных
        examples = [
            [1, 'iPhone 15 Pro', 89990, 99990, 'RUB'],
            [2, 'MacBook Pro M3', 199990, 219990, 'RUB']
        ]
        
        for row, example in enumerate(examples, 2):
            for col, value in enumerate(example, 1):
                ws.cell(row=row, column=col, value=value)
        
        # Автоподбор ширины колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Сохранить в байты
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()
    
    def parse_products_excel(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсить Excel файл с товарами"""
        try:
            # Читаем Excel файл
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Товары')
            
            # Проверяем обязательные колонки
            required_columns = ['Название товара*', 'ID категории*', 'Цена*']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
            
            products = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row['Название товара*']) or pd.isna(row['ID категории*']) or pd.isna(row['Цена*']):
                        continue
                    
                    # Парсим характеристики
                    specifications = {}
                    if not pd.isna(row.get('Характеристики (JSON)', '')):
                        try:
                            specifications = json.loads(str(row['Характеристики (JSON)']))
                        except json.JSONDecodeError:
                            specifications = {}
                    
                    product = {
                        'name': str(row['Название товара*']).strip(),
                        'category_id': int(row['ID категории*']),
                        'description': str(row.get('Описание', '')).strip(),
                        'brand': str(row.get('Бренд', '')).strip(),
                        'model': str(row.get('Модель', '')).strip(),
                        'price': float(row['Цена*']),
                        'currency': str(row.get('Валюта', 'RUB')).strip().upper(),
                        'stock': int(row.get('Количество на складе', 0)) if not pd.isna(row.get('Количество на складе', 0)) else 0,
                        'image_url': str(row.get('URL изображения', '')).strip(),
                        'specifications': specifications
                    }
                    
                    products.append(product)
                    
                except Exception as e:
                    errors.append(f"Строка {index + 2}: {str(e)}")
            
            if errors:
                raise ValueError(f"Ошибки при парсинге: {'; '.join(errors)}")
            
            return products
            
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")
    
    def parse_prices_excel(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Парсить Excel файл с ценами"""
        try:
            # Читаем Excel файл
            df = pd.read_excel(io.BytesIO(file_content), sheet_name='Цены')
            
            # Проверяем обязательные колонки
            required_columns = ['ID товара*', 'Новая цена*']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
            
            prices = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Пропускаем пустые строки
                    if pd.isna(row['ID товара*']) or pd.isna(row['Новая цена*']):
                        continue
                    
                    price_data = {
                        'product_id': int(row['ID товара*']),
                        'name': str(row.get('Название товара', '')).strip(),
                        'price': float(row['Новая цена*']),
                        'old_price': float(row.get('Старая цена', row['Новая цена*'])),
                        'currency': str(row.get('Валюта', 'RUB')).strip().upper()
                    }
                    
                    prices.append(price_data)
                    
                except Exception as e:
                    errors.append(f"Строка {index + 2}: {str(e)}")
            
            if errors:
                raise ValueError(f"Ошибки при парсинге: {'; '.join(errors)}")
            
            return prices
            
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")
    
    def export_products_to_excel(self, products: List[Dict[str, Any]]) -> bytes:
        """Экспортировать товары в Excel файл"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Товары"
        
        # Заголовки
        headers = [
            'ID', 'Название', 'Категория', 'Описание', 'Бренд', 'Модель',
            'Цена', 'Валюта', 'На складе', 'URL изображения', 'Дата создания'
        ]
        
        # Добавить заголовки
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Добавить данные
        for row, product in enumerate(products, 2):
            ws.cell(row=row, column=1, value=product.get('id', ''))
            ws.cell(row=row, column=2, value=product.get('name', ''))
            ws.cell(row=row, column=3, value=product.get('category_name', ''))
            ws.cell(row=row, column=4, value=product.get('description', ''))
            ws.cell(row=row, column=5, value=product.get('brand', ''))
            ws.cell(row=row, column=6, value=product.get('model', ''))
            ws.cell(row=row, column=7, value=product.get('price', ''))
            ws.cell(row=row, column=8, value=product.get('currency', ''))
            ws.cell(row=row, column=9, value=product.get('stock', ''))
            ws.cell(row=row, column=10, value=product.get('image_url', ''))
            ws.cell(row=row, column=11, value=product.get('created_at', ''))
        
        # Автоподбор ширины колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Сохранить в байты
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

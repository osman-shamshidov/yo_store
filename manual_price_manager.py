"""
Ручное управление ценами в Yo Store
Только через Excel файлы и API - без автоматического обновления
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product
from price_storage import get_price, set_price, get_all_prices

class ManualPriceManager:
    """Класс для ручного управления ценами через Excel файлы"""
    
    def __init__(self):
        pass
    
    def update_price_from_excel_data(self, price_data: dict, db: Session = None):
        """Обновить цену товара из данных Excel файла"""
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            # Поддерживаем как старый формат (product_id), так и новый (sku)
            product_id = price_data.get('product_id')
            sku = price_data.get('sku')
            new_price = price_data.get('price')
            old_price = price_data.get('old_price', new_price)
            currency = price_data.get('currency', 'RUB')
            
            if not new_price:
                raise ValueError("price обязательна")
            
            # Найти товар либо по ID, либо по SKU
            if product_id:
                product = db.query(Product).filter(Product.id == product_id).first()
                if not product:
                    raise ValueError(f"Товар с ID {product_id} не найден")
            elif sku:
                product = db.query(Product).filter(Product.sku == sku).first()
                if not product:
                    raise ValueError(f"Товар с SKU '{sku}' не найден")
            else:
                raise ValueError("Необходимо указать либо product_id, либо sku")
            
            # Получаем текущую цену из JSON файла
            existing_price = get_price(product.sku)
            
            # Сохраняем is_parse из существующей записи
            is_parse = existing_price.get('is_parse', True) if existing_price else True
            
            # Вычисляем old_price: если цена изменилась, сохраняем старую цену
            if existing_price and existing_price.get('price') != new_price:
                old_price_to_save = existing_price.get('price')
            else:
                old_price_to_save = old_price
            
            # Обновляем или создаем цену в JSON файле
            # discount_percentage вычисляется автоматически из old_price и price
            set_price(
                sku=product.sku,
                    price=new_price,
                old_price=old_price_to_save,
                    currency=currency,
                is_parse=is_parse
                )
            
            # История цен удалена из новой структуры БД
            
            print(f"✅ Обновлена цена для {product.name}: {old_price} -> {new_price} {currency}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления цены: {e}")
            return False
        finally:
            if should_close:
                db.close()
    
    def load_prices_from_json_file(self, file_path: str):
        """Загрузить цены из JSON файла (для совместимости)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                price_data = json.load(f)
            
            db = SessionLocal()
            try:
                updated_count = 0
                errors = []
                
                for i, item in enumerate(price_data):
                    try:
                        success = self.update_price_from_excel_data(item, db)
                        if success:
                            updated_count += 1
                        else:
                            errors.append(f"Строка {i+1}: Не удалось обновить цену")
                    except Exception as e:
                        errors.append(f"Строка {i+1}: {str(e)}")
                
                db.commit()
                print(f"✅ Загружено цен из файла: {updated_count}")
                if errors:
                    print(f"⚠️ Ошибки: {errors}")
                
                return updated_count, errors
                
            except Exception as e:
                print(f"❌ Ошибка загрузки цен из файла: {e}")
                db.rollback()
                return 0, [str(e)]
            finally:
                db.close()
                
        except FileNotFoundError:
            print(f"❌ Файл цен не найден: {file_path}")
            return 0, [f"Файл {file_path} не найден"]
        except json.JSONDecodeError:
            print(f"❌ Неверный JSON в файле цен: {file_path}")
            return 0, [f"Неверный JSON в файле {file_path}"]
    
    # Функция get_price_history удалена - история цен больше не хранится в БД
    
    def get_all_current_prices(self):
        """Получить все текущие цены с информацией о товарах"""
        db = SessionLocal()
        try:
            # Получаем все товары
            products = db.query(Product).filter(Product.is_available == True).all()
            
            # Получаем все цены из JSON файла
            all_prices = get_all_prices()
            
            prices = []
            for product in products:
                price_data = all_prices.get(product.sku)
                if price_data:
                    prices.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'sku': product.sku,
                        'current_price': price_data.get('price', 0.0),
                        'old_price': price_data.get('old_price', 0.0),
                        'discount_percentage': price_data.get('discount_percentage', 0.0),
                        'currency': price_data.get('currency', 'RUB'),
                        'last_updated': price_data.get('updated_at', None)
                    })
            
            return prices
        finally:
            db.close()

# Глобальный экземпляр для использования в API
manual_price_manager = ManualPriceManager()

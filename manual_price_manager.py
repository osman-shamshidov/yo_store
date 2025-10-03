"""
Ручное управление ценами в Yo Store
Только через Excel файлы и API - без автоматического обновления
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Product, CurrentPrice, PriceHistory

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
            product_id = price_data.get('product_id')
            new_price = price_data.get('price')
            old_price = price_data.get('old_price', new_price)
            currency = price_data.get('currency', 'RUB')
            
            if not product_id or not new_price:
                raise ValueError("product_id и price обязательны")
            
            # Найти товар
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Товар с ID {product_id} не найден")
            
            # Найти текущую цену
            current_price = db.query(CurrentPrice).filter(
                CurrentPrice.product_id == product_id
            ).first()
            
            if current_price:
                # Обновить существующую цену
                current_price.old_price = current_price.price
                current_price.price = new_price
                current_price.currency = currency
                current_price.updated_at = datetime.utcnow()
                
                # Рассчитать скидку
                if current_price.old_price > current_price.price:
                    current_price.discount_percentage = round(
                        ((current_price.old_price - current_price.price) / current_price.old_price) * 100, 2
                    )
                else:
                    current_price.discount_percentage = 0.0
            else:
                # Создать новую цену
                new_price_record = CurrentPrice(
                    product_id=product_id,
                    price=new_price,
                    old_price=old_price,
                    discount_percentage=0.0,
                    currency=currency,
                    updated_at=datetime.utcnow()
                )
                db.add(new_price_record)
            
            # Добавить в историю цен
            price_history = PriceHistory(
                product_id=product_id,
                price=new_price,
                old_price=old_price,
                updated_at=datetime.utcnow()
            )
            db.add(price_history)
            
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
    
    def get_price_history(self, product_id: int, limit: int = 10):
        """Получить историю цен товара"""
        db = SessionLocal()
        try:
            history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product_id
            ).order_by(PriceHistory.updated_at.desc()).limit(limit).all()
            
            return [
                {
                    'price': h.price,
                    'old_price': h.old_price,
                    'updated_at': h.updated_at.isoformat()
                }
                for h in history
            ]
        finally:
            db.close()
    
    def get_all_current_prices(self):
        """Получить все текущие цены с информацией о товарах"""
        db = SessionLocal()
        try:
            results = db.query(Product, CurrentPrice).join(
                CurrentPrice, Product.id == CurrentPrice.product_id
            ).filter(Product.is_available == True).all()
            
            prices = []
            for product, price in results:
                prices.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_price': price.price,
                    'old_price': price.old_price,
                    'discount_percentage': price.discount_percentage,
                    'currency': price.currency,
                    'last_updated': price.updated_at.isoformat() if price.updated_at else None
                })
            
            return prices
        finally:
            db.close()

# Глобальный экземпляр для использования в API
manual_price_manager = ManualPriceManager()

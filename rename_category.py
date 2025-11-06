#!/usr/bin/env python3
"""
Скрипт для переименования категории "Портативные колонки" в "Умные колонки"
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Product, Category, SkuVariant
from config import Config
from datetime import datetime

def rename_category():
    """Переименовать категорию 'Портативные колонки' в 'Умные колонки'"""
    engine = create_engine(Config.DATABASE_URL)
    with Session(engine) as session:
        old_name = "Портативные колонки"
        new_name = "Умные колонки"
        
        print(f"🔄 Переименование категории '{old_name}' в '{new_name}'...\n")
        
        # 1. Обновляем товары (products)
        products = session.query(Product).filter(Product.level_0 == old_name).all()
        products_count = len(products)
        if products_count > 0:
            for product in products:
                product.level_0 = new_name
                product.updated_at = datetime.utcnow()
            print(f"✅ Обновлено товаров в таблице products: {products_count}")
        else:
            print(f"ℹ️  Товаров с категорией '{old_name}' не найдено")
        
        # 2. Обновляем категории (categories)
        categories = session.query(Category).filter(Category.level_0 == old_name).all()
        categories_count = len(categories)
        if categories_count > 0:
            for category in categories:
                category.level_0 = new_name
            print(f"✅ Обновлено категорий в таблице categories: {categories_count}")
        else:
            print(f"ℹ️  Категорий с названием '{old_name}' не найдено")
        
        # 3. Обновляем варианты SKU (sku_variant)
        sku_variants = session.query(SkuVariant).filter(SkuVariant.level_0 == old_name).all()
        sku_variants_count = len(sku_variants)
        if sku_variants_count > 0:
            for variant in sku_variants:
                variant.level_0 = new_name
            print(f"✅ Обновлено вариантов SKU в таблице sku_variant: {sku_variants_count}")
        else:
            print(f"ℹ️  Вариантов SKU с категорией '{old_name}' не найдено")
        
        # Сохраняем изменения
        try:
            session.commit()
            print(f"\n✅ Переименование завершено успешно!")
            print(f"   Всего обновлено записей: {products_count + categories_count + sku_variants_count}")
        except Exception as e:
            session.rollback()
            print(f"\n❌ Ошибка при сохранении изменений: {e}")
            raise

if __name__ == "__main__":
    rename_category()


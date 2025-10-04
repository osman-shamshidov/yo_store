from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from database import get_db
from models import Product, Category, CurrentPrice
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import io
from excel_handler import ExcelHandler
from manual_price_manager import manual_price_manager

def get_product_images(product):
    """Получить массив изображений товара"""
    images = []
    
    # Сначала попробуем получить изображения из specifications
    try:
        specs = json.loads(product.specifications) if product.specifications else {}
        images_data = specs.get('images', [])
        
        for img_data in images_data:
            if isinstance(img_data, dict):
                # Новый формат: {"url": "...", "alt": "..."}
                images.append(img_data["url"])
            elif isinstance(img_data, str):
                # Новый формат: массив строк
                images.append(img_data)
                
    except json.JSONDecodeError:
        pass
    
    # Если не нашли в specifications, пробуем старое поле images
    if not images:
        try:
            images_data = json.loads(product.images) if product.images else []
            for img_data in images_data:
                if isinstance(img_data, dict):
                    images.append(img_data["url"])
                elif isinstance(img_data, str):
                    images.append(img_data)
        except json.JSONDecodeError:
            pass
    
    # Если нет множественных изображений, используем основное
    if not images and product.image_url:
        images = [product.image_url]
    
    return images

def parse_images_from_string(images_str: str) -> List[str]:
    """Парсить строку изображений разделенных запятыми в JSON массив"""
    if not images_str or not images_str.strip():
        return []
    
    # Разделяем по запятой и очищаем от пробелов
    image_urls = [url.strip() for url in str(images_str).split(',') if url.strip()]
    
    # Конвертируем в JSON массив строк
    return json.dumps(image_urls)

app = FastAPI(title="Yo Store API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for API
class ProductResponse(BaseModel):
    id: int
    sku: str  # Уникальный SKU товара
    name: str
    description: str
    brand: str
    model: str
    category_name: str
    image_url: str
    images: List[str] = []  # Массив изображений
    specifications: dict
    price: float
    old_price: float
    discount_percentage: float
    currency: str
    
    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    product_count: int
    parent_category_id: Optional[int] = None
    brand: Optional[str] = None
    is_subcategory: bool = False
    subcategories: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True

class ProductDetailResponse(BaseModel):
    id: int
    sku: str  # Уникальный SKU товара
    name: str
    description: str
    brand: str
    model: str
    category_name: str
    image_url: str
    images: List[str] = []  # Массив изображений
    specifications: dict
    price: float
    old_price: float
    discount_percentage: float
    currency: str
    is_available: bool
    created_at: str
    
    class Config:
        from_attributes = True

# API Routes
@app.get("/")
async def root():
    return {"message": "Yo Store API", "version": "1.0.0"}

@app.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all main categories with product counts and subcategories"""
    # Получить только основные категории (не подкатегории)
    main_categories = db.query(Category).filter(
        Category.parent_category_id == None
    ).all()
    
    result = []
    for category in main_categories:
        # Получить подкатегории сначала
        subcategories = db.query(Category).filter(
            Category.parent_category_id == category.id
        ).all()
        
        # Подсчитать товары в основной категории + всех подкатегориях
        subcategory_ids = [subcat.id for subcat in subcategories]
        subcategory_ids.append(category.id)  # Включаем основную категорию
        
        product_count = db.query(Product).filter(
            Product.category_id.in_(subcategory_ids)
        ).count()
        
        subcategory_responses = []
        for subcat in subcategories:
            subcat_product_count = db.query(Product).filter(
                Product.category_id == subcat.id
            ).count()
            
            subcategory_responses.append(CategoryResponse(
                id=subcat.id,
                name=subcat.name,
                description=subcat.description,
                icon=subcat.icon,
                product_count=subcat_product_count,
                parent_category_id=subcat.parent_category_id,
                brand=subcat.brand,
                is_subcategory=subcat.is_subcategory,
                subcategories=[]
            ))
        
        result.append(CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            icon=category.icon,
            product_count=product_count,
            parent_category_id=category.parent_category_id,
            brand=category.brand,
            is_subcategory=category.is_subcategory,
            subcategories=subcategory_responses
        ))
    
    return result

@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    level0: Optional[str] = None,
    level1: Optional[str] = None,
    level2: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get unique product models (grouped by level2) with optional hierarchical filters"""
    # Простая логика: получаем все товары, затем группируем в Python
    query = db.query(Product, CurrentPrice).outerjoin(
        CurrentPrice, Product.id == CurrentPrice.product_id
    )
    
    # Применяем фильтры
    filters = []
    
    if brand:
        filters.append(Product.brand == brand)
    if level0:
        filters.append(Product.level0 == level0)
    if level1:
        filters.append(Product.level1 == level1)
    if level2:
        filters.append(Product.level2 == level2)
    if model:
        filters.append(Product.model == model)
        
    # Применяем старую логику categories только для обратной совместимости
    if category_id and not (level0 or level1 or level2):
        # Если указана только категория, ищем товары в основной категории и всех подкатегориях
        subcategory_ids = db.query(Category.id).filter(
            Category.parent_category_id == category_id
        ).all()
        
        category_ids = [category_id] + [subcat[0] for subcat in subcategory_ids]
        filters.append(Product.category_id.in_(category_ids))
    elif category_id and brand and not (level0 or level1 or level2):
        # Если указаны и категория, и бренд, ищем товары в подкатегориях этой категории с нужным брендом
        subcategory_ids = db.query(Category.id).filter(
            and_(
                Category.parent_category_id == category_id,
                Category.brand == brand,
                Category.is_subcategory == True
            )
        ).all()
        
        if subcategory_ids:
            subcategory_id_list = [subcat[0] for subcat in subcategory_ids]
            filters.append(Product.category_id.in_(subcategory_id_list))
        else:
            # Если подкатегория не найдена, возвращаем пустой результат
            filters.append(Product.id == -1)  # Невозможный ID
    
    # Применяем фильтры
    if filters:
        query = query.filter(and_(*filters))
    
    # Используем подкеру для получения одного представительного товара из каждой модели
    subquery = db.query(
        func.min(Product.id).label('id')
    ).filter(*filters).group_by(Product.model, Product.brand).subquery()
    
    # Теперь получаем только те товары, которые являются представителями групп
    final_query = db.query(Product, CurrentPrice).outerjoin(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).outerjoin(subquery, Product.id == subquery.c.id).filter(
        subquery.c.id.isnot(None)
    ).order_by(Product.model, Product.id)
    
    # Применяем лимит и отступ
    results = final_query.offset(offset).limit(limit).all()
    
    products = []
    for result in results:
        product = result[0]  # Product


        price = result[1]    # CurrentPrice или None
        
        # Если цена отсутствует, используем значения по умолчанию
        if price is None:
            price_obj = type('Price', (), {
                'price': 0.0,
                'old_price': 0.0,
                'discount_percentage': 0.0,
                'currency': 'RUB'
            })()
        else:
            price_obj = price
        
        try:
            specifications = json.loads(product.specifications) if product.specifications else {}
        except json.JSONDecodeError:
            specifications = {}
        
        images = get_product_images(product)
        
        # Получаем название категории из level полей или используем старое поле
        category_name = product.level0 or "Без категории"
        if product.level1:
            category_name += f" / {product.level1}"
        if product.level2:
            category_name += f" / {product.level2}"
        
        products.append(ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            brand=product.brand,
            model=product.model,
            category_name=category_name,
            image_url=images[0] if images else (product.image_url or ''),
            images=images,
            specifications=specifications,
            price=price_obj.price,
            old_price=price_obj.old_price,
            discount_percentage=price_obj.discount_percentage,
            currency=price_obj.currency,
        ))
    
    return products

@app.get("/products/{model}/variants")
async def get_model_variants(model: str, db: Session = Depends(get_db)):
    """Get all variants and their prices for a specific model"""
    
    # Сначала попробуем найти основной продукт с полными спецификациями
    main_product = db.query(Product).filter(
        Product.model == model,
        Product.specifications.like('%variants%')
    ).first()
    
    if main_product:
        # Найден основной продукт с вложенными вариантами
        specifications = {}
        try:
            if main_product.specifications:
                specifications = json.loads(main_product.specifications)
        except json.JSONDecodeError:
            pass
        
        variants = []
        
        # Извлекаем варианты из specifications.variants
        if 'variants' in specifications:
            # Сортируем варианты по цвету (в алфавитном порядке)
            sorted_variants = sorted(specifications['variants'], key=lambda x: x.get('specifications', {}).get('color', ''))
            
            for variant_info in sorted_variants:
                # Находим цену для этого варианта по SKU
                variant_product = db.query(Product).filter(Product.sku == variant_info['sku']).first()
                price = None
                if variant_product:
                    price = db.query(CurrentPrice).filter(CurrentPrice.product_id == variant_product.id).first()
                
                variant_specs = variant_info.get('specifications', {})
                
                # Получаем изображения для цвета из основного продукта
                variant_color = variant_specs.get('color', '')
                variant_color_normalized = variant_color.lower().replace(' ', '-')
                variant_images = []
                
                if 'images' in specifications:
                    for img_info in specifications['images']:
                        if isinstance(img_info, dict) and 'color' in img_info:
                            img_color = img_info.get('color', '').lower()
                            if img_color == variant_color_normalized:
                                variant_images.append(img_info.get('url', ''))
                        elif isinstance(img_info, str):
                            # Прямой URL - пытаемся определить цвет из пути
                            img_path = img_info.lower()
                            if variant_color_normalized in img_path:
                                variant_images.append(img_info)
                
                variant_data = {
                    "sku": variant_info['sku'],
                    "name": variant_info['name'],
                    "price": price.price if price else 0.0,
                    "old_price": price.old_price if price else 0.0,
                    "discount_percentage": price.discount_percentage if price else 0.0,
                    "currency": price.currency if price else "RUB",
                    "stock": variant_info.get('stock', 0),
                    "is_available": variant_info.get('is_available', True),
                    
                    # Добавляем спецификации варианта
                    "color": variant_specs.get('color', ''),
                    "memory": variant_specs.get('memory', ''),
                    "sim_type": variant_specs.get('sim_type', ''),
                    
                    # Изображения для этого цвета
                    "images": variant_images,
                    "main_image": variant_images[0] if variant_images else ""
                }
                
                variants.append(variant_data)
        
        return {
            "model": model,
            "variants": variants,
            "total_variants": len(variants)
        }
    
    # Fallback: Если основного продукта нет, найдем все варианты для данной модели
    variants_query = db.query(Product, CurrentPrice).outerjoin(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).filter(Product.model == model).order_by(Product.specifications)  # Сортируем по specifications
    
    variants = []
    for result in variants_query.all():
        product = result[0]
        price = result[1]
        
        # Получаем спецификации варианта
        specifications = {}
        try:
            if product.specifications:
                specifications = json.loads(product.specifications)
        except json.JSONDecodeError:
            pass
        
        # Получаем изображения
        images = get_product_images(product)
        
        variant_data = {
            "sku": product.sku,
            "name": product.name,
            "price": price.price if price else 0.0,
            "old_price": price.old_price if price else 0.0,
            "discount_percentage": price.discount_percentage if price else 0.0,
            "currency": price.currency if price else "RUB",
            "stock": product.stock,
            "is_available": product.is_available,
            
            # Добавляем спецификации варианта (цвет, память, SIM)
            "color": specifications.get('color', ''),
            "memory": specifications.get('memory', ''),
            "sim_type": specifications.get('sim_type', ''),
            
            # Изображения для этого варианта (один цвет обычно)
            "images": images,
            "main_image": images[0] if images else ""
        }
        
        variants.append(variant_data)
    
    # Сортируем варианты по цвету для fallback случая
    variants.sort(key=lambda x: x.get('color', ''))
    
    return {
        "model": model,
        "variants": variants,
        "total_variants": len(variants)
    }

@app.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get detailed product information"""
    result = db.query(Product, CurrentPrice, Category).join(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).join(Category, Product.category_id == Category.id).filter(
        Product.id == product_id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product, price, category = result
    
    try:
        specifications = json.loads(product.specifications) if product.specifications else {}
    except json.JSONDecodeError:
        specifications = {}
    
    images = get_product_images(product)
    
    return ProductDetailResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        brand=product.brand,
        model=product.model,
        category_name=category.name,
        image_url=product.image_url or '',
        images=images,
        specifications=specifications,
        price=price.price,
        old_price=price.old_price,
        discount_percentage=price.discount_percentage,
        currency=price.currency,
        is_available=product.is_available,
        created_at=product.created_at.isoformat()
    )

@app.get("/search")
async def search_products(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search products by name, brand, or model"""
    search_term = f"%{q}%"
    
    results = db.query(Product, CurrentPrice, Category).join(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).join(Category, Product.category_id == Category.id).filter(
        and_(
            Product.is_available == True,
            (
                Product.name.ilike(search_term) |
                Product.brand.ilike(search_term) |
                Product.model.ilike(search_term)
            )
        )
    ).order_by(Product.name.desc()).limit(limit).all()
    
    products = []
    for product, price, category in results:
        try:
            specifications = json.loads(product.specifications) if product.specifications else {}
        except json.JSONDecodeError:
            specifications = {}
        
        images = get_product_images(product)
        
        products.append(ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            brand=product.brand,
            model=product.model,
            category_name=category.name,
            image_url=images[0] if images else (product.image_url or ''),
            images=images,
            specifications=specifications,
            price=price.price,
            old_price=price.old_price,
            discount_percentage=price.discount_percentage,
            currency=price.currency,
        ))
    
    return products

@app.get("/webapp")
async def webapp():
    """Serve the web app"""
    return FileResponse("webapp.html")

@app.get("/admin")
async def admin():
    """Serve the admin panel"""
    return FileResponse("admin.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Excel Management API
@app.get("/api/excel/template/products")
async def download_products_template():
    """Скачать шаблон Excel файла для добавления товаров"""
    excel_handler = ExcelHandler()
    template_data = excel_handler.create_products_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_template.xlsx"}
    )

@app.get("/api/excel/template/prices")
async def download_prices_template():
    """Скачать шаблон Excel файла для обновления цен"""
    excel_handler = ExcelHandler()
    template_data = excel_handler.create_prices_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=prices_template.xlsx"}
    )

@app.post("/api/excel/import/products")
async def import_products_from_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Импортировать товары из Excel файла"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel (.xlsx или .xls)")
    
    try:
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Парсим Excel файл
        excel_handler = ExcelHandler()
        products_data = excel_handler.parse_products_excel(file_content)
        
        # Добавляем товары в базу данных
        added_count = 0
        errors = []
        
        for i, product_data in enumerate(products_data):
            try:
                # Проверить существование категории
                category = db.query(Category).filter(Category.id == product_data['category_id']).first()
                if not category:
                    errors.append(f"Товар {i+1}: Категория с ID {product_data['category_id']} не найдена")
                    continue
                
                # Создать товар
                parsed_images = parse_images_from_string(product_data['image_url'])
                first_image = product_data['image_url'].split(',')[0].strip() if product_data['image_url'] else None
                
                db_product = Product(
                    name=product_data['name'],
                    category_id=product_data['category_id'],
                    description=product_data['description'],
                    brand=product_data['brand'],
                    model=product_data['model'],
                    image_url=first_image,  # Legacy поле - берем первый URL
                    images=parsed_images,  # Новое поле - JSON массив всех изображений
                    specifications=json.dumps(product_data['specifications']),
                    stock=product_data['stock'],
                    is_available=True
                )
                
                db.add(db_product)
                db.flush()  # Получить ID
                
                # Создать начальную цену
                db_price = CurrentPrice(
                    product_id=db_product.id,
                    price=product_data['price'],
                    old_price=product_data['price'],
                    discount_percentage=0.0,
                    currency=product_data['currency'],
                    updated_at=datetime.utcnow()
                )
                
                db.add(db_price)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Товар {i+1}: {str(e)}")
        
        db.commit()
        
        return {
            "message": "Импорт завершен",
            "added": added_count,
            "errors": errors,
            "total_processed": len(products_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при импорте: {str(e)}")

@app.post("/api/excel/import/prices")
async def import_prices_from_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Обновить цены из Excel файла"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel (.xlsx или .xls)")
    
    try:
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Парсим Excel файл
        excel_handler = ExcelHandler()
        prices_data = excel_handler.parse_prices_excel(file_content)
        
        # Обновляем цены в базе данных через ручной менеджер
        updated_count = 0
        errors = []
        
        for i, price_data in enumerate(prices_data):
            try:
                success = manual_price_manager.update_price_from_excel_data(price_data, db)
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Строка {i+1}: Не удалось обновить цену")
            except Exception as e:
                errors.append(f"Строка {i+1}: {str(e)}")
        
        db.commit()
        
        return {
            "message": "Обновление цен завершено",
            "updated": updated_count,
            "errors": errors,
            "total_processed": len(prices_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении цен: {str(e)}")

@app.get("/api/excel/export/products")
async def export_products_to_excel(db: Session = Depends(get_db)):
    """Экспортировать все товары в Excel файл"""
    try:
        # Получить все товары с ценами и категориями
        results = db.query(Product, CurrentPrice, Category).outerjoin(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).outerjoin(Category, Product.category_id == Category.id).all()
        
        products_data = []
        for product, price, category in results:
            try:
                specifications = json.loads(product.specifications) if product.specifications else {}
            except json.JSONDecodeError:
                specifications = {}
            
            # Получить массив изображений используя существующую функцию
            images = get_product_images(product)
            
            products_data.append({
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'category_name': category.name if category else '',
                'level0': product.level0,
                'level1': product.level1,
                'level2': product.level2,
                'description': product.description or '',
                'brand': product.brand,
                'model': product.model or '',
                'price': price.price if price else 0.0,
                'old_price': price.old_price if price else price.price if price else 0.0,
                'currency': price.currency if price else 'RUB',
                'discount_percentage': price.discount_percentage if price else 0.0,
                'stock': product.stock,
                'image_text': ' | '.join(images) if images else product.image_url or '',
                'images_count': len(images),
                'is_available': product.is_available,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
            })
        
        # Создать Excel файл
        excel_handler = ExcelHandler()
        excel_data = excel_handler.export_products_to_excel(products_data)
        
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=products_export.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при экспорте: {str(e)}")

# Additional Price Management API
@app.get("/api/prices/current")
async def get_current_prices():
    """Получить все текущие цены"""
    try:
        prices = manual_price_manager.get_all_current_prices()
        return {
            "message": "Текущие цены получены",
            "prices": prices,
            "total": len(prices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения цен: {str(e)}")

@app.get("/api/prices/history/{product_id}")
async def get_price_history(product_id: int, limit: int = 10):
    """Получить историю цен товара"""
    try:
        history = manual_price_manager.get_price_history(product_id, limit)
        return {
            "message": f"История цен товара {product_id}",
            "product_id": product_id,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории цен: {str(e)}")

@app.post("/api/prices/update-single")
async def update_single_price(
    product_id: int,
    new_price: float,
    currency: str = "RUB",
    db: Session = Depends(get_db)
):
    """Обновить цену одного товара"""
    try:
        price_data = {
            'product_id': product_id,
            'price': new_price,
            'currency': currency
        }
        
        success = manual_price_manager.update_price_from_excel_data(price_data, db)
        
        if success:
            db.commit()
            return {
                "message": "Цена успешно обновлена",
                "product_id": product_id,
                "new_price": new_price,
                "currency": currency
            }
        else:
            raise HTTPException(status_code=400, detail="Не удалось обновить цену")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка обновления цены: {str(e)}")

@app.get("/product-images/{model_key}/{color}")
async def get_product_images_by_color(model_key: str, color: str):
    """Get images for a specific product color"""
    import os
    
    model_key_mapping = {
        'iphone-16': 'IPHONE16',
        'iphone-16-pro': 'IPHONE16Pro', 
        'iphone-16-pro-max': 'IPHONE16ProMax',
        'iphone-17-pro': 'IPHONE17Pro',
        'iphone-17-pro-max': 'IPHONE17ProMax',
        'macbook-air-m2': 'MACBOOKAirM2',
        'ipad-air': 'IPADAir',
        'airpods-pro2': 'AIRPODSPro2',
        'homepod-mini': 'HOMEPODmini',
        'samsung': 'SAM',
        'google': 'GOO',
        'lenovo': 'LEN',
        'asus': 'ASU'
    }
    actual_model_key = model_key_mapping.get(model_key, model_key.upper())
    
    try:
        # Определяем папку с изображениями на основе model_key и цвета
        image_folder = f"static/images/products/{actual_model_key}/{color}"
        
        # Проверяем существование папки
        if not os.path.exists(image_folder):
            raise HTTPException(status_code=404, detail=f"Папка изображений не найдена: {image_folder}")
        
        # Формируем пути к реальным файлам
        image_paths = []
        try:
            # Получаем список всех файлов в папке
            all_files = os.listdir(image_folder)
            # Фильтруем только jpg файлы
            jpg_files = [f for f in all_files if f.endswith('.jpg')]
            # Сортируем файлы по имени
            jpg_files.sort()
            
            # Формируем пути к изображениям
            for file_name in jpg_files:
                image_path = f"/static/images/products/{actual_model_key}/{color}/{file_name}"
                image_paths.append(image_path)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка чтения папки: {str(e)}")
                
        return {"image_paths": image_paths}
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Изображения не найдены: {str(e)}")

@app.get("/color-schemes/{model_key}")
async def get_color_schemes(model_key: str):
    """Get color schemes for a product"""
    model_key_mapping = {
        'iphone-16': 'IPHONE16',
        'iphone-16-pro': 'IPHONE16Pro', 
        'iphone-16-pro-max': 'IPHONE16ProMax',
        'iphone-17-pro': 'IPHONE17Pro',
        'iphone-17-pro-max': 'IPHONE17ProMax',
        'macbook-air-m2': 'MACBOOKAirM2',
        'ipad-air': 'IPADAir',
        'airpods-pro2': 'AIRPODSPro2',
        'homepod-mini': 'HOMEPODmini',
        'samsung': 'SAM',
        'google': 'GOO',
        'lenovo': 'LEN',
        'asus': 'ASU'
    }
    actual_key = model_key_mapping.get(model_key, model_key.upper())
    
    # Статичные данные цветов для каждой модели
    color_schemes = {
        "IPHONE16": {
            "colors": [
                {"value": "ultramarine"},
                {"value": "black"},
                {"value": "white"},
                {"value": "pink"},
                {"value": "teal"}
            ],
            "default_color": "ultramarine"
        },
        "IPHONE16Pro": {
            "colors": [
                {"value": "titanium-black"},
                {"value": "titanium-white"},
                {"value": "titanium-natural"},
                {"value": "titanium-desert"}
            ],
            "default_color": "titanium-black"
        },
        "IPHONE16ProMax": {
            "colors": [
                {"value": "titanium-black"},
                {"value": "titanium-white"},
                {"value": "titanium-natural"},
                {"value": "titanium-desert"}
            ],
            "default_color": "titanium-black"
        },
        "MACBOOKAirM2": {
            "colors": [
                {"value": "space-gray"},
                {"value": "silver"}
            ],
            "default_color": "space-gray"
        },
        "IPADAir": {
            "colors": [
                {"value": "space-gray"},
                {"value": "blue"},
                {"value": "silver"}
            ],
            "default_color": "space-gray"
        },
        "AIRPODSPro2": {
            "colors": [
                {"value": "white"}
            ],
            "default_color": "white"
        },
        "HOMEPODmini": {
            "colors": [
                {"value": "black"},
                {"value": "white"}
            ],
            "default_color": "black"
        },
        "SAM": {
            "colors": [
                {"value": "black"},
                {"value": "silver"}
            ],
            "default_color": "black"
        },
        "GOO": {
            "colors": [
                {"value": "black"},
                {"value": "blue"},
                {"value": "white"}
            ],
            "default_color": "black"
        },
        "IPHONE17Pro": {
            "colors": [
                {"value": "deep-blue"},
                {"value": "cosmic-orange"},
                {"value": "silver"}
            ],
            "default_color": "deep-blue"
        },
        "IPHONE17ProMax": {
            "colors": [
                {"value": "deep-blue"},
                {"value": "cosmic-orange"},
                {"value": "silver"}
            ],
            "default_color": "deep-blue"
        }
    }
    
    if actual_key not in color_schemes:
        raise HTTPException(status_code=404, detail=f"Цветовая схема не найдена для {model_key}")
    
    return color_schemes[actual_key]

@app.get("/variant-schemes/{model_key}")
async def get_variant_schemes(model_key: str):
    """Get variant schemes for a product"""
    model_key_mapping = {
        'iphone-16': 'IPHONE16',
        'iphone-16-pro': 'IPHONE16Pro', 
        'iphone-16-pro-max': 'IPHONE16ProMax',
        'iphone-17-pro': 'IPHONE17Pro',
        'iphone-17-pro-max': 'IPHONE17ProMax',
        'macbook-air-m2': 'MACBOOKAirM2',
        'ipad-air': 'IPADAir',
        'airpods-pro2': 'AIRPODSPro2',
        'homepod-mini': 'HOMEPODmini',
        'samsung': 'SAM',
        'google': 'GOO',
        'lenovo': 'LEN',
        'asus': 'ASU'
    }
    actual_key = model_key_mapping.get(model_key, model_key.upper())
    
    # Статичные данные вариантов для каждой модели
    variant_schemes = {
        "IPHONE16": {
            "variants": {
                "storage": ["128GB", "256GB", "512GB"],
                "color": ["ultramarine", "black", "white", "pink", "teal"],
                "sim": ["2eSIM", "SIM+ESIM", "2SIM"]
            }
        },
        "IPHONE16Pro": {
            "variants": {
                "storage": ["256GB", "512GB", "1TB"],
                "color": ["titanium-black", "titanium-white", "titanium-natural", "titanium-desert"],
                "sim": ["2eSIM", "SIM+ESIM", "2SIM"]
            }
        },
        "IPHONE16ProMax": {
            "variants": {
                "storage": ["256GB", "512GB", "1TB"],
                "color": ["titanium-black", "titanium-white", "titanium-natural", "titanium-desert"],
                "sim": ["2eSIM", "SIM+ESIM", "2SIM"]
            }
        },
        "MACBOOKAirM2": {
            "variants": {
                "storage": ["256GB", "512GB"],
                "color": ["space-gray", "silver"]
            }
        },
        "IPADAir": {
            "variants": {
                "storage": ["64GB", "256GB"],
                "color": ["space-gray", "blue", "silver"]
            }
        },
        "AIRPODSPro2": {
            "variants": {
                "color": ["white"]
            }
        },
        "HOMEPODmini": {
            "variants": {
                "color": ["black", "white"]
            }
        },
        "IPHONE17Pro": {
            "variants": {
                "storage": ["256GB", "512GB", "1TB", "2TB"],
                "color": ["deep-blue", "cosmic-orange", "silver"],
                "sim": ["2eSIM", "SIM+ESIM", "2SIM"]
            }
        },
        "IPHONE17ProMax": {
            "variants": {
                "storage": ["256GB", "512GB", "1TB", "2TB"], 
                "color": ["deep-blue", "cosmic-orange", "silver"],
                "sim": ["2eSIM", "SIM+ESIM", "2SIM"]
            }
        }
    }
    
    if actual_key not in variant_schemes:
        raise HTTPException(status_code=404, detail=f"Схема вариантов не найдена для {model_key}")
    
    return variant_schemes[actual_key]

# Новые endpoints для иерархической фильтрации

@app.get("/hierarchy/brands")
async def get_brands(db: Session = Depends(get_db)):
    """Получить все доступные бренды"""
    brands = db.query(Product.brand.distinct()).filter(
        Product.brand.isnot(None),
        Product.is_available == True
    ).all()
    return [brand[0] for brand in brands]

@app.get("/hierarchy/levels")
async def get_hierarchy_levels(
    level: Optional[int] = None,
    brand: Optional[str] = None,
    parent_level0: Optional[str] = None,
    parent_level1: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить значения уровней иерархии
    
    level: кавой уровень получить (0, 1, или 2)
    brand: фильтр по бренду
    parent_level0: для уровня 1 - фильтр по level0
    parent_level1: для уровня 2 - фильтр по level1
    """
    
    filters = [Product.is_available == True]
    
    if brand:
        filters.append(Product.brand == brand)
    if parent_level0:
        filters.append(Product.level0 == parent_level0)
    if parent_level1:
        filters.append(Product.level1 == parent_level1)
    
    query = db.query(Product).filter(and_(*filters))
    
    if level == 0:
        # Получаем все level0
        results = query.with_entities(Product.level0.distinct()).filter(
            Product.level0.isnot(None)
        ).all()
        return [item[0] for item in results if item[0]]
        
    elif level == 1:
        # Получаем все level1
        results = query.with_entities(Product.level1.distinct()).filter(
            Product.level1.isnot(None)
        ).all()
        return [item[0] for item in results if item[0]]
        
    elif level == 2:
        # Получаем все level2
        results = query.with_entities(Product.level2.distinct()).filter(
            Product.level2.isnot(None)
        ).all()
        return [item[0] for item in results if item[0]]
    
    else:
        # Возвращаем всю иерархию
        return {
            "level0": db.query(Product.level0.distinct()).filter(
                Product.level0.isnot(None),
                Product.is_available == True
            ).all(),
            "level1": db.query(Product.level1.distinct()).filter(
                Product.level1.isnot(None),
                Product.is_available == True
            ).all(),
            "level2": db.query(Product.level2.distinct()).filter(
                Product.level2.isnot(None),
                Product.is_available == True
            ).all()
        }

@app.get("/hierarchy/models")
async def get_models(
    brand: Optional[str] = None,
    level0: Optional[str] = None,
    level1: Optional[str] = None,
    level2: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить все доступные модели с фильтрацией"""
    
    filters = [Product.is_available == True]
    
    if brand:
        filters.append(Product.brand == brand)
    if level0:
        filters.append(Product.level0 == level0)
    if level1:
        filters.append(Product.level1 == level1)
    if level2:
        filters.append(Product.level2 == level2)
    
    models = db.query(Product.model.distinct()).filter(
        and_(*filters)
    ).all()
    
    return [model[0] for model in models if model[0]]

@app.get("/hierarchy/skus")
async def get_skus_with_info(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    level0: Optional[str] = None,
    level1: Optional[str] = None,
    level2: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить SKU с детальной информацией"""
    
    filters = [Product.is_available == True]
    
    if brand:
        filters.append(Product.brand == brand)
    if model:
        filters.append(Product.model == model)
    if level0:
        filters.append(Product.level0 == level0)
    if level1:
        filters.append(Product.level1 == level1)
    if level2:
        filters.append(Product.level2 == level2)
    
    # Получаем SKU с ценами
    results = db.query(Product, CurrentPrice).join(
        CurrentPrice, Product.id == CurrentPrice.product_id,
        isouter=True
    ).filter(and_(*filters)).all()
    
    skus_info = []
    for product, price in results:
        sku_data = {
            "sku": product.sku,
            "name": product.name,
            "brand": product.brand,
            "model": product.model,
            "level0": product.level0,
            "level1": product.level1,
            "level2": product.level2,
            "price": price.price if price else 0.0,
            "currency": price.currency if price else "RUB",
            "stock": product.stock
        }
        skus_info.append(sku_data)
    
    return skus_info

if __name__ == "__main__":
    import uvicorn
    from config import Config
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
    try:
        images_data = json.loads(product.images) if product.images else []
    except json.JSONDecodeError:
        images_data = []
    
    # Извлекаем URL из объектов изображений или используем строки напрямую
    images = []
    for img_data in images_data:
        if isinstance(img_data, dict):
            # Новый формат: {"url": "...", "alt": "..."}
            images.append(img_data["url"])
        elif isinstance(img_data, str):
            # Старый формат: просто строка URL
            images.append(img_data)
    
    # Если нет множественных изображений, используем основное
    if not images and product.image_url:
        images = [product.image_url]
    
    return images

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
        # Подсчитать товары в основной категории
        product_count = db.query(Product).filter(
            Product.category_id == category.id
        ).count()
        
        # Получить подкатегории
        subcategories = db.query(Category).filter(
            Category.parent_category_id == category.id
        ).all()
        
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
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get products with optional category and brand filters"""
    query = db.query(Product, CurrentPrice, Category).join(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).join(Category, Product.category_id == Category.id)
    
    if category_id and brand:
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
            query = query.filter(Product.category_id.in_(subcategory_id_list))
        else:
            # Если подкатегория не найдена, возвращаем пустой результат
            query = query.filter(Product.id == -1)  # Невозможный ID
    elif category_id:
        # Если указана только категория, ищем товары в основной категории и всех подкатегориях
        subcategory_ids = db.query(Category.id).filter(
            Category.parent_category_id == category_id
        ).all()
        
        category_ids = [category_id] + [subcat[0] for subcat in subcategory_ids]
        query = query.filter(Product.category_id.in_(category_ids))
    elif brand:
        query = query.filter(Product.brand == brand)
    
    # Сортировка по убыванию названия (от Z до A)
    results = query.order_by(Product.name.desc()).offset(offset).limit(limit).all()
    
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
            image_url=images[0] if images else product.image_url,
            images=images,
            specifications=specifications,
            price=price.price,
            old_price=price.old_price,
            discount_percentage=price.discount_percentage,
            currency=price.currency,
        ))
    
    return products

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
        image_url=product.image_url,
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
            image_url=images[0] if images else product.image_url,
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
                db_product = Product(
                    name=product_data['name'],
                    category_id=product_data['category_id'],
                    description=product_data['description'],
                    brand=product_data['brand'],
                    model=product_data['model'],
                    image_url=product_data['image_url'],
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
        results = db.query(Product, CurrentPrice, Category).join(
            CurrentPrice, Product.id == CurrentPrice.product_id
        ).join(Category, Product.category_id == Category.id).all()
        
        products_data = []
        for product, price, category in results:
            try:
                specifications = json.loads(product.specifications) if product.specifications else {}
            except json.JSONDecodeError:
                specifications = {}
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'category_name': category.name,
                'description': product.description,
                'brand': product.brand,
                'model': product.model,
                'price': price.price,
                'currency': price.currency,
                'stock': product.stock,
                'image_url': product.image_url,
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

if __name__ == "__main__":
    import uvicorn
    from config import Config
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

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

app = FastAPI(title="Yo Store API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for API
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    brand: str
    model: str
    category_name: str
    image_url: str
    specifications: dict
    price: float
    old_price: float
    discount_percentage: float
    currency: str
    is_available: bool
    
    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    product_count: int
    
    class Config:
        from_attributes = True

class ProductDetailResponse(BaseModel):
    id: int
    name: str
    description: str
    brand: str
    model: str
    category_name: str
    image_url: str
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
    """Get all categories with product count"""
    categories = db.query(Category).filter(Category.is_active == True).all()
    
    result = []
    for category in categories:
        product_count = db.query(Product).filter(
            and_(Product.category_id == category.id, Product.is_available == True)
        ).count()
        
        result.append(CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            icon=category.icon,
            product_count=product_count
        ))
    
    return result

@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    category_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get products with optional category filter"""
    query = db.query(Product, CurrentPrice, Category).join(
        CurrentPrice, Product.id == CurrentPrice.product_id
    ).join(Category, Product.category_id == Category.id).filter(
        Product.is_available == True
    )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    results = query.offset(offset).limit(limit).all()
    
    products = []
    for product, price, category in results:
        try:
            specifications = json.loads(product.specifications) if product.specifications else {}
        except json.JSONDecodeError:
            specifications = {}
        
        products.append(ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            brand=product.brand,
            model=product.model,
            category_name=category.name,
            image_url=product.image_url,
            specifications=specifications,
            price=price.price,
            old_price=price.old_price,
            discount_percentage=price.discount_percentage,
            currency=price.currency,
            is_available=product.is_available
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
    
    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        brand=product.brand,
        model=product.model,
        category_name=category.name,
        image_url=product.image_url,
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
    ).limit(limit).all()
    
    products = []
    for product, price, category in results:
        try:
            specifications = json.loads(product.specifications) if product.specifications else {}
        except json.JSONDecodeError:
            specifications = {}
        
        products.append(ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            brand=product.brand,
            model=product.model,
            category_name=category.name,
            image_url=product.image_url,
            specifications=specifications,
            price=price.price,
            old_price=price.old_price,
            discount_percentage=price.discount_percentage,
            currency=price.currency,
            is_available=product.is_available
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

if __name__ == "__main__":
    import uvicorn
    from config import Config
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

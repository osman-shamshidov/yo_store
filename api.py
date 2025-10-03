from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
from models import Product, Category, CurrentPrice
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

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

if __name__ == "__main__":
    import uvicorn
    from config import Config
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

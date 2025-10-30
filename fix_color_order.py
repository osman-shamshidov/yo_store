#!/usr/bin/env python3
"""
Fix color wording in DB: replace 'Black Titanium' -> 'Titanium Black'
Across:
- products.specifications JSON (field 'color')
- product_images.color
"""
import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Product, ProductImage
from config import Config


MAPPINGS = {
    'black titanium': 'Titanium Black',
    'white titanium': 'Titanium White',
    'natural titanium': 'Titanium Natural',
    'desert titanium': 'Titanium Desert',
    'blue titanium': 'Titanium Desert',
}

# Model-specific mappings (apply only for certain level_2 values)
MODEL_SPECIFIC = {
    'iphone 16 pro': {
        'black': 'Titanium Black',
        'white': 'Titanium White',
    }
}


def normalize(value: str) -> str:
    return (value or '').strip()


def run() -> None:
    engine = create_engine(Config.DATABASE_URL)
    with Session(engine) as db:
        updated_products = 0
        updated_images = 0

        # Update products.specifications color (global mappings)
        products = db.query(Product).all()
        for p in products:
            if not p.specifications:
                continue
            try:
                specs = json.loads(p.specifications) if isinstance(p.specifications, str) else p.specifications
            except json.JSONDecodeError:
                continue
            color = normalize(specs.get('color', ''))
            key = color.lower()
            if key in MAPPINGS:
                specs['color'] = MAPPINGS[key]
                p.specifications = json.dumps(specs, ensure_ascii=False)
                updated_products += 1

        # Apply model-specific mappings (e.g., iPhone 16 Pro: Black -> Titanium Black)
        products = db.query(Product).all()
        for p in products:
            target_model = normalize(p.level_2).lower()
            for model_key, cmap in MODEL_SPECIFIC.items():
                if model_key in target_model:
                    try:
                        specs = json.loads(p.specifications) if isinstance(p.specifications, str) else p.specifications or {}
                    except json.JSONDecodeError:
                        continue
                    color = normalize(specs.get('color', ''))
                    ckey = color.lower()
                    if ckey in cmap:
                        specs['color'] = cmap[ckey]
                        p.specifications = json.dumps(specs, ensure_ascii=False)
                        updated_products += 1

        # Update product_images.color
        images = db.query(ProductImage).all()
        for img in images:
            color = normalize(img.color)
            key = color.lower()
            if key in MAPPINGS:
                img.color = MAPPINGS[key]
                updated_images += 1

        db.commit()
        print(f"Updated products: {updated_products}, product_images: {updated_images}")


if __name__ == '__main__':
    run()



#!/usr/bin/env python3
import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Product, ProductImage
from config import Config

def normalize(value: str) -> str:
    return (value or '').strip()

engine = create_engine(Config.DATABASE_URL)
with Session(engine) as db:
    colors = set()
    for p in db.query(Product).all():
        if not p.specifications:
            continue
        try:
            specs = json.loads(p.specifications) if isinstance(p.specifications, str) else p.specifications
        except json.JSONDecodeError:
            continue
        c = normalize(specs.get('color', ''))
        if c:
            colors.add(c)
    for img in db.query(ProductImage).all():
        c = normalize(img.color)
        if c:
            colors.add(c)

    out = sorted(colors, key=lambda s: s.lower())
    for c in out:
        print(c)

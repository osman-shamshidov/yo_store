#!/usr/bin/env python3
"""
Populate missing Level2Description rows for distinct Product.level_2.
Generates concise description and structured details heuristically by product family.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Product, Level2Description
from datetime import datetime
import json
from config import Config
from typing import Union


def guess_family(level2: str) -> str:
    name = (level2 or '').lower()
    if 'iphone' in name:
        return 'iphone'
    if 'macbook' in name:
        return 'macbook'
    if 'ipad' in name:
        return 'ipad'
    if 'airpods' in name:
        return 'airpods'
    if 'homepod' in name:
        return 'homepod'
    if 'galaxy' in name or 'samsung' in name:
        return 'android_phone'
    return 'generic'


def build_payload(level2: str) -> tuple[str, dict]:
    family = guess_family(level2)
    title = level2
    if family == 'iphone':
        desc = f"{title}: быстрый чип, отличные камеры, яркий дисплей и премиальные материалы."
        details = {
            "Платформа": "iOS",
            "Дисплей": "OLED / Super Retina (диагональ зависит от модели)",
            "Процессор": "Apple A‑series / A17+",
            "Камера": "Основная система с продвинутыми режимами",
            "Материалы": "Стекло и титан/алюминий",
            "Зарядка": "MagSafe / быстрая зарядка",
        }
    elif family == 'macbook':
        desc = f"{title}: тонкий и тихий ноутбук на чипе Apple, длительная автономность и отличный дисплей."
        details = {
            "Платформа": "macOS",
            "Процессор": "Apple Silicon (M‑series)",
            "Дисплей": "IPS / Liquid Retina, True Tone",
            "Аккумулятор": "Длительная автономность",
            "Клавиатура": "Подсветка, большой трекпад",
            "Порты": "USB‑C / Thunderbolt",
        }
    elif family == 'ipad':
        desc = f"{title}: производительный планшет для работы и творчества с поддержкой Apple Pencil."
        details = {
            "Платформа": "iPadOS",
            "Дисплей": "Liquid Retina / IPS",
            "Аксессуары": "Apple Pencil, клавиатуры",
            "Процессор": "Apple A‑/M‑series",
            "Звук": "Стереодинамики",
        }
    elif family == 'airpods':
        desc = f"{title}: компактные наушники с активным шумоподавлением и глубоким звуком."
        details = {
            "Шумоподавление": "Активное (ANC)",
            "Прозрачность": "Режим прозрачности",
            "Зарядка": "Беспроводная / быстрая",
            "Защита": "От влаги и пота",
        }
    elif family == 'homepod':
        desc = f"{title}: умная колонка с насыщенным звучанием и интеграцией с экосистемой Apple."
        details = {
            "Умные функции": "Siri, умный дом",
            "Звук": "360° звук, вычислительное аудио",
            "Подключение": "Wi‑Fi, AirPlay",
        }
    elif family == 'android_phone':
        desc = f"{title}: мощный Android‑смартфон с современными камерами и дисплеем."
        details = {
            "Платформа": "Android",
            "Дисплей": "AMOLED / высокая частота",
            "Процессор": "Флагманский чипсет",
            "Камера": "Мультикамера с ночным режимом",
        }
    else:
        desc = f"{title}: современное устройство с сбалансированными характеристиками."
        details = {
            "Особенности": ["Производительность", "Автономность", "Качество сборки"],
        }
    return desc, details


RU_KEY_MAP = {
    "platform": "Платформа",
    "display": "Дисплей",
    "processor": "Процессор",
    "camera": "Камера",
    "materials": "Материалы",
    "charging": "Зарядка",
    "battery": "Аккумулятор",
    "keyboard": "Клавиатура",
    "ports": "Порты",
    "accessories": "Аксессуары",
    "audio": "Звук",
    "smart": "Умные функции",
    "sound": "Звук",
    "connectivity": "Подключение",
    "highlights": "Особенности",
}

def rusify_details(details_json: Union[str, dict]) -> str:
    try:
        details = json.loads(details_json) if isinstance(details_json, str) else details_json
    except Exception:
        return details_json if isinstance(details_json, str) else json.dumps(details_json, ensure_ascii=False)
    new_details = {}
    for k, v in details.items():
        rk = RU_KEY_MAP.get(k, k)
        new_details[rk] = v
    return json.dumps(new_details, ensure_ascii=False)


def main() -> None:
    engine = create_engine(Config.DATABASE_URL)
    with Session(engine) as db:
        # Distinct level_2 from products
        level2_values = [row[0] for row in db.query(Product.level_2).filter(Product.level_2.isnot(None)).distinct().all()]
        existing = {row[0] for row in db.query(Level2Description.level_2).all()}
        missing = [lv for lv in level2_values if lv not in existing]

        created = 0
        for lv in missing:
            desc, details = build_payload(lv)
            rec = Level2Description(
                level_2=lv,
                description=desc,
                details=json.dumps(details, ensure_ascii=False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(rec)
            created += 1
        if created:
            db.commit()

        # Rusify existing entries if needed
        updated = 0
        rows = db.query(Level2Description).all()
        for row in rows:
            try:
                det = json.loads(row.details) if row.details else {}
            except Exception:
                det = {}
            if any(k in det for k in RU_KEY_MAP.keys()):
                row.details = rusify_details(det)
                row.updated_at = datetime.utcnow()
                updated += 1
        if updated:
            db.commit()

        print(f"Missing: {len(missing)}, created: {created}, rusified: {updated}")


if __name__ == "__main__":
    main()



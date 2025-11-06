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
    if 'яндекс' in name or 'yandex' in name or 'станция' in name:
        return 'yandex_station'
    if 'adapter' in name or 'адаптер' in name:
        return 'adapter'
    return 'generic'


def build_payload(level2: str) -> tuple[str, dict]:
    family = guess_family(level2)
    title = level2
    name_lower = level2.lower()
    
    if family == 'iphone':
        # Детальные описания для разных моделей iPhone
        if 'pro max' in name_lower or 'promax' in name_lower:
            desc = f"{title}: флагманский смартфон с максимальным экраном, продвинутой камерой и мощным процессором. Премиальные материалы и передовые технологии."
            details = {
                "Платформа": "iOS",
                "Дисплей": "Super Retina XDR OLED, 6.7 дюйма, ProMotion 120 Гц",
                "Процессор": "Apple A17 Pro / A18 Pro",
                "Камера": "Тройная камера: основная 48 МП, сверхширокоугольная, телеобъектив с оптическим зумом",
                "Материалы": "Титан и керамический щит",
                "Зарядка": "MagSafe, беспроводная, быстрая зарядка",
                "Память": "До 1 ТБ встроенной памяти",
                "Защита": "IP68 (водонепроницаемость до 6 метров)",
            }
        elif 'pro' in name_lower:
            desc = f"{title}: профессиональный смартфон с продвинутой камерой, мощным процессором и премиальным дизайном. Идеален для творчества и работы."
            details = {
                "Платформа": "iOS",
                "Дисплей": "Super Retina XDR OLED, 6.1 дюйма, ProMotion 120 Гц",
                "Процессор": "Apple A17 Pro / A18 Pro",
                "Камера": "Тройная камера: основная 48 МП, сверхширокоугольная, телеобъектив",
                "Материалы": "Титан и керамический щит",
                "Зарядка": "MagSafe, беспроводная, быстрая зарядка",
                "Память": "До 1 ТБ встроенной памяти",
                "Защита": "IP68 (водонепроницаемость до 6 метров)",
            }
        elif 'plus' in name_lower:
            desc = f"{title}: смартфон с увеличенным экраном, улучшенной камерой и длительной автономностью. Отличный выбор для любителей больших экранов."
            details = {
                "Платформа": "iOS",
                "Дисплей": "Super Retina XDR OLED, 6.7 дюйма",
                "Процессор": "Apple A17 / A18",
                "Камера": "Двойная камера: основная 48 МП, сверхширокоугольная",
                "Материалы": "Алюминий и керамический щит",
                "Зарядка": "MagSafe, беспроводная, быстрая зарядка",
                "Память": "До 512 ГБ встроенной памяти",
                "Защита": "IP68 (водонепроницаемость до 6 метров)",
            }
        else:
            desc = f"{title}: современный смартфон с отличной камерой, ярким дисплеем и мощным процессором. Сбалансированное сочетание функций и цены."
            details = {
                "Платформа": "iOS",
                "Дисплей": "Super Retina XDR OLED, 6.1 дюйма",
                "Процессор": "Apple A17 / A18",
                "Камера": "Двойная камера: основная 48 МП, сверхширокоугольная",
                "Материалы": "Алюминий и керамический щит",
                "Зарядка": "MagSafe, беспроводная, быстрая зарядка",
                "Память": "До 512 ГБ встроенной памяти",
                "Защита": "IP68 (водонепроницаемость до 6 метров)",
            }
    elif family == 'macbook':
        if 'pro' in name_lower:
            desc = f"{title}: профессиональный ноутбук с мощным процессором Apple Silicon, ярким дисплеем и длительной автономностью. Идеален для профессиональной работы."
            details = {
                "Платформа": "macOS",
                "Процессор": "Apple M3 Pro / M3 Max / M4 Pro",
                "Дисплей": "Liquid Retina XDR, 14 или 16 дюймов, ProMotion 120 Гц",
                "Аккумулятор": "До 22 часов работы",
                "Клавиатура": "Magic Keyboard с подсветкой, большой Force Touch трекпад",
                "Порты": "Thunderbolt 4, HDMI, SD кардридер, MagSafe 3",
                "Память": "До 128 ГБ оперативной памяти",
                "Хранилище": "До 8 ТБ SSD",
            }
        elif 'air' in name_lower:
            desc = f"{title}: ультратонкий и легкий ноутбук с процессором Apple Silicon. Отличная производительность и длительная автономность в компактном корпусе."
            details = {
                "Платформа": "macOS",
                "Процессор": "Apple M3 / M4",
                "Дисплей": "Liquid Retina, 13.6 или 15.3 дюйма, True Tone",
                "Аккумулятор": "До 18 часов работы",
                "Клавиатура": "Magic Keyboard с подсветкой, большой Force Touch трекпад",
                "Порты": "Thunderbolt 4, MagSafe 3",
                "Память": "До 24 ГБ оперативной памяти",
                "Хранилище": "До 2 ТБ SSD",
            }
        else:
            desc = f"{title}: надежный ноутбук на чипе Apple Silicon с отличной производительностью и длительной автономностью."
            details = {
                "Платформа": "macOS",
                "Процессор": "Apple Silicon (M‑series)",
                "Дисплей": "Liquid Retina, True Tone",
                "Аккумулятор": "Длительная автономность",
                "Клавиатура": "Magic Keyboard с подсветкой, большой трекпад",
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
        if 'galaxy' in name_lower and ('s24' in name_lower or 's25' in name_lower):
            desc = f"{title}: флагманский Android‑смартфон с передовыми камерами, ярким дисплеем и мощным процессором. Инновационные функции и премиальный дизайн."
            details = {
                "Платформа": "Android",
                "Дисплей": "Dynamic AMOLED 2X, 120 Гц, HDR10+",
                "Процессор": "Snapdragon 8 Gen 3 / Exynos 2400",
                "Камера": "Тройная камера: основная 200 МП, сверхширокоугольная, телеобъектив",
                "Память": "До 1 ТБ встроенной памяти, до 12 ГБ RAM",
                "Зарядка": "Быстрая зарядка, беспроводная зарядка",
                "Защита": "IP68 (водонепроницаемость)",
            }
        elif 'galaxy' in name_lower:
            desc = f"{title}: мощный Android‑смартфон Samsung с современными камерами, ярким дисплеем и длительной автономностью."
            details = {
                "Платформа": "Android",
                "Дисплей": "AMOLED, высокая частота обновления",
                "Процессор": "Флагманский чипсет",
                "Камера": "Мультикамера с ночным режимом",
                "Зарядка": "Быстрая зарядка, беспроводная зарядка",
                "Защита": "IP68 (водонепроницаемость)",
            }
        else:
            desc = f"{title}: мощный Android‑смартфон с современными камерами и дисплеем."
            details = {
                "Платформа": "Android",
                "Дисплей": "AMOLED / высокая частота",
                "Процессор": "Флагманский чипсет",
                "Камера": "Мультикамера с ночным режимом",
            }
    elif family == 'yandex_station':
        if 'макс' in name_lower or 'max' in name_lower:
            desc = f"{title}: умная колонка с максимальным звуком, голосовым помощником Алисой и интеграцией с экосистемой Яндекса. Идеальна для управления умным домом."
            details = {
                "Голосовой помощник": "Алиса от Яндекса",
                "Звук": "Мощные динамики с глубокими басами",
                "Подключение": "Wi‑Fi, Bluetooth",
                "Умный дом": "Управление устройствами умного дома",
                "Экран": "Цветной дисплей (для моделей с экраном)",
                "Аудио": "Поддержка Яндекс.Музыки и других сервисов",
            }
        elif 'дуо' in name_lower or 'duo' in name_lower:
            desc = f"{title}: умная колонка с двумя динамиками, голосовым помощником Алисой и отличным звуком. Компактный размер с мощным звучанием."
            details = {
                "Голосовой помощник": "Алиса от Яндекса",
                "Звук": "Два динамика с объемным звуком",
                "Подключение": "Wi‑Fi, Bluetooth",
                "Умный дом": "Управление устройствами умного дома",
                "Аудио": "Поддержка Яндекс.Музыки и других сервисов",
            }
        elif 'миди' in name_lower or 'midi' in name_lower:
            desc = f"{title}: компактная умная колонка с голосовым помощником Алисой. Отличный баланс размера и качества звука."
            details = {
                "Голосовой помощник": "Алиса от Яндекса",
                "Звук": "Качественный звук в компактном корпусе",
                "Подключение": "Wi‑Fi, Bluetooth",
                "Умный дом": "Управление устройствами умного дома",
                "Аудио": "Поддержка Яндекс.Музыки и других сервисов",
            }
        else:
            desc = f"{title}: умная колонка с голосовым помощником Алисой и интеграцией с экосистемой Яндекса."
            details = {
                "Голосовой помощник": "Алиса от Яндекса",
                "Звук": "Качественный звук",
                "Подключение": "Wi‑Fi, Bluetooth",
                "Умный дом": "Управление устройствами умного дома",
            }
    elif family == 'adapter':
        desc = f"{title}: зарядное устройство для быстрой и безопасной зарядки ваших устройств."
        details = {
            "Мощность": "20W / быстрая зарядка",
            "Совместимость": "USB-C, Lightning",
            "Безопасность": "Защита от перегрева и перегрузки",
            "Сертификация": "Соответствие стандартам безопасности",
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



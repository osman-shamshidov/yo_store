#!/usr/bin/env python3
"""
Обновляет существующие описания level2_descriptions более детальными описаниями и характеристиками.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Product, Level2Description
from datetime import datetime
import json
from config import Config
from populate_level2_descriptions import build_payload

def main() -> None:
    engine = create_engine(Config.DATABASE_URL)
    with Session(engine) as db:
        # Получаем все существующие описания
        existing_descriptions = db.query(Level2Description).all()
        
        updated = 0
        for desc in existing_descriptions:
            # Генерируем новые детальные описания
            new_desc, new_details = build_payload(desc.level_2)
            
            # Обновляем только если описание слишком короткое или детали неполные
            should_update = False
            
            # Проверяем длину описания
            if len(desc.description) < 50:
                should_update = True
            
            # Проверяем количество характеристик
            try:
                current_details = json.loads(desc.details) if desc.details else {}
                if len(current_details) < 5:
                    should_update = True
            except:
                should_update = True
            
            if should_update:
                desc.description = new_desc
                desc.details = json.dumps(new_details, ensure_ascii=False)
                desc.updated_at = datetime.utcnow()
                updated += 1
                print(f"Обновлено: {desc.level_2}")
        
        if updated:
            db.commit()
            print(f"\nВсего обновлено: {updated} записей")
        else:
            print("Все записи уже имеют детальные описания")

if __name__ == "__main__":
    main()


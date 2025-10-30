import os
import sys
import json
from datetime import datetime
import pandas as pd


def transform_specs(value: object) -> object:
    if value is None:
        return value
    try:
        text = str(value).strip()
        if not text:
            return value
        data = json.loads(text)
        if isinstance(data, dict):
            # Rename keys if present
            if 'memory' in data and 'disk' not in data:
                data['disk'] = data.pop('memory')
            if 'sim_type' in data and 'sim_config' not in data:
                data['sim_config'] = data.pop('sim_type')
            return json.dumps(data, ensure_ascii=False)
        return value
    except Exception:
        # Leave as-is if not valid JSON
        return value


def process_file(xlsx_path: str) -> None:
    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"File not found: {xlsx_path}")

    # Backup original
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{xlsx_path}.backup_{ts}"
    with open(xlsx_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())

    # Read all sheets
    sheets = pd.read_excel(xlsx_path, sheet_name=None)

    modified_any = False
    target_column = 'Характеристики (JSON)'

    for name, df in sheets.items():
        if target_column in df.columns:
            df[target_column] = df[target_column].apply(transform_specs)
            sheets[name] = df
            modified_any = True

    if not modified_any:
        print('No sheets contained column: Характеристики (JSON). Nothing changed.')
        return

    # Write back preserving sheets order
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    print(f'Updated keys memory→disk and sim_type→sim_config. Backup saved to {backup_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python update_feed_specs_keys.py "/absolute/path/Фид на сайт.xlsx"')
        sys.exit(1)
    process_file(sys.argv[1])



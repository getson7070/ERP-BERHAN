import csv
import json
from pathlib import Path
from db import get_db

BASE_DIR = Path(__file__).resolve().parent
FINETO_DIR = BASE_DIR.parent / 'fineto'
MAPPINGS_FILE = BASE_DIR / 'fineto_mapping.json'


def load_mappings():
    with open(MAPPINGS_FILE) as f:
        return json.load(f)


def read_template_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        lines = f.readlines()
    start = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith('Start entering data'):
            start = idx + 1
            break
    reader = csv.DictReader(lines[start:])
    return list(reader)


def import_csv(mapping):
    table = mapping['table']
    csv_file = FINETO_DIR / mapping['csv']
    rows = read_template_csv(csv_file)
    if not rows:
        return
    with get_db() as conn:
        for row in rows:
            data = {db_field: row.get(csv_field) for csv_field, db_field in mapping['fields'].items()}
            placeholders = ','.join('?' for _ in data)
            columns = ','.join(data.keys())
            conn.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', tuple(data.values()))
        conn.commit()


def main():
    for mapping in load_mappings():
        import_csv(mapping)


if __name__ == '__main__':
    main()

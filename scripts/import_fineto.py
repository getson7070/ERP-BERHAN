import csv
import json
import pathlib

from db import get_db
from erp.sql_compat import to_psql

MAPPING_FILE = pathlib.Path("fineto/mapping.json")
DATA_DIR = pathlib.Path("fineto")


def import_fineto():
    if not MAPPING_FILE.exists():
        raise FileNotFoundError("mapping.json not found")
    with open(MAPPING_FILE) as f:
        mappings = json.load(f)

    conn = get_db()
    for filename, cfg in mappings.items():
        file_path = DATA_DIR / filename
        if not file_path.exists():
            continue
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for row in reader:
                mapped = {dst: row.get(src) for src, dst in cfg["field_map"].items()}
                rows.append(mapped)
            if rows:
                cols = ",".join(rows[0].keys())
                placeholders = ",".join("?" for _ in rows[0])
                sql = to_psql(
                    f"INSERT INTO {cfg['table']} ({cols}) VALUES ({placeholders})"  # nosec B608
                )
                conn.executemany(sql, [tuple(r.values()) for r in rows])
                conn.commit()
    conn.close()


if __name__ == "__main__":
    import_fineto()



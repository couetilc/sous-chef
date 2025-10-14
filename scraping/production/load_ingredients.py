#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "psycopg[binary]"
# ]
# ///

import os, csv
import psycopg
from pathlib import Path

<<<<<<< HEAD
path = Path("./canonical_ingredients.csv")
=======
# Path to your canonical ingredients CSV
path = Path("./scraping/production/canonical_ingredients.csv")

# Default to local Postgres if DATABASE_URL not set
>>>>>>> cfc79889f687a78f3016fa5ea59ebe56e45ff5cd
conn_info = os.getenv("DATABASE_URL", "postgresql://dbuser:dbpass@localhost:5432/api")

def f(x):
    """Parse numeric cell -> float or None (NULL). Accepts '', 'NA', 'null', etc."""
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"na", "n/a", "null", "none"}:
        return None
    try:
        return float(s.replace(",", ""))  # tolerate thousands separators
    except ValueError:
        return None

def t(x):
    """Parse text cell -> str or None (NULL) stripping empty strings."""
    if x is None:
        return None
    s = str(x).strip()
    return s if s != "" else None

with psycopg.connect(conn_info, row_factory=psycopg.rows.dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS canonical_ingredients")
        cur.execute("""
            CREATE TABLE canonical_ingredients (
                id SERIAL PRIMARY KEY,
                food_id TEXT,
                description TEXT,
                food_category TEXT,
                calories REAL,
                protein_g REAL,
                fat_g REAL,
                carbs_g REAL,
                price_g REAL,
                quantity_other TEXT,
                price REAL
            )
        """)

        with path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for row in reader:
                rows.append((
                    t(row.get("food_id")),
                    t(row.get("description")),
                    t(row.get("food_category")),
                    f(row.get("calories")),
                    f(row.get("protein_g")),
                    f(row.get("fat_g")),
                    f(row.get("carbs_g")),
                    f(row.get("price_g")),
                    t(row.get("quantity_other")),
                    f(row.get("price")),
                ))


        cur.executemany("""
            INSERT INTO canonical_ingredients
            (food_id, description, food_category, calories, protein_g, fat_g, carbs_g, price_g, quantity_other, price)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, rows)
    conn.commit()

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "psycopg[binary]"
# ]
# ///

import os
import psycopg
import csv
from pathlib import Path

# Path to your canonical ingredients CSV
path = Path("./scraping/production/canonical_ingredients.csv")

# Default to local Postgres if DATABASE_URL not set
conn_info = os.getenv("DATABASE_URL", "postgresql://dbuser:dbpass@localhost:5432/api")

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

        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("""
                    INSERT INTO canonical_ingredients
                    (food_id, description, food_category, calories, protein_g, fat_g, carbs_g, price_g, quantity_other, price)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    row.get("food_id"),
                    row.get("description"),
                    row.get("food_category"),
                    row.get("calories"),
                    row.get("protein_g"),
                    row.get("fat_g"),
                    row.get("carbs_g"),
                    row.get("price_g"),
                    row.get("quantity_other"),
                    row.get("price"),
                ))

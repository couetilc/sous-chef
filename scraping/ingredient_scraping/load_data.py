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

path = Path("./scraping/ingredient_scraping/ingredient_csv_files/legacy_cleaned_ingredients.csv")

conn_info = os.getenv("DATABASE_URL", "postgresql://dbuser:dbpass@localhost:5432/api")

with psycopg.connect(conn_info, row_factory = psycopg.rows.dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS scraped_ingredients")
        cur.execute("CREATE TABLE scraped_ingredients (id serial PRIMARY KEY, name TEXT, calories TEXT, protein TEXT, fat TEXT, carbs TEXT, category TEXT)")
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("INSERT INTO scraped_ingredients (name, calories, protein, fat, carbs, category) VALUES (%s,%s,%s,%s,%s,%s)", (row["description"], row["calories"], row["protein_g"], row["fat_g"], row["carbs_g"], row["food_category"]))


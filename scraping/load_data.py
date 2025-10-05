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

path = Path("./scraping/recipes_clean.csv")

conn_info = os.getenv("DATABASE_URL", "postgresql://dbuser:dbpass@localhost:5432/api")

with psycopg.connect(conn_info, row_factory = psycopg.rows.dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS scraped_recipes")
        cur.execute("CREATE TABLE scraped_recipes (id serial PRIMARY KEY, title TEXT, url TEXT, image TEXT, ingredients TEXT, steps TEXT)")
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute("INSERT INTO scraped_recipes (title, url, image, ingredients, steps) VALUES (%s,%s,%s,%s,%s)", (row["title"], row["url"], row["image"], row["ingredients"], row["steps"]))


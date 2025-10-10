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

path = Path("./price_scraping/ingredient_prices.csv")

conn_info = os.getenv("DATABASE_URL", "postgresql://dbuser:dbpass@localhost:5432/api")

with psycopg.connect(conn_info, row_factory = psycopg.rows.dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS scraped_prices")
        cur.execute("CREATE TABLE scraped_prices (id serial PRIMARY KEY, ingredient_name TEXT, quantity TEXT, price TEXT)")
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute(
                    "INSERT INTO scraped_prices (ingredient_name, quantity, price) VALUES (%s,%s,%s)",
                    (row["ingredient_name"], row["quantity"], row["price"])
                )

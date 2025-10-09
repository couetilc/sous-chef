#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pandas"
# ]
# ///

import pandas as pd

INPUT_CSV = "scraping/ingredient_scraping/ingredient_csv_files/foundation_scraped_ingredients.csv"      
OUTPUT_CSV = "scraping/ingredient_scraping/ingredient_csv_files/foundation_cleaned_ingredients.csv"

# Load the combined dataset
df = pd.read_csv(INPUT_CSV)

df.columns = df.columns.str.strip()

# Columns that must all be present (non-empty)
nutrient_cols = ["calories", "protein_g", "fat_g", "carbs_g"]

for col in nutrient_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Option 1️⃣: Drop only rows missing *all* nutrients
clean_df = df.dropna(subset=nutrient_cols, how="all")

# Save the cleaned dataset
clean_df.to_csv(OUTPUT_CSV, index=False)

print(f"Cleaned dataset saved to {OUTPUT_CSV}")
print(f"Original rows: {len(df)}")
print(f"Remaining rows: {len(clean_df)}")

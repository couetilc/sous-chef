#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pandas"
# ]
# ///

import pandas as pd

# Filenames
FOODS_CSV = "scraping/ingredient_scraping/usda_csv_files/legacy_food.csv"
FOOD_NUTRIENT_CSV = "scraping/ingredient_scraping/usda_csv_files/legacy_food_nutrient.csv"
NUTRIENT_CSV = "scraping/ingredient_scraping/usda_csv_files/legacy_nutrient.csv"
OUTPUT_CSV = "scraping/ingredient_scraping/ingredient_csv_files/legacy_scraped_ingredients.csv"

# Load csvs
foods_df = pd.read_csv(FOODS_CSV, dtype=str)
fn_df = pd.read_csv(FOOD_NUTRIENT_CSV, dtype=str)
nutrient_df = pd.read_csv(NUTRIENT_CSV, dtype=str)

# Rename for consistency
nutrient_df = nutrient_df.rename(columns={"id": "nutrient_id", "name": "nutrient_name", "unit_name": "unit"})
fn_df = fn_df.rename(columns={"id": "food_nutrient_id"})

# Merge food_nutrient with nutrient definitions
fn_with_defs = fn_df.merge(nutrient_df, how="left", on="nutrient_id")

wanted_nutrients = {
    # Calories
    "Energy",
    "Protein",
    "Total lipid (fat)",
    "Carbohydrate, by difference",
    "Fiber, total dietary",
    "Sugars, total"
}

fn_with_defs = fn_with_defs[ fn_with_defs["nutrient_name"].isin(wanted_nutrients) ]

# Convert amount column to numeric
fn_with_defs["amount"] = pd.to_numeric(fn_with_defs["amount"], errors="coerce")

# Food is rows, nutrient is columns
pivot = fn_with_defs.pivot_table(
    index="fdc_id",
    columns="nutrient_name",
    values="amount",
    # No duplicates
    aggfunc="first"
).reset_index()

# Merge with foods_df to bring in description
combined = foods_df.merge(pivot, how="left", on="fdc_id")

combined = combined.rename(columns={
    "Energy": "calories",
    "Protein": "protein_g",
    "Total lipid (fat)": "fat_g",
    "Carbohydrate, by difference": "carbs_g",
    "Fiber, total dietary": "fiber_g",
    "Sugars, total": "sugar_g",
})

columns_to_keep = [
    "fdc_id",
    "description",
    "data_type",
    "food_category_id",
    "publication_date",
    "calories",
    "protein_g",
    "fat_g",
    "carbs_g",
    "fiber_g",
    "sugar_g"
]

existing = [c for c in columns_to_keep if c in combined.columns]
final = combined[existing]

# Write to output
final.to_csv(OUTPUT_CSV, index=False)
print(f"Wrote {len(final)} foods with macros to {OUTPUT_CSV}")

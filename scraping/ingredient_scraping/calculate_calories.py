#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pandas"
# ]
# ///

import pandas as pd

INPUT_CSV = "scraping/ingredient_scraping/ingredient_csv_files/legacy_scraped_ingredients.csv"
OUTPUT_CSV = "scraping/ingredient_scraping/ingredient_csv_files/legacy_cleaned_ingredients.csv"

CAL_PER_GRAM_PROTEIN = 4
CAL_PER_GRAM_CARBS = 4
CAL_PER_GRAM_FAT = 9

def main():
    df = pd.read_csv(INPUT_CSV)

    # Ensure numeric types for macros
    for col in ["protein_g", "fat_g", "carbs_g"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            print(f"⚠️ Missing column: {col}")
            return

    # Recalculate and round calories
    df["calories"] = (
        (df["protein_g"].fillna(0) * CAL_PER_GRAM_PROTEIN) +
        (df["fat_g"].fillna(0) * CAL_PER_GRAM_FAT) +
        (df["carbs_g"].fillna(0) * CAL_PER_GRAM_CARBS)
    ).round(1)

    # Remove fiber column if present
    if "fiber_g" in df.columns:
        df = df.drop(columns=["fiber_g"])

    # Reorder columns: put calories before macros
    col_order = df.columns.tolist()
    if all(c in col_order for c in ["calories", "protein_g", "fat_g", "carbs_g"]):
        # Move calories before the macros
        for c in ["calories"]:
            col_order.remove(c)
        # Find where to insert before protein_g
        insert_index = col_order.index("protein_g")
        col_order.insert(insert_index, "calories")
        df = df[col_order]

    # Save new CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Recalculated and reformatted CSV saved to {OUTPUT_CSV}")
    print(f"Total rows: {len(df)}")

if __name__ == "__main__":
    main()
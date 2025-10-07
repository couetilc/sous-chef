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

food_category_map = {
    1: "Dairy and Egg Products",
    2: "Spices and Herbs",
    3: "Baby Foods",
    4: "Fats and Oils",
    5: "Poultry Products",
    6: "Soups, Sauces, and Gravies",
    7: "Sausages and Luncheon Meats",
    8: "Breakfast Cereals",
    9: "Fruits and Fruit Juices",
    10: "Pork Products",
    11: "Vegetables and Vegetable Products",
    12: "Nut and Seed Products",
    13: "Beef Products",
    14: "Beverages",
    15: "Finfish and Shellfish Products",
    16: "Legumes and Legume Products",
    17: "Lamb, Veal, and Game Products",
    18: "Baked Products",
    19: "Sweets",
    20: "Cereal Grains and Pasta",
    21: "Fast Foods",
    22: "Meals, Entrees, and Side Dishes",
    23: "Snacks",
    24: "American Indian/Alaska Native Foods",
    25: "Restaurant Foods",
    26: "Branded Food Products Database",
    27: "Quality Control Materials",
    28: "Alcoholic Beverages",
}

def main():
    df = pd.read_csv(INPUT_CSV)

    # Replace food_category ID with name
    df["food_category"] = df["food_category_id"].map(food_category_map)
    df.drop(columns=["food_category_id"], inplace=True, errors="ignore")

    # Recalculate and round calories
    df["calories"] = (
        (df["protein_g"].fillna(0) * CAL_PER_GRAM_PROTEIN) +
        (df["fat_g"].fillna(0) * CAL_PER_GRAM_FAT) +
        (df["carbs_g"].fillna(0) * CAL_PER_GRAM_CARBS)
    ).round(1)

    # Drop unneeded columns
    columns_to_remove = ["fiber_g", "data_type", "publication_date"]
    df.drop(columns=[c for c in columns_to_remove if c in df.columns], inplace=True)

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
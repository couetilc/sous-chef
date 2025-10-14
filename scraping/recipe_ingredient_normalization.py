#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pandas",
#   "rapidfuzz",
#   "nltk",
# ]
# ///

import pandas as pd
import re
import nltk
from rapidfuzz import process, fuzz
from nltk.stem import WordNetLemmatizer
from pathlib import Path

# --- CONFIGURATION ---
RECIPE_FILE = Path("scraping/recipe_scraping/recipe_csv_files/recipes.csv")
INGREDIENT_FILE = Path("scraping/finalized_ingredients.csv")
OUTPUT_FILE = Path("scraping/recipe_ingredient_matches.csv")
N_RECIPES = 20
MIN_SCORE = 0

lemmatizer = WordNetLemmatizer()

STOPWORDS = [
    "cup", "cups", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons", "tsp",
    "ounce", "ounces", "oz", "gram", "grams", "g", "kg", "pound", "pounds", "lb", "lbs",
    "liter", "liters", "ml", "quart", "quarts", "gallon", "gallons",
    "chopped", "minced", "diced", "sliced", "thinly", "boneless", "skinless", "fresh",
    "ground", "large", "small", "medium", "raw", "frozen", "cooked", "dry", "dried",
    "whole", "peeled", "seeded", "grated", "crushed", "drained", "to", "taste", "and", "of", "with", "the"
]

def normalize(text: str) -> str:
    """Normalize text by cleaning and lemmatizing."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\d+(\.\d+)?|\d+/\d+|½|¼|¾', '', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [
        lemmatizer.lemmatize(w.strip())
        for w in text.split()
        if w.strip() and w.strip() not in STOPWORDS
    ]
    return " ".join(sorted(tokens))

def core_phrase(ingredient_name: str) -> str:
    """Return only the first two comma-separated parts for matching context."""
    parts = [p.strip() for p in ingredient_name.split(",") if p.strip()]
    return ", ".join(parts[:2])  # Keep only first two components

# --- LOAD DATA ---
recipes_df = pd.read_csv(RECIPE_FILE)
ingredients_df = pd.read_csv(INGREDIENT_FILE)

recipes_df = recipes_df.head(N_RECIPES)

ingredient_names = ingredients_df["description"].astype(str).tolist()
ingredient_core = [core_phrase(name) for name in ingredient_names]
ingredient_norms = [normalize(n) for n in ingredient_core]

print(f"Loaded {len(recipes_df)} recipes and {len(ingredient_names)} ingredients.")

# --- MATCH FUNCTION ---
def find_best_match(ingredient):
    normalized = normalize(ingredient)
    if not normalized:
        return pd.Series(["", 0])
    match, score, _ = process.extractOne(
        normalized,
        ingredient_norms,
        scorer=fuzz.token_set_ratio
    )
    matched_name = ingredient_names[ingredient_norms.index(match)] if score >= MIN_SCORE else ""
    return pd.Series([matched_name, score])

# --- PROCESS ---
matches = []
for i, row in recipes_df.iterrows():
    recipe_ingredients = str(row.get("ingredients", "")).split("|")
    for ing in recipe_ingredients:
        ing = ing.strip()
        if not ing:
            continue
        matched_name, score = find_best_match(ing)
        matches.append({
            "recipe_index": i,
            "original_ingredient": ing,
            "normalized_ingredient": normalize(ing),
            "matched_ingredient": matched_name,
            "match_score": score
        })

# --- SAVE ---
matches_df = pd.DataFrame(matches)
matches_df.to_csv(OUTPUT_FILE, index=False)

print(f"\n✅ Matching complete! Saved to '{OUTPUT_FILE}'")
print(matches_df.head(10))

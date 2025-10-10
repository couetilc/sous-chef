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

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# File paths
RECIPE_FILE = Path("scraping/recipe_scraping/recipe_csv_files/recipes.csv")
INGREDIENT_FILE = Path("scraping/ingredient_scraping/ingredient_csv_files/legacy_cleaned_ingredients.csv")
OUTPUT_FILE = Path("scraping/recipe_ingredient_matches.csv")
N_RECIPES = 20  # only process the first 20

# Normalizer
lemmatizer = WordNetLemmatizer()

def normalize(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)       # remove parentheses
    text = re.sub(r'[^a-z\s]', '', text)        # remove punctuation/numbers
    text = re.sub(r'\b(?:cup|cups|tablespoon|tablespoons|teaspoon|teaspoons|ounce|ounces|pound|pounds|large|small|medium|chopped|sliced|fresh|organic|dried|boneless|skinless|ground|of|and|with|the)\b', '', text)
    tokens = [lemmatizer.lemmatize(w.strip()) for w in text.split() if w.strip()]
    return " ".join(sorted(tokens))

# --- LOAD DATA ---
recipes_df = pd.read_csv(RECIPE_FILE)
ingredients_df = pd.read_csv(INGREDIENT_FILE)

# Get only the first 20 recipes
recipes_df = recipes_df.head(N_RECIPES)

# Extract ingredient descriptions
ingredient_names = ingredients_df["description"].astype(str).tolist()
ingredient_norms = [normalize(n) for n in ingredient_names]

print(f"Loaded {len(recipes_df)} recipes and {len(ingredient_names)} ingredient descriptions.")

# --- MATCHING FUNCTION ---
def find_best_match(ingredient):
    normalized = normalize(ingredient)
    if not normalized:
        return pd.Series(["", 0])
    match, score, _ = process.extractOne(
        normalized,
        ingredient_norms,
        scorer=fuzz.token_sort_ratio
    )
    return pd.Series([ingredient_names[ingredient_norms.index(match)], score])

# --- PROCESS EACH RECIPE ---
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

# --- SAVE RESULTS ---
matches_df = pd.DataFrame(matches)
matches_df.to_csv(OUTPUT_FILE, index=False)

print(f"\n✅ Matching complete! Saved results to '{OUTPUT_FILE}'")
print(matches_df.head(10))

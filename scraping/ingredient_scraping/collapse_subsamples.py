#!/usr/bin/env python3
import pandas as pd
import re

# === 1. Load your CSV ===
df = pd.read_csv("cleaned_ingredients.csv")

# Inspect columns
print("Columns detected:", df.columns.tolist())

# === 2. Normalize the ingredient name ===
# Remove sub-sample suffixes like "- Proximates - NF9913SR"
def normalize_name(name):
    # Remove trailing identifiers like "- Proximates - NF1234AB"
    return re.sub(r"\s*-\s*Proximates\s*-\s*NF\d+[A-Z]{0,2}$", "", str(name)).strip()

df["base_name"] = df["description"].apply(normalize_name)

# === 3. Group and collapse ===
# Average numeric columns (if any) across sub-samples, keeping first non-null values for others
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
non_numeric_cols = [c for c in df.columns if c not in numeric_cols and c not in ["base_name"]]

collapsed = (
    df.groupby("base_name", as_index=False)
      .agg({**{col: "first" for col in non_numeric_cols},
            **{col: "mean" for col in numeric_cols}})
)

# === 4. Sort and export ===
collapsed = collapsed.sort_values("base_name").reset_index(drop=True)
collapsed.to_csv("collapsed_ingredients.csv", index=False)

print(f"✅ Collapsed from {len(df)} → {len(collapsed)} unique ingredients.")
print("Saved as collapsed_ingredients.csv")

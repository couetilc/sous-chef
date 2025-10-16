#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""

- Ensures each entry has product_name, category, and price_formatted.
- Adds 'notes' and 'source_row' columns for transparency in demos.
- Includes optional 'chatter' to look busy.

Usage:
  ./clean_prices.py
  ./clean_prices.py --in /scraping/price_scraping/ingredient_prices.csv --out cleaned.csv
  ./clean_prices.py --no-chatter

Expected input columns (best-effort; only 'ingredient_name' and 'price' are needed):
  ingredient_name, quantity, price, ... (others are ignored)

Output columns:
  product_name, category, price_formatted, quantity, raw_price, notes, source_row
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# ---------- Config ----------
DEFAULT_IN  = Path("./scraping/price_scraping/ingredient_prices.csv")
DEFAULT_OUT = Path("./scraping/price_scraping/ingredient_prices_cleaned.csv")

CATEGORY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "Produce": ("apple", "banana", "broccoli", "spinach", "lettuce", "onion", "garlic", "carrot", "tomato", "cilantro",
                "pepper", "cucumber", "avocado", "grape", "berry", "potato", "mushroom", "kale", "lime", "lemon"),
    "Meat": ("beef", "chicken", "pork", "turkey", "lamb", "steak", "bacon", "sausage", "ham"),
    "Seafood": ("salmon", "tuna", "shrimp", "cod", "tilapia", "sardine", "oyster", "clam", "crab"),
    "Dairy": ("milk", "cheese", "yogurt", "butter", "cream", "half-and-half", "mozzarella", "cheddar", "parmesan"),
    "Grains & Pasta": ("rice", "pasta", "spaghetti", "noodle", "bread", "tortilla", "quinoa", "couscous", "oats"),
    "Baking": ("flour", "sugar", "yeast", "baking", "cocoa", "vanilla", "cornstarch", "bicarbonate"),
    "Snacks": ("chips", "cracker", "cookie", "pretzel", "popcorn", "granola", "snack"),
    "Beverages": ("coffee", "tea", "soda", "juice", "water", "sparkling"),
    "Condiments": ("ketchup", "mustard", "mayo", "mayonnaise", "relish", "sriracha", "hot sauce", "bbq", "soy sauce"),
    "Spices & Herbs": ("salt", "pepper", "cumin", "turmeric", "paprika", "oregano", "basil", "chili", "cinnamon",
                       "nutmeg", "clove", "ginger", "cardamom", "thyme", "rosemary", "sage", "chive", "parsley"),
    "Frozen": ("frozen", "ice cream", "fish sticks", "frozen pizza", "frozen vegetables"),
    "Canned & Jarred": ("canned", "jar", "pickles", "olives", "beans", "tomato sauce", "broth", "stock"),
    "Personal Care": ("toothpaste", "shampoo", "soap", "detergent", "deodorant", "lotion"),
    "Household": ("paper towel", "trash bag", "foil", "wrap", "cleaner", "bleach", "sponge"),
}

CHATTER_BURSTS = [
    "Indexing rows…", "Normalizing names…", "Inferring categories…",
    "Formatting prices…", "De-duplicating…", "Reconciling oddities…",
    "Checking for empties…", "Finalizing…"
]


# ---------- Helpers ----------
def chatter(enabled: bool, msg: str, delay: float = 0.01) -> None:
    if not enabled:
        return
    print(f"[cleaner] {msg}")
    # Small delay to look active without being annoying
    time.sleep(delay)


def clean_name(raw: str) -> str:
    s = (raw or "").strip()
    # Collapse whitespace, remove trailing commas/dots and style to title case
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[,\.\s]+$", "", s)
    # Keep common lowercase connectors (e.g., "of", "and") after title()
    titled = s.title()
    # Restore small words to lower if not starting token
    small = {"Of", "And", "Or", "With", "In", "On", "For", "The", "A", "An"}
    tokens = titled.split()
    for i, t in enumerate(tokens):
        if i and t in small:
            tokens[i] = t.lower()
    return " ".join(tokens) or "Unnamed Item"


def infer_category(name: str) -> str:
    lower = name.lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        if any(k in lower for k in keys):
            return cat
    return "Other"


def parse_price(raw_price: str) -> float | None:
    """
    Best-effort numeric extraction from a messy price string.
    Accepts '3.49', '$3.49', 'USD 3.49', '3,49', etc.
    Returns float or None if unparseable/empty.
    """
    s = (raw_price or "").strip()
    if not s:
        return None
    # Replace commas used as decimal separators
    s = s.replace(",", "")
    # Grab first numeric like 12, 12.34, .99
    m = re.search(r"(?<!\d)(\d*\.\d+|\d+)(?![\d/])", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def fmt_price(value: float | None) -> str:
    if value is None or value != value:  # NaN guard
        return "$0.00"
    return f"${value:,.2f}"


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Clean ingredient_prices.csv for demo output.")
    ap.add_argument("--in", dest="in_path", type=Path, default=DEFAULT_IN,
                    help=f"Path to input CSV (default: {DEFAULT_IN})")
    ap.add_argument("--out", dest="out_path", type=Path, default=DEFAULT_OUT,
                    help=f"Path to output CSV (default: {DEFAULT_OUT})")
    ap.add_argument("--no-chatter", action="store_true", help="Disable busy chatter in stdout")
    args = ap.parse_args()

    chatter_enabled = not args.no_chatter

    if not args.in_path.exists():
        print(f"ERROR: Input CSV not found: {args.in_path}", file=sys.stderr)
        sys.exit(2)

    chatter(chatter_enabled, f"Opening {args.in_path} …")
    with args.in_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Soft validation — we mainly need ingredient_name and price
        required = {"ingredient_name", "price"}
        missing = [c for c in required if c not in reader.fieldnames]
        if missing:
            print(f"WARNING: Missing expected columns: {', '.join(missing)}. "
                  f"Continuing with best-effort parsing.", file=sys.stderr)

        rows = list(reader)

    total = len(rows)
    if total == 0:
        print("No rows found. Nothing to do.")
        return

    chatter(chatter_enabled, f"Loaded {total} rows.")
    chatter(chatter_enabled, "Priming pipelines…")
    processed = []

    # Prepare output
    out_fields = [
        "product_name",
        "category",
        "price_formatted",
        "quantity",
        "raw_price",
        "notes",
        "source_row",
    ]

    # Walk rows
    for i, row in enumerate(rows, start=1):
        if chatter_enabled and i == 1:
            chatter(True, CHATTER_BURSTS[0])
        elif chatter_enabled and i == total // 3:
            chatter(True, CHATTER_BURSTS[1])
        elif chatter_enabled and i == (2 * total) // 3:
            chatter(True, CHATTER_BURSTS[2])

        raw_name = row.get("ingredient_name") or row.get("name") or ""
        product_name = clean_name(raw_name)
        category = infer_category(product_name)

        raw_price = row.get("price", "")
        price_val = parse_price(raw_price)
        price_formatted = fmt_price(price_val)

        quantity = row.get("quantity", "")  # optional
        notes_bits = []
        if not raw_name:
            notes_bits.append("filled:name")
        if price_val is None:
            notes_bits.append("filled:price")
        if category == "Other":
            notes_bits.append("fallback:category")
        notes = ";".join(notes_bits)

        processed.append({
            "product_name": product_name,
            "category": category,
            "price_formatted": price_formatted,
            "quantity": quantity,
            "raw_price": raw_price,
            "notes": notes,
            "source_row": str(i),
        })

        # Lightweight progress line (no carriage returns to keep it simple)
        if chatter_enabled and i % max(1, total // 10) == 0:
            pct = int(i * 100 / total)
            print(f"[cleaner] Progress: {pct:3d}% ({i}/{total})")

        # Tiny cosmetic delay (keeps demo snappy)
        if chatter_enabled:
            time.sleep(0.002)

    chatter(chatter_enabled, CHATTER_BURSTS[3])
    chatter(chatter_enabled, CHATTER_BURSTS[4])
    chatter(chatter_enabled, CHATTER_BURSTS[5])

    # Write output
    chatter(chatter_enabled, f"Writing cleaned CSV → {args.out_path}")
    with args.out_path.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(processed)

    chatter(chatter_enabled, CHATTER_BURSTS[6])
    chatter(chatter_enabled, CHATTER_BURSTS[7], delay=0.02)

    # Final summary
    total_other = sum(1 for r in processed if r["category"] == "Other")
    total_zero  = sum(1 for r in processed if r["price_formatted"] == "$0.00")
    print("\n=== Clean Summary ===")
    print(f"Input rows:           {total}")
    print(f"Output rows:          {len(processed)}")
    print(f"Fallback categories:  {total_other}")
    print(f"Zero/filled prices:   {total_zero}")
    print(f"Output file:          {args.out_path.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)

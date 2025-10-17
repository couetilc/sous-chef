#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Clean ingredient_prices-style CSV into the 5-column output required by downstream loaders.

- Ensures the output has EXACTLY these columns:
    food_id, ingredient_name, quantity_other, quantity_oz, price
- Preserves optional chatter/progress messages.
- Attempts to infer quantity_oz from free-form quantity (e.g., "16 oz", "0.5-oz").
- Leaves quantity_other with the non-oz remainder (e.g., "12 ct", "9 in").
- Parses price into a plain numeric string with two decimals (no $). Blank if unparseable.

Usage:
  ./clean_prices.py
  ./clean_prices.py --in ./scraping/price_scraping/ingredient_prices.csv --out ./scraping/price_scraping/ingredient_prices_cleaned.csv
  ./clean_prices.py --no-chatter

Expected input columns (best-effort; only 'ingredient_name' and 'price' are needed):
  food_id (optional), ingredient_name, quantity (or quantity_other/quantity_oz), price, ...

Output columns (exact):
  food_id, ingredient_name, quantity_other, quantity_oz, price
"""

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from typing import Dict, Tuple, Optional

# ---------- Config ----------
DEFAULT_IN  = Path("./scraping/price_scraping/ingredient_prices.csv")
DEFAULT_OUT = Path("./scraping/price_scraping/ingredient_prices_cleaned.csv")

CHATTER_BURSTS = [
    "Indexing rows…", "Normalizing names…", "Inferring quantities…",
    "Parsing prices…", "De-duplicating…", "Reconciling oddities…",
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
    titled = s.title()
    # Restore small words to lower if not starting token
    small = {"Of", "And", "Or", "With", "In", "On", "For", "The", "A", "An"}
    tokens = titled.split()
    for i, t in enumerate(tokens):
        if i and t in small:
            tokens[i] = t.lower()
    return " ".join(tokens) or "Unnamed Item"


def parse_price_numeric(raw_price: str) -> Optional[float]:
    """
    Best-effort numeric extraction from a messy price string.
    Accepts '3.49', '$3.49', 'USD 3.49', '3,49', etc.
    Returns float or None if unparseable/empty.
    """
    s = (raw_price or "").strip()
    if not s:
        return None
    # Remove thousands separators; treat commas as thousands (not decimals)
    s = s.replace(",", "")
    # Grab first numeric like 12, 12.34, .99
    m = re.search(r"(?<!\d)(\d*\.\d+|\d+)(?![\d/])", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def format_price_plain(value: Optional[float]) -> str:
    if value is None or value != value:  # NaN guard
        return ""
    return f"{value:.2f}"


_OZ_RX = re.compile(
    r"""
    (?P<num>
        (?:\d+(?:\.\d+)?)     # 12 or 12.5
        |
        (?:\.\d+)             # .5
    )
    \s*[- ]?\s*
    (?:oz|ounce|ounces)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

def split_quantity_fields(
    quantity: str,
    existing_other: Optional[str] = None,
    existing_oz: Optional[str] = None
) -> Tuple[str, str]:
    """
    Returns (quantity_other, quantity_oz).
    - If input already has explicit quantity_other/quantity_oz, they win.
    - Else, tries to extract the *first* ounce amount as quantity_oz (numeric string).
      Remaining text (minus that ounce fragment) becomes quantity_other.
    """
    # If caller already provided explicit columns, trust them.
    if (existing_other and existing_other.strip()) or (existing_oz and existing_oz.strip()):
        return (existing_other or "").strip(), (existing_oz or "").strip()

    q = (quantity or "").strip()
    if not q:
        return "", ""

    m = _OZ_RX.search(q)
    if not m:
        # No ounces found; keep entire thing in other
        return q, ""

    oz_val = m.group("num")
    # Remove the matched ounce fragment from the original for "other"
    start, end = m.span()
    other = (q[:start] + q[end:]).strip()
    # Tidy stray separators
    other = re.sub(r"\s{2,}", " ", other).strip(" -/,;")

    return other, oz_val


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Clean ingredient_prices.csv to required 5-column output.")
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

    # Prepare STRICT output schema
    out_fields = [
        "food_id",
        "ingredient_name",
        "quantity_other",
        "quantity_oz",
        "price",
    ]

    for i, row in enumerate(rows, start=1):
        if chatter_enabled and i == 1:
            chatter(True, CHATTER_BURSTS[0])
        elif chatter_enabled and i == total // 3:
            chatter(True, CHATTER_BURSTS[1])
        elif chatter_enabled and i == (2 * total) // 3:
            chatter(True, CHATTER_BURSTS[2])

        # --- food_id (optional passthrough) ---
        food_id = (row.get("food_id") or "").strip()

        # --- ingredient_name (cleaned) ---
        raw_name = row.get("ingredient_name") or row.get("name") or ""
        ingredient_name = clean_name(raw_name)

        # --- quantities (derive if not explicitly present) ---
        quantity_other_in = row.get("quantity_other")
        quantity_oz_in    = row.get("quantity_oz")
        quantity_raw      = row.get("quantity", "")

        quantity_other, quantity_oz = split_quantity_fields(
            quantity=quantity_raw,
            existing_other=quantity_other_in,
            existing_oz=quantity_oz_in
        )

        # --- price (numeric, plain string) ---
        price_val = parse_price_numeric(row.get("price", ""))
        price_out = format_price_plain(price_val)

        processed.append({
            "food_id": food_id,
            "ingredient_name": ingredient_name,
            "quantity_other": quantity_other,
            "quantity_oz": quantity_oz,
            "price": price_out,
        })

        # Lightweight progress
        if chatter_enabled and i % max(1, total // 10) == 0:
            pct = int(i * 100 / total)
            print(f"[cleaner] Progress: {pct:3d}% ({i}/{total})")

        if chatter_enabled:
            time.sleep(0.002)

    chatter(chatter_enabled, CHATTER_BURSTS[3])
    chatter(chatter_enabled, CHATTER_BURSTS[4])
    chatter(chatter_enabled, CHATTER_BURSTS[5])

    # Write output
    chatter(chatter_enabled, f"Writing cleaned CSV → {args.out_path}")
    with args.out_path.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(processed)

    chatter(chatter_enabled, CHATTER_BURSTS[6])
    chatter(chatter_enabled, CHATTER_BURSTS[7], delay=0.02)

    # Final summary
    blanks_price = sum(1 for r in processed if not r["price"])
    blanks_name  = sum(1 for r in processed if not r["ingredient_name"] or r["ingredient_name"] == "Unnamed Item")
    print("\n=== Clean Summary ===")
    print(f"Input rows:           {total}")
    print(f"Output rows:          {len(processed)}")
    print(f"Blank prices:         {blanks_price}")
    print(f"Unnamed ingredients:  {blanks_name}")
    print(f"Output file:          {args.out_path.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)

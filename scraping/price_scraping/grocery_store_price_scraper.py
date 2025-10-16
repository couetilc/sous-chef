#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""
Generate ingredient_prices.csv by attaching Kroger prices to a canonical ingredient list.

Usage:
  ./grocery_store_price_scraper.py --canonical /path/to/canonical.csv --out ingredient_prices.csv

Environment variables:
  KROGER_CLIENT_ID (required)
  KROGER_CLIENT_SECRET (required)
  PAYLESS_ZIP (default: 47906)
  PAGE_LIMIT (default: 5)
  OUT (fallback if --out not provided)

Notes:
- Every row from the canonical CSV is written to the output.
- If no price is available (including on any error), quantity fields and price are left blank on that row.

Output columns:
- food_id
- ingredient_name
- quantity_other    # non-oz portion (e.g., "9 in", "12 ct")
- quantity_oz       # numeric ounces if found or derivable (e.g., "6" or "16")
- price
"""

import os, sys, csv, time, argparse, requests, re
from typing import Dict, Any, List, Optional, Tuple

# ------------------------------------
# Config
# ------------------------------------
BASE = "https://api.kroger.com/v1"
ZIP_NEAR = os.getenv("PAYLESS_ZIP", "47906")
PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", "5"))

CLIENT_ID = os.getenv("KROGER_CLIENT_ID")
CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    print("Set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET.", file=sys.stderr)
    sys.exit(1)

# Light heuristics to avoid obvious mismatches
EXCLUDE_BY_TERM = {
    "onion": ["powder", "dehydrated"],
    "garlic": ["powder", "minced", "paste"],
    "ground beef": ["patty", "patties", "burger"],
    "olive oil": ["spray"],
    "cheddar cheese": ["spray", "puffs"],
}
PREFERRED_UNITS = {
    "ground beef": ["lb"],
    "boneless skinless chicken breast": ["lb", "oz"],
    "whole milk": ["gal", "1/2 gal", "quart"],
    "eggs": ["ct"],
    "onion": ["lb", "ct"],
    "garlic": ["ct"],
    "cheddar cheese": ["oz", "lb"],
    "olive oil": ["fl oz", "liter", "ml"],
    "all purpose flour": ["lb", "oz"],
    "rice": ["lb", "oz"],
}

# ------------------------------------
# Auth & API helpers
# ------------------------------------
def get_token(scope: str = "product.compact") -> str:
    r = requests.post(
        f"{BASE}/connect/oauth2/token",
        auth=requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": scope},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    tok = j.get("access_token")
    if not tok:
        raise RuntimeError(f"Token response missing access_token: {j}")
    return tok

def find_payless_location(token: str) -> Dict[str, Any]:
    headers = {"Accept":"application/json","Authorization": f"Bearer {token}"}
    params = {"filter.zipCode.near": ZIP_NEAR, "filter.radiusInMiles": 25, "filter.limit": 50}
    r = requests.get(f"{BASE}/locations", headers=headers, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", []) or []

    def is_payless(loc: Dict[str, Any]) -> bool:
        name = (loc.get("name") or "").lower()
        chain = (loc.get("chain") or "").lower()
        return ("pay" in name and "less" in name) or ("pay" in chain and "less" in chain)

    for loc in data:
        if is_payless(loc):
            return loc
    return data[0] if data else {}

def search_products(token: str, location_id: str, term: str) -> List[Dict[str, Any]]:
    """
    Fault-tolerant search:
      - 400 / 404 => treat as no results ([])
      - 429/5xx   => retry once, then treat as no results
      - Any RequestException => []
    """
    headers = {"Accept":"application/json","Authorization": f"Bearer {token}"}
    params = {"filter.term": term, "filter.locationId": location_id, "filter.limit": PAGE_LIMIT}

    def _req():
        return requests.get(f"{BASE}/products", headers=headers, params=params, timeout=30)

    try:
        r = _req()
        if r.status_code in (400, 404):
            return []
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(0.8)
            r = _req()
            if r.status_code in (400, 404):
                return []
        r.raise_for_status()
        return r.json().get("data", []) or []
    except requests.exceptions.RequestException as e:
        # Network or other HTTP errors: log and skip
        print(f"[warn] search '{term}': {type(e).__name__}: {e}", file=sys.stderr)
        return []

# ------------------------------------
# Matching & parsing helpers
# ------------------------------------
def good_match(term: str, product: Dict[str, Any]) -> bool:
    desc = (product.get("description") or "").lower()
    if term.lower() not in desc:
        return False
    for bad in EXCLUDE_BY_TERM.get(term.lower(), []):
        if bad in desc:
            return False
    items = product.get("items") or []
    if items:
        size = (items[0].get("size") or "").lower()
        prefs = PREFERRED_UNITS.get(term.lower(), [])
        if prefs and not any(u in size for u in prefs):
            return False
    return True

def pick_product(term: str, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for p in products:
        if good_match(term, p):
            return p
    return products[0] if products else None

# ---------- size parsing ----------
_U_RE = re.compile(
    r"""^\s*
        (?P<num>\d+(?:\.\d+)?)
        \s*
        (?P<unit>
            lb|lbs|
            oz|fl\s*oz|
            ct|count|
            in|inch|inches|
            qt|pt|gal|gallon|litre|liter|l|
            ml|g|kg
        )
        s?
        \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

def _parse_piece(piece: str) -> Tuple[Optional[float], Optional[str], str]:
    """
    Returns (oz_value, normalized_unit_or_none, original_piece_trimmed).
    """
    s = piece.strip()
    m = _U_RE.match(s.replace(".", "."))
    if not m:
        return None, None, s
    num = float(m.group("num"))
    unit = m.group("unit").lower().replace(" ", "")
    if unit in ("lb", "lbs"):
        return num * 16.0, "lb", s
    if unit in ("oz",):
        return num, "oz", s
    if unit in ("floz", "flozs"):
        return num, "fl oz", s
    # Not an ounce-bearing unit
    return None, unit, s

def split_size_to_other_and_oz(size: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not size:
        return None, None
    pieces = [p.strip() for p in size.split("/") if p.strip()]
    oz_explicit: Optional[float] = None
    oz_from_lb: Optional[float] = None
    other_parts: List[str] = []

    for p in pieces:
        oz_val, unit, original = _parse_piece(p)
        if unit in ("oz", "fl oz") and oz_val is not None:
            oz_explicit = oz_val
        elif unit == "lb" and oz_val is not None:
            oz_from_lb = oz_val
            other_parts.append(original)
        else:
            other_parts.append(original)

    oz_final = oz_explicit if oz_explicit is not None else oz_from_lb
    other = " / ".join(other_parts) if other_parts else None
    oz_str = f"{oz_final:g}" if oz_final is not None else None
    return other, oz_str

def extract_qty_and_price(p: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (quantity_other, quantity_oz, price) — blanks if missing.
    """
    items = p.get("items") or []
    if not items:
        return None, None, None
    it0 = items[0]
    size = it0.get("size")
    quantity_other, quantity_oz = split_size_to_other_and_oz(size)

    price_obj = it0.get("price") or {}
    price = price_obj.get("regular")
    if price is not None:
        try:
            price_str = f"{float(price):.2f}"
        except Exception:
            price_str = None
    else:
        price_str = None

    return quantity_other, quantity_oz, price_str

# ------------------------------------
# Canonical list handling
# ------------------------------------
LIKELY_NAME_COLUMNS = ["ingredient_name","canonical_name","ingredient","name","item","description"]

def detect_name_column(header: List[str]) -> str:
    lower = [h.strip().lower() for h in header]
    for cand in LIKELY_NAME_COLUMNS:
        if cand in lower:
            return header[lower.index(cand)]
    if len(header) > 1 and header[0].strip().lower() in {"fdc_id","id"}:
        return header[1]
    return header[0]

def read_canonical_list(path: str) -> List[Tuple[str, str]]:
    """
    Returns a list of (food_id, ingredient_name) pairs.
    If no numeric ID is found in the first column, id = "".
    """
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        rows = list(r)
    if not rows:
        return []
    header, data_rows = rows[0], rows[1:]
    name_col = detect_name_column(header)
    name_idx = header.index(name_col)
    id_idx = 0 if header[0].strip().lower() in {"fdc_id", "id"} else None

    pairs: List[Tuple[str, str]] = []
    for row in data_rows:
        if len(row) <= name_idx:
            continue
        name = (row[name_idx] or "").strip()
        if not name:
            continue
        food_id = row[id_idx].strip() if (id_idx is not None and len(row) > id_idx) else ""
        pairs.append((food_id, name))
    return pairs

def make_search_term(name: str) -> str:
    parts = [p.strip() for p in name.split(",") if p.strip()]
    if not parts:
        return name.strip()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}, {parts[1]}"

# ------------------------------------
# Main
# ------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", required=True, help="Path to canonical ingredients CSV")
    ap.add_argument("--out", default=os.getenv("OUT", "ingredient_prices25.csv"), help="Output CSV path")
    args = ap.parse_args()

    canonical_rows = read_canonical_list(args.canonical)
    # Cutoff
    canonical_rows = canonical_rows[:25]
    if not canonical_rows:
        print(f"No ingredients found in {args.canonical}", file=sys.stderr)
        sys.exit(2)

    token = get_token("product.compact")
    loc = find_payless_location(token)
    if not loc:
        print(f"No Kroger-family location found near ZIP {ZIP_NEAR}", file=sys.stderr)
        sys.exit(3)
    location_id = loc["locationId"]
    store_name = loc.get("name", "Unknown Store")
    print(f"Using {store_name} (locationId={location_id})", file=sys.stderr)

    processed_cache: Dict[str, Tuple[Optional[str], Optional[str], Optional[str]]] = {}

    # Stream rows so work is never lost; write blank fields on any error/no-result.
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["food_id","ingredient_name","quantity_other","quantity_oz","price"]
        )
        w.writeheader()

        for i, (food_id, canonical_name) in enumerate(canonical_rows, 1):
            q_other = q_oz = price = None  # default to blanks

            try:
                if canonical_name in processed_cache:
                    q_other, q_oz, price = processed_cache[canonical_name]
                else:
                    search_term = make_search_term(canonical_name)
                    # Debug visibility of actual query term to stdout (not stderr)
                    print(search_term)

                    prods = search_products(token, location_id, search_term)
                    chosen = pick_product(search_term.lower(), prods)

                    if chosen:
                        q_other, q_oz, price = extract_qty_and_price(chosen)
                    # Cache even if blanks, so duplicates write the same result quickly
                    processed_cache[canonical_name] = (q_other, q_oz, price)

            except requests.exceptions.HTTPError as e:
                # Example: 401 if token expires mid-run; try a single refresh
                print(f"[warn] {canonical_name}: {type(e).__name__}: {e}", file=sys.stderr)
                try:
                    token = get_token("product.compact")
                except Exception as e2:
                    print(f"[warn] token refresh failed: {e2}", file=sys.stderr)
                # leave q_other/q_oz/price as None (blanks)

            except Exception as e:
                # Any other parsing/network hiccup: log and keep blanks
                print(f"[warn] {canonical_name}: {type(e).__name__}: {e}", file=sys.stderr)

            # Always write a row—even on errors—with blanks where unknown.
            w.writerow({
                "food_id": food_id,
                "ingredient_name": canonical_name,
                "quantity_other": q_other,
                "quantity_oz": q_oz,
                "price": price
            })

            # Periodic flush to keep file durable on disk
            if i % 50 == 0 or i == len(canonical_rows):
                f.flush()
                os.fsync(f.fileno())
                pct = (i / len(canonical_rows)) * 100
                print(f"[{i}/{len(canonical_rows)}] ({pct:.1f}%) ingredients processed", file=sys.stderr)
            # Gentle pacing
            time.sleep(0.12)

    print(f"Wrote {args.out}", file=sys.stderr)

if __name__ == "__main__":
    main()

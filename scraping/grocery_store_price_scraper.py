#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
import os, sys, csv, time, requests
from typing import Dict, Any, List, Optional

BASE = "https://api.kroger.com/v1"
ZIP_NEAR = os.getenv("PAYLESS_ZIP", "47906")
OUT = os.getenv("OUT", "ingredient_prices.csv")
PAGE_LIMIT = int(os.getenv("PAGE_LIMIT", "5"))  # fetch a few to choose a sane match

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
    headers = {"Accept":"application/json","Authorization": f"Bearer {token}"}
    params = {
        "filter.term": term,
        "filter.locationId": location_id,   # required to get price
        "filter.limit": PAGE_LIMIT,
        # do NOT set filter.fulfillment; it can over-restrict at some banners
    }
    r = requests.get(f"{BASE}/products", headers=headers, params=params, timeout=30)
    # Some inputs can 400 if Kroger rejects the term; handle gracefully
    if r.status_code == 400:
        return []
    r.raise_for_status()
    return r.json().get("data", []) or []

def good_match(term: str, product: Dict[str, Any]) -> bool:
    desc = (product.get("description") or "").lower()
    if term.lower() not in desc:
        return False
    for bad in EXCLUDE_BY_TERM.get(term, []):
        if bad in desc:
            return False
    items = product.get("items") or []
    if items:
        size = (items[0].get("size") or "").lower()
        prefs = PREFERRED_UNITS.get(term, [])
        if prefs and not any(u in size for u in prefs):
            return False
    return True

def pick_product(term: str, products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    # 1) first "good" match by heuristics
    for p in products:
        if good_match(term, p):
            return p
    # 2) fallback: first result
    return products[0] if products else None

def extract_qty_and_price(p: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    items = p.get("items") or []
    if not items:
        return None, None
    it0 = items[0]
    size = it0.get("size")
    price_obj = it0.get("price") or {}
    price = price_obj.get("regular")  # regular only
    if price is None:
        return size, None
    try:
        return size, f"{float(price):.2f}"
    except Exception:
        return size, None

def main(ingredients: List[str]) -> None:
    token = get_token("product.compact")
    loc = find_payless_location(token)
    if not loc:
        print(f"No Pay Less/Kroger-family location found near ZIP {ZIP_NEAR}", file=sys.stderr)
        sys.exit(2)

    location_id = loc["locationId"]
    store_name = loc.get("name", "Unknown Store")
    print(f"Using {store_name} (locationId={location_id})")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ingredient_name","quantity","price"])
        w.writeheader()
        for term in ingredients:
            prods = search_products(token, location_id, term)
            chosen = pick_product(term, prods)
            if not chosen:
                # write a blank price row so downstream joins still work
                w.writerow({"ingredient_name": term, "quantity": None, "price": None})
                continue
            qty, price = extract_qty_and_price(chosen)
            w.writerow({"ingredient_name": term, "quantity": qty, "price": price})
            time.sleep(0.12)  # be polite

    print(f"Wrote {OUT}")

if __name__ == "__main__":
    # Replace this list or pass terms on the CLI
    ingredients = [
        "onion",
        "garlic",
        "boneless skinless chicken breast",
        "ground beef",
        "olive oil",
        "all purpose flour",
        "eggs",
        "whole milk",
        "cheddar cheese",
        "rice",
    ]
    if len(sys.argv) > 1:
        ingredients = sys.argv[1:]
    main(ingredients)

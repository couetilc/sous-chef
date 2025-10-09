#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "httpx>=0.27",
#   "tenacity>=9.0.0",
#   "python-dotenv>=1.0.1"
# ]
# ///
"""
Generate a final ingredient_prices.csv by querying Kroger for each canonical ingredient.
If no price is available, write -1.

USAGE:
  uv run gen_prices.py \
    --input ./legacy_scraped_ingredients.csv \
    --name-col ingredient_name \
    --quantity-col quantity \
    --output ./ingredient_prices.csv

ENV (for Kroger official API):
  KROGER_CLIENT_ID=...
  KROGER_CLIENT_SECRET=...
  KROGER_LOCATION_ID=02100824          # e.g., W Lafayette Payless
  KROGER_SCOPE=product.compact         # optional; default below
  KROGER_OAUTH_URL=https://api.kroger.com/v1/connect/oauth2/token
  KROGER_PRODUCTS_URL=https://api.kroger.com/v1/products

ALT (if you already have a local proxy that returns {price: float}):
  PRICE_PROXY_BASE_URL=http://localhost:8000/search?term={term}&locationId={loc}
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Attach prices to canonical ingredients via Kroger API.")
    p.add_argument("--input", required=True, help="Path to canonical ingredients CSV (input).")
    p.add_argument("--output", default="./ingredient_prices.csv", help="Path to final prices CSV (output).")
    p.add_argument("--name-col", default="ingredient_name", help="Column in input with ingredient names.")
    p.add_argument("--quantity-col", default=None, help="Optional column in input with quantity text.")
    p.add_argument("--location-id", default=os.getenv("KROGER_LOCATION_ID", "").strip(),
                   help="Kroger locationId; can also come from KROGER_LOCATION_ID env.")
    p.add_argument("--min-score", type=float, default=0.0,
                   help="Optional fuzzy threshold (0..1) to accept a product name match. (0 means accept first).")
    p.add_argument("--sleep", type=float, default=0.0,
                   help="Optional sleep seconds between calls to be extra gentle on the API.")
    return p.parse_args()

# ---------- Kroger API helpers ----------

class KrogerClient:
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.client_id = os.getenv("KROGER_CLIENT_ID")
        self.client_secret = os.getenv("KROGER_CLIENT_SECRET")
        self.scope = os.getenv("KROGER_SCOPE", "product.compact")
        self.oauth_url = os.getenv("KROGER_OAUTH_URL", "https://api.kroger.com/v1/connect/oauth2/token")
        self.products_url = os.getenv("KROGER_PRODUCTS_URL", "https://api.kroger.com/v1/products")
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

        # Optional internal proxy override (if you already have one)
        self.proxy_url_tpl = os.getenv("PRICE_PROXY_BASE_URL", "").strip()  # e.g. http://.../search?term={term}&locationId={loc}

        self.http = httpx.Client(timeout=20.0, headers={"User-Agent": "SousChef/price-scraper"})

    def close(self):
        self.http.close()

    def _have_proxy(self) -> bool:
        return bool(self.proxy_url_tpl)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _proxy_price(self, term: str) -> Optional[float]:
        url = self.proxy_url_tpl.format(term=httpx.QueryParams({"": term})[0], loc=self.location_id)
        # If template didn’t include {term} or {loc}, append as query
        if "{term}" not in self.proxy_url_tpl and "{loc}" not in self.proxy_url_tpl:
            url = f"{self.proxy_url_tpl}&term={httpx.utils.quote(term)}&locationId={self.location_id}"
        r = self.http.get(url)
        r.raise_for_status()
        data = r.json()
        # Expect { "price": 3.49 } or { "price": null }
        price = data.get("price", None)
        if price is None:
            return None
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    def _ensure_token(self):
        # Refresh 30s before expiry
        now = time.time()
        if self._token and now < (self._token_expiry - 30):
            return

        if not self.client_id or not self.client_secret:
            raise RuntimeError("KROGER_CLIENT_ID / KROGER_CLIENT_SECRET not set (and no PRICE_PROXY_BASE_URL provided).")

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "scope": self.scope,
        }
        auth = (self.client_id, self.client_secret)
        r = self.http.post(self.oauth_url, headers=headers, data=data, auth=auth)
        r.raise_for_status()
        tok = r.json()
        self._token = tok["access_token"]
        self._token_expiry = time.time() + int(tok.get("expires_in", 1800))

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def _search_products_raw(self, term: str) -> dict:
        if self._have_proxy():
            # If you have a proxy, use that path instead of official API
            price = self._proxy_price(term)
            return {"__proxy_price__": price}

        self._ensure_token()
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {
            "filter.term": term,
            "filter.locationId": self.location_id,
            "filter.limit": 10,
        }
        r = self.http.get(self.products_url, headers=headers, params=params)
        # Basic handling for 401 -> refresh token once
        if r.status_code == 401:
            self._token = None
            self._token_expiry = 0
            self._ensure_token()
            headers = {"Authorization": f"Bearer {self._token}"}
            r = self.http.get(self.products_url, headers=headers, params=params)

        if r.status_code == 429:
            # Tenacity will back off and retry
            r.raise_for_status()

        r.raise_for_status()
        return r.json()

    def fetch_best_price(self, term: str) -> Optional[float]:
        """
        Return the lowest available price for the search term at the given location.
        If no price is found, return None.
        """
        data = self._search_products_raw(term)

        # Proxy path short-circuit
        if "__proxy_price__" in data:
            return data["__proxy_price__"]

        # Official Kroger response: typically {"data": [ ... products ... ]}
        products = data.get("data") or []
        best: Optional[float] = None

        for prod in products:
            items = prod.get("items") or []
            for it in items:
                price_info = it.get("price") or {}
                # Prefer promo if present, else regular
                price = price_info.get("promo")
                if price is None:
                    price = price_info.get("regular")
                try:
                    price_f = float(price) if price is not None else None
                except (TypeError, ValueError):
                    price_f = None
                if price_f is None:
                    continue
                if best is None or price_f < best:
                    best = price_f

        return best

# ---------- I/O & Orchestration ----------

def read_existing_prices(path: Path) -> Dict[Tuple[str, Optional[str]], str]:
    """
    If output already exists, read it so we can resume without re-querying.
    Keyed by (ingredient_name, quantity_or_None) -> price_str
    """
    if not path.exists():
        return {}
    existing = {}
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Accept either 2 or 3 column shape
        cols = reader.fieldnames or []
        name_key = "ingredient_name" if "ingredient_name" in cols else (cols[0] if cols else "ingredient_name")
        quantity_key = "quantity" if "quantity" in cols else None
        price_key = "price" if "price" in cols else (cols[-1] if cols else "price")

        for row in reader:
            name = (row.get(name_key) or "").strip()
            qty = (row.get(quantity_key).strip() if quantity_key else None) if row.get(quantity_key) is not None else None
            price = (row.get(price_key) or "").strip()
            if name:
                existing[(name, qty)] = price
    return existing

def main():
    load_dotenv()
    args = parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    if not args.location_id:
        # If you’re using official Kroger API, location is required.
        # If you use a proxy that doesn’t care, you can set any string here.
        print("Warning: --location-id not provided (env KROGER_LOCATION_ID). Proceeding anyway.", file=sys.stderr)

    # Prepare client
    client = KrogerClient(location_id=args.location_id)

    # Resume support
    existing = read_existing_prices(out_path)

    # Open output and ensure header
    out_exists = out_path.exists()
    with out_path.open("a+", newline="", encoding="utf-8") as outf, in_path.open("r", newline="", encoding="utf-8") as inf:
        in_reader = csv.DictReader(inf)
        name_col = args.name_col
        quantity_col = args.quantity_col if args.quantity_col and args.quantity_col in (in_reader.fieldnames or []) else None

        # Standardize header
        fieldnames = ["ingredient_name"]
        if quantity_col:
            fieldnames.append("quantity")
        fieldnames.append("price")

        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        if not out_exists:
            writer.writeheader()

        # Build a quick set of already done keys for resume
        done_keys = set(existing.keys())

        seen = set()  # avoid duplicate ingredient rows from input
        for row in in_reader:
            name = (row.get(name_col) or "").strip()
            if not name:
                continue
            qty = (row.get(quantity_col) or "").strip() if quantity_col else None

            key = (name, qty)
            if key in seen:
                continue
            seen.add(key)

            # Already have it? Re-emit existing price (for idempotency)
            if key in done_keys:
                writer.writerow({
                    "ingredient_name": name,
                    **({"quantity": qty} if quantity_col else {}),
                    "price": existing[key],
                })
                continue

            # Fetch price
            try:
                price = client.fetch_best_price(name)
            except Exception as e:
                # On any error, write -1
                price = None

            # Respect gentle pacing if requested
            if args.sleep > 0:
                time.sleep(args.sleep)

            price_out = f"{price:.2f}" if isinstance(price, (float, int)) else "-1"
            writer.writerow({
                "ingredient_name": name,
                **({"quantity": qty} if quantity_col else {}),
                "price": price_out,
            })

    client.close()
    print(f"Done. Wrote: {out_path}")

if __name__ == "__main__":
    main()

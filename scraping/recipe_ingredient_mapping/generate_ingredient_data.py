#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pandas>=2.0",
#   "openai>=1.50.0",
#   "python-dateutil>=2.8.2",
# ]
# ///
"""
Price-only estimator using canonical (per-100g) prices.
NO LLM for ingredient lines.
LLM is called ONLY for recipe-level outliers (based on price per serving).

Outputs:
- recipe_ingredients_out.csv  (per-ingredient audit; price per serving)
- recipe_totals_out.csv       (per-recipe: calc price, LLM price for outliers, and final price)

Outlier policy (defaults, configurable via CLI):
- If calc price_per_serving_usd < --low-threshold  OR  > --high-threshold,
  query LLM ONCE for the recipe title to estimate per-serving/total prices.
"""

from __future__ import annotations

import argparse, csv, json, os, re, sys, time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

import pandas as pd

# ----------------------------- Unit & density tables -----------------------------

UNIT_MAP_WEIGHT = {
    "g": 1.0, "gram": 1.0, "grams": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
    "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
    "oz": 28.349523125, "ounce": 28.349523125, "ounces": 28.349523125,
    "lb": 453.59237, "lbs": 453.59237, "pound": 453.59237, "pounds": 453.59237,
}

UNIT_MAP_VOLUME = {
    "ml": 1.0, "milliliter": 1.0, "milliliters": 1.0,
    "l": 1000.0, "liter": 1000.0, "liters": 1000.0,
    "tsp": 4.92892, "teaspoon": 4.92892, "teaspoons": 4.92892,
    "tbsp": 14.7868, "tablespoon": 14.7868, "tablespoons": 14.7868,
    "cup": 240.0, "cups": 240.0,
    "fl oz": 29.5735, "floz": 29.5735, "fluid ounce": 29.5735, "fluid ounces": 29.5735,
}

DENSITY_KEYWORDS = [
    ("olive oil", 0.91), ("canola oil", 0.91), ("vegetable oil", 0.91), ("oil", 0.91),
    ("butter", 0.96), ("milk", 1.03), ("water", 1.00),
    ("broth", 1.00), ("stock", 1.00), ("vinegar", 1.00),
    ("honey", 1.42), ("salt", 1.20),
    ("sugar", 0.85), ("brown sugar", 0.75),
    ("flour", 0.53), ("rice", 0.85),
]

EACH_MASS = {
    "egg": 50.0, "clove garlic": 3.0, "garlic clove": 3.0, "garlic": 3.0,
    "shallot": 40.0, "onion": 110.0, "lime": 70.0, "lemon": 90.0,
    "avocado": 150.0, "bell pepper": 120.0, "strip bacon": 12.0,
    "slice bacon": 12.0, "slice bread": 25.0, "potato": 170.0,
}

TRAILING_DESCRIPTORS = [
    "divided","to taste","or to taste","at room temperature","softened","melted",
    "minced","sliced","diced","chopped","halved","peeled","seeded","rinsed",
    "drained","beaten","grated","shredded","large","small","medium","more as needed",
]

# ----------------------------- Regex helpers -----------------------------

UNITS_PATTERN = r"(?:g|gram|grams|kg|mg|oz|ounce|ounces|lb|lbs|pound|pounds|ml|milliliter|milliliters|l|liter|liters|tsp|teaspoon|teaspoons|tbsp|tablespoon|tablespoons|cup|cups|fl\s*oz|floz|dash|pinch|bunch|head|can|package|packages|bag|stick|slice|link|clove|cloves)"
PAREN_SIZE_RE = re.compile(
    r"\((?P<qty>\d*\.?\d+(?:/\d+)?)\s*(?P<unit>(?:fl\s*oz|floz|oz|ounce|ounces|g|gram|grams|kg|lb|pound|pounds|ml|milliliter|milliliters|l|liter|liters))\)",
    re.IGNORECASE,
)
LEADING_QTY_UNIT_RE = re.compile(
    rf"^\s*(?P<qty>\d+[\u00BC-\u00BE\u2150-\u215E]?|\d*\.\d+|\d+\s*/\s*\d+)\s*(?P<unit>{UNITS_PATTERN})?\b(?:\s+of\b)?\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
SECONDARY_FRONT_TOKEN_RE = re.compile(
    rf"^\s*(?P<qty>\d+(?:\.\d+)?|\d+\s*/\s*\d+)\s*(?P<unit>{UNITS_PATTERN})\b\s*(?P<rest>.*)$",
    re.IGNORECASE,
)

UNICODE_FRACTIONS = {"¼":"1/4","½":"1/2","¾":"3/4","⅐":"1/7","⅑":"1/9","⅒":"1/10","⅓":"1/3","⅔":"2/3","⅕":"1/5","⅖":"2/5","⅗":"3/5","⅘":"4/5","⅙":"1/6","⅚":"5/6","⅛":"1/8","⅜":"3/8","⅝":"5/8","⅞":"7/8"}
LIQUID_KEYWORDS_FOR_OZ = ["oil","broth","stock","milk","water","vinegar"]

# ----------------------------- Dataclass -----------------------------

@dataclass
class ParsedIngredient:
    raw: str
    qty: Optional[float]
    unit: Optional[str]
    name: str
    mass_g: Optional[float]
    source: str
    fallback_reason: Optional[str] = None

# ----------------------------- Parsing utils -----------------------------

SCRAPE_FIXES = [
    (r"\bpotatoe\b", "potato"),
    (r"\bdashe?\b", "dash"),
    (r"\bpinche\b", "pinch"),
    (r"\s+,", ","),     # stray space before comma
    (r",\s*$", ""),     # trailing comma
]

def normalize_unicode_fractions(s: str) -> str:
    for k,v in UNICODE_FRACTIONS.items():
        s = s.replace(k, v) if k in s else s
    return s

def normalize_text_noise(s: str) -> str:
    s = s.strip()
    for pat, repl in SCRAPE_FIXES:
        s = re.sub(pat, repl, s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def parse_fraction_to_float(s: str) -> Optional[float]:
    s = s.strip()
    if " " in s and "/" in s:
        a,b = s.split(" ",1)
        try:
            base = float(a); num,den = b.split("/",1)
            return base + float(num)/float(den)
        except: pass
    if "/" in s:
        try:
            num,den = s.split("/",1)
            return float(num)/float(den)
        except: return None
    try: return float(s)
    except: return None

def unit_norm(u: Optional[str]) -> Optional[str]:
    if not u: return None
    u = u.strip().lower().replace(".","")
    u = u.replace("fl","fl ").strip() if u.startswith("floz") else u
    if u in {"ounce","ounces"}: return "oz"
    if u in {"tsps","tspn","tspns"}: return "tsp"
    if u in {"tbs","tbspn","tbspns"}: return "tbsp"
    if u in {"ltrs","ltr"}: return "l"
    if u in {"floz","flounce","flounces"}: return "fl oz"
    return u

def clean_descriptors(name: str) -> str:
    name = normalize_text_noise(name)
    for w in TRAILING_DESCRIPTORS:
        name = re.sub(rf"\b{re.escape(w)}\b", "", name, flags=re.IGNORECASE)
    name = name.replace(" ,", ",").strip().strip(",")
    name = re.sub(r"\s+", " ", name)
    return name

def qty_unit_name_parse(ing: str) -> Tuple[Optional[float], Optional[str], str]:
    s = normalize_unicode_fractions(ing)
    s = normalize_text_noise(s)
    m = LEADING_QTY_UNIT_RE.match(s)
    if not m:
        return None, None, clean_descriptors(s)
    qty_s = (m.group("qty") or "").strip()
    unit = unit_norm(m.group("unit"))
    rest = clean_descriptors(m.group("rest") or "")
    qty = parse_fraction_to_float(qty_s) if qty_s else None

    # Pull a missed front "0.75 cup" etc. from rest if needed
    if (qty is None or unit is None) and rest:
        m2 = SECONDARY_FRONT_TOKEN_RE.match(rest)
        if m2:
            qty2 = parse_fraction_to_float(m2.group("qty"))
            unit2 = unit_norm(m2.group("unit"))
            rest2 = clean_descriptors(m2.group("rest") or "")
            if qty is None and qty2 is not None: qty = qty2
            if unit is None and unit2 is not None: unit = unit2
            rest = rest2

    # Promote count-words (bunch/head/can/...) to units if still missing
    m3 = re.match(r"^(bunch|head|can|package|packages|bag|stick|slice|link|clove|cloves)\b\s*(.*)$", rest, flags=re.IGNORECASE)
    if unit is None and m3:
        unit = m3.group(1).lower()
        rest = clean_descriptors(m3.group(2) or "")

    return qty, unit, rest

def find_density(name_lower: str) -> Optional[float]:
    for key,d in DENSITY_KEYWORDS:
        if key in name_lower: return d
    return None

def estimate_each_mass(name_lower: str) -> Optional[float]:
    for key,g in EACH_MASS.items():
        if key in name_lower: return g
    if name_lower.endswith("s"):
        return EACH_MASS.get(name_lower[:-1])
    return None

def oz_is_fluid(name_lower: str) -> bool:
    return any(k in name_lower for k in LIQUID_KEYWORDS_FOR_OZ)

def to_grams(qty: float, unit: Optional[str], name_lower: str) -> Tuple[Optional[float], str, Optional[str]]:
    if qty is None:
        ge = estimate_each_mass(name_lower)
        return (ge, "each_heuristic", None) if ge else (None, "unparsed_qty", "no_quantity")
    if unit:
        u = "fl oz" if unit=="oz" and oz_is_fluid(name_lower) else unit
        if u in UNIT_MAP_WEIGHT:
            return qty*UNIT_MAP_WEIGHT[u], "rule_weight", None
        if u in UNIT_MAP_VOLUME:
            ml = qty*UNIT_MAP_VOLUME[u]; dens = find_density(name_lower)
            return ((ml*dens, "density", None) if dens else (None, "density_missing", "volume_without_density"))
        ge = estimate_each_mass(name_lower)
        return ((qty*ge, "each_heuristic", "unknown_unit_used_each") if ge else (None,"unknown_unit",u))
    ge = estimate_each_mass(name_lower)
    return ((qty*ge, "each_heuristic", None) if ge else (None,"no_unit",None))

def embedded_parenthetical_mass(s: str) -> Optional[Tuple[float,str]]:
    m = PAREN_SIZE_RE.search(s)
    if not m: return None
    qty = parse_fraction_to_float(m.group("qty"))
    unit = unit_norm(m.group("unit"))
    if qty is None or unit is None: return None
    return qty, unit

def apply_parenthetical_hint(base_qty: Optional[float], unit: Optional[str], name: str, name_lower: str):
    """
    Returns (maybe_mass_g, unit_out, hint_used, count_for_cache)
    """
    hint = embedded_parenthetical_mass(name)
    count_for_cache = base_qty if base_qty is not None else 1.0
    if not hint: return base_qty, unit, None, count_for_cache
    hq, hu = hint
    if hu in UNIT_MAP_WEIGHT:
        mass_g = count_for_cache * hq * UNIT_MAP_WEIGHT[hu]
        return mass_g, None, "parenthetical_weight", count_for_cache
    if hu in UNIT_MAP_VOLUME:
        ml = hq * UNIT_MAP_VOLUME[hu]; dens = find_density(name_lower)
        if dens:
            mass_g = count_for_cache * ml * dens
            return mass_g, None, "parenthetical_volume_with_density", count_for_cache
        else:
            return base_qty, unit, "parenthetical_volume_missing_density", count_for_cache
    return base_qty, unit, None, count_for_cache

# ----------------------------- LLM (recipe-level) -----------------------------

def llm_recipe_price_estimate(recipe_title: str, servings: float) -> Tuple[Optional[float], Optional[float], float]:
    """
    Ask OpenAI for a price estimate based on the RECIPE TITLE only.
    Returns (price_per_serving_usd, total_price_usd, confidence). On failure: (None, None, 0.0).
    """
    try:
        from openai import OpenAI
    except Exception as e:
        sys.stderr.write(f"[LLM] openai import error: {e}\n"); return None, None, 0.0
    if not os.getenv("OPENAI_API_KEY"):
        sys.stderr.write("[LLM] OPENAI_API_KEY not set; skipping.\n"); return None, None, 0.0

    client = OpenAI()
    prompt = (
        "Estimate the typical US grocery cost for the dish named below. "
        "Return ONLY JSON like {\"price_per_serving_usd\": 1.23, \"total_price_usd\": 4.92, \"confidence\": 0.7}.\n"
        f"RECIPE TITLE: {recipe_title}\n"
        f"SERVINGS: {servings}\n"
        "If you are unsure, make a reasonable estimate."
    )

    # Try Responses API, then fall back to Chat Completions
    try:
        resp = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)
        text = getattr(resp,"output_text",None) or str(resp)
        data = json.loads(text)
        pps = float(data["price_per_serving_usd"])
        tot = float(data["total_price_usd"])
        conf = float(data.get("confidence", 0.7))
        return pps, tot, conf
    except TypeError:
        pass
    except Exception as e:
        sys.stderr.write(f"[LLM] responses API error: {e}\n")

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You return ONLY compact JSON with keys price_per_serving_usd, total_price_usd, confidence."},
                {"role":"user","content":prompt},
            ],
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        data = json.loads(text)
        pps = float(data["price_per_serving_usd"])
        tot = float(data["total_price_usd"])
        conf = float(data.get("confidence", 0.7))
        return pps, tot, conf
    except Exception as e:
        sys.stderr.write(f"[LLM] chat.completions error: {e}\n")
        return None, None, 0.0

# ----------------------------- Core processing -----------------------------

def process(recipes_path: str,
            canonical_path: str,
            out_ing_path: str,
            out_rec_path: str,
            tiny_threshold_g: float,
            low_threshold: float,
            high_threshold: float,
            log_every: int,
            max_recipes: Optional[int],
            skip_llm_outliers: bool) -> None:

    start_all = time.time()

    # Canonical: only price_g needed (per 100 g)
    canon_raw = pd.read_csv(canonical_path, dtype={"food_id": str})
    canon_raw["price_g"] = pd.to_numeric(canon_raw["price_g"], errors="coerce")
    canon = (
        canon_raw.drop_duplicates(subset=["food_id"], keep="first")
                 .set_index("food_id")[["price_g"]]
                 .fillna(0.0)
    )
    print(f"[INFO] canonical: {len(canon_raw):,} rows → {len(canon):,} unique food_id", flush=True)

    # Recipes
    df = pd.read_csv(recipes_path, dtype=str).fillna("")
    total_recipes = len(df) if not max_recipes else min(max_recipes, len(df))
    print(f"[INFO] recipes: processing {total_recipes:,}/{len(df):,}", flush=True)

    required_cols = {"title", "ingredients", "ingredients_id", "servings"}
    missing = required_cols - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    ing_rows: List[Dict] = []
    recipe_rows: List[Dict] = []

    warn_mismatch = 0
    outliers = 0
    llm_calls = 0
    loop_start = time.time()

    for idx, row in df.iloc[:total_recipes].iterrows():
        title = row["title"]
        try:
            servings = float(row.get("servings","1") or "1")
            if servings <= 0: raise ValueError
        except Exception:
            servings = 1.0

        ing_field = row["ingredients"]; ids_field = row["ingredients_id"]
        ing_list = [s.strip() for s in ing_field.split(" | ")] if ing_field else []
        id_list  = [s.strip() for s in ids_field.split(" | ")] if ids_field else []

        if len(ing_list) != len(id_list):
            id_list2 = [s.strip() for s in ids_field.split("|")] if ids_field else []
            if len(ing_list) == len(id_list2):
                id_list = id_list2
            else:
                warn_mismatch += 1
                if warn_mismatch <= 5:
                    sys.stderr.write(f"[WARN] mismatch ing/id in '{title}' (row {idx}) — skipped\n")
                continue

        # Price per serving accumulator (ingredients-only, canonical only)
        recipe_price_per_serving_calc = 0.0

        for ing_str, fid in zip(ing_list, id_list):
            raw = ing_str.strip()
            fid_str = (fid or "").strip() or None

            # Parse + parenthetical hint
            qty, unit, name = qty_unit_name_parse(raw)
            name_lower = name.lower()
            qty2, unit2, hint_used, _unused = apply_parenthetical_hint(qty, unit, raw, name_lower)
            grams_from_hint = None
            if unit2 is None and isinstance(qty2,(int,float)) and hint_used and "parenthetical" in hint_used:
                grams_from_hint = float(qty2); qty = unit = None
            else:
                qty, unit = qty2, (unit2 if unit2 not in {"g"} else None)

            # Convert to grams (for canonical price path)
            if grams_from_hint is not None:
                mass_g, source, fallback_reason = grams_from_hint, "parenthetical", None
            else:
                mass_g, source, fallback_reason = to_grams(qty, unit, name_lower)

            # Compute price if canonical available
            price_usd = 0.0
            if mass_g is not None and mass_g < tiny_threshold_g:
                price_usd = 0.0
            elif mass_g is not None and fid_str and fid_str in canon.index:
                price_per_100g = float(canon.loc[fid_str]["price_g"])
                price_usd = price_per_100g * (mass_g / 100.0)
            else:
                # No LLM here by design; unknowns contribute $0
                price_usd = 0.0

            recipe_price_per_serving_calc += (price_usd or 0.0)

            # per-ingredient audit row (per serving)
            ing_rows.append({
                "recipe_title": title,
                "ingredient_raw": raw,
                "ingredient_name": name,
                "food_id": fid_str or "",
                "mass_g": f"{mass_g:.4f}" if mass_g is not None else "",
                "price_usd_per_serving_calc": f"{(price_usd or 0.0):.4f}",
                "note": "" if price_usd > 0 else (fallback_reason or "no_canonical_or_tiny"),
            })

        # Per-recipe totals (calc)
        total_price_usd_calc = recipe_price_per_serving_calc * (servings or 1.0)

        # Outlier detection
        is_outlier = (recipe_price_per_serving_calc < low_threshold) or (recipe_price_per_serving_calc > high_threshold)

        # Optional LLM estimate for outliers (recipe-level)
        llm_pps = None
        llm_total = None
        llm_conf = None
        if is_outlier and not skip_llm_outliers:
            outliers += 1
            llm_calls += 1
            llm_pps, llm_total, llm_conf = llm_recipe_price_estimate(title, servings)

        # Final price selection
        final_pps = llm_pps if (llm_pps is not None) else recipe_price_per_serving_calc
        final_total = llm_total if (llm_total is not None) else total_price_usd_calc

        # per-recipe row
        recipe_rows.append({
            "recipe_title": title,
            "servings": f"{servings:.0f}" if float(servings).is_integer() else f"{servings}",
            "price_per_serving_usd_calc": f"{recipe_price_per_serving_calc:.4f}",
            "total_price_usd_calc": f"{total_price_usd_calc:.4f}",
            "is_outlier": "yes" if is_outlier else "no",
            "llm_price_per_serving_usd": f"{llm_pps:.4f}" if llm_pps is not None else "",
            "llm_total_price_usd": f"{llm_total:.4f}" if llm_total is not None else "",
            "llm_confidence": f"{llm_conf:.3f}" if llm_conf is not None else "",
            "final_price_per_serving_usd": f"{final_pps:.4f}",
            "final_total_price_usd": f"{final_total:.4f}",
        })

        # Progress
        i = idx + 1
        if i % log_every == 0 or i == total_recipes:
            elapsed = time.time() - loop_start
            print(f"[PROGRESS] {i:,}/{total_recipes:,} recipes | {elapsed:,.1f}s | outliers {outliers}, LLM calls {llm_calls}", flush=True)
            loop_start = time.time()

    # Write outputs
    pd.DataFrame(ing_rows).to_csv(out_ing_path, index=False)
    pd.DataFrame(recipe_rows).to_csv(out_rec_path, index=False)

    print(f"[DONE] wrote {len(ing_rows):,} ingredient rows -> {out_ing_path}")
    print(f"[DONE] wrote {len(recipe_rows):,} recipe totals -> {out_rec_path}")
    print(f"[STATS] outliers={outliers}, LLM calls={llm_calls}, elapsed={time.time()-start_all:,.1f}s", flush=True)

# ----------------------------- CLI -----------------------------

def main():
    ap = argparse.ArgumentParser(description="Price-only estimator (canonical). LLM only for recipe-level outliers.")
    ap.add_argument("--recipes", required=True, help="Path to recipes_with_matches.csv")
    ap.add_argument("--canonical", required=True, help="Path to canonical_list.csv")
    ap.add_argument("--out-ingredients", default="recipe_ingredients_out.csv", help="Per-ingredient output CSV (audit)")
    ap.add_argument("--out-recipes", default="recipe_totals_out.csv", help="Per-recipe totals CSV")
    ap.add_argument("--tiny-threshold-g", type=float, default=2.0, help="If known mass < threshold, treat as $0 and skip")
    ap.add_argument("--low-threshold", type=float, default=0.15, help="Outlier lower bound for price_per_serving_usd")
    ap.add_argument("--high-threshold", type=float, default=20.0, help="Outlier upper bound for price_per_serving_usd")
    ap.add_argument("--log-every", type=int, default=500, help="Print progress every N recipes")
    ap.add_argument("--max-recipes", type=int, default=None, help="Process at most N recipes (trial runs)")
    ap.add_argument("--skip-llm-outliers", action="store_true", help="Do not use LLM even for outliers")
    args = ap.parse_args()

    process(
        recipes_path=args.recipes,
        canonical_path=args.canonical,
        out_ing_path=args.out_ingredients,
        out_rec_path=args.out_recipes,
        tiny_threshold_g=args.tiny_threshold_g,
        low_threshold=args.low_threshold,
        high_threshold=args.high_threshold,
        log_every=args.log_every,
        max_recipes=args.max_recipes,
        skip_llm_outliers=args.skip_llm_outliers,
    )

if __name__ == "__main__":
    main()

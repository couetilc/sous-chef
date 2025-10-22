#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "beautifulsoup4",
#   "requests",
# ]
# ///
import csv
import json
import time
import re
import sys
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------- Config ----------------

HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
# Only accept canonical recipe URLs with a 6-digit numeric id (per user's request)
RECIPE_RE = re.compile(r"^https?://www\.allrecipes\.com/recipe/\d{6}/.+/?$", re.I)

# Default input files (can be overridden by CLI args)
DEFAULT_SITEMAPS = [
  "scraping/recipe_scraping/sitemaps/sitemap1.txt",
  "scraping/recipe_scraping/sitemaps/sitemap2.txt",
  "scraping/recipe_scraping/sitemaps/sitemap3.txt",
  "scraping/recipe_scraping/sitemaps/sitemap4.txt",
]

OUT_CSV = "scraping/recipe_scraping/recipe_csv_files/recipes_final.csv"
REQUEST_TIMEOUT = 20

# ---------------- Helpers ----------------

def is_recipe_link(href: str) -> bool:
  if not href or not href.startswith("http"):
    return False
  try:
    parsed = urlparse(href)
    if not parsed.netloc.endswith("allrecipes.com"):
      return False
    return bool(RECIPE_RE.match(href))
  except Exception:
    return False

def fetch(url: str) -> requests.Response | None:
  try:
    r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    if r.status_code == 200:
      return r
  except requests.RequestException:
    pass
  return None

def _clean_text(s: str) -> str:
  s = s.replace("\xa0", " ").strip()
  s = re.sub(r"\s+", " ", s)
  return s

def _flatten_instructions(instr):
  """Normalize recipeInstructions into a flat list of step strings."""
  steps = []

  def add_step(x):
    if not x:
      return
    if isinstance(x, str):
      t = _clean_text(x)
      if t:
        steps.append(t)
    elif isinstance(x, dict):
      t = _clean_text(x.get("text") or x.get("name") or "")
      if t:
        steps.append(t)

  if isinstance(instr, list):
    for item in instr:
      if isinstance(item, dict) and item.get("@type") == "HowToSection":
        for sub in item.get("itemListElement", []):
          add_step(sub)
      else:
        add_step(item)
  elif isinstance(instr, dict):
    if instr.get("@type") == "HowToSection":
      for sub in instr.get("itemListElement", []):
        add_step(sub)
    else:
      add_step(instr)
  elif isinstance(instr, str):
    for p in [p.strip() for p in re.split(r"[\r\n]+", instr) if p.strip()]:
      steps.append(_clean_text(p))

  # Deduplicate while preserving order
  seen, deduped = set(), []
  for s in steps:
    if s not in seen:
      seen.add(s)
      deduped.append(s)
  return deduped

def _image_from_jsonld(image_field):
  """
  image can be a string URL, a dict with 'url', or a list of either.
  Return a single URL string if possible.
  """
  if not image_field:
    return None
  if isinstance(image_field, str):
    return image_field.strip()
  if isinstance(image_field, dict):
    return (image_field.get("url") or "").strip() or None
  if isinstance(image_field, list):
    # pick the first usable
    for it in image_field:
      u = _image_from_jsonld(it)
      if u:
        return u
  return None

# ---- New utility helpers for times/servings/nutrition ----

_ISO_DUR_RE = re.compile(
  r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$",
  re.I
)

def iso8601_to_minutes(val: str | None) -> int | None:
  """
  Convert ISO-8601 duration like 'PT1H30M' or 'PT45M' or 'P0DT20M' to minutes.
  Returns None if parsing fails.
  """
  if not val or not isinstance(val, str):
    return None
  m = _ISO_DUR_RE.match(val.strip())
  if not m:
    return None
  days = int(m.group("days") or 0)
  hours = int(m.group("hours") or 0)
  minutes = int(m.group("minutes") or 0)
  seconds = int(m.group("seconds") or 0)
  total_min = days * 24 * 60 + hours * 60 + minutes + (seconds // 60)
  return total_min if total_min > 0 else (0 if any([days, hours, minutes, seconds]) else None)

_NUMERIC_RE = re.compile(r"[-+]?\d*\.?\d+")
_INT_RE = re.compile(r"\d+")

def parse_number(text: str) -> float | None:
  if not text:
    return None
  m = _NUMERIC_RE.search(text.replace(",", ""))
  return float(m.group(0)) if m else None

def parse_int(text: str) -> int | None:
  if not text:
    return None
  m = _INT_RE.search(text.replace(",", ""))
  return int(m.group(0)) if m else None

def normalize_servings(yield_field) -> str:
  """
  Best-effort to extract a numeric servings value; fall back to cleaned text.
  yield_field can be a string, number, or list (Allrecipes sometimes gives array).
  """
  raw = ""
  if isinstance(yield_field, list) and yield_field:
    raw = " ".join([str(x) for x in yield_field])
  elif isinstance(yield_field, (str, int, float)):
    raw = str(yield_field)
  raw = _clean_text(raw)
  if not raw:
    return ""
  n = parse_int(raw)
  return str(n) if n is not None else raw

def clean_grams(val: str | None) -> str:
  """
  Extract numeric grams from strings like '15 g', '15g', '15.2 grams'.
  Returns '' on failure.
  """
  if not val:
    return ""
  n = parse_number(val)
  return f"{n:.2f}".rstrip("0").rstrip(".") if n is not None else ""

def clean_calories(val: str | None) -> str:
  """
  Extract numeric calories from strings like '433 calories' or '433 kcal'.
  Returns '' on failure.
  """
  if not val:
    return ""
  n = parse_int(val)
  return str(n) if n is not None else ""

# ---------------- Sitemap parsing ----------------

def extract_recipe_urls_from_xml_text(text: str):
  """
  Extract <loc> URLs from a sitemap-like XML string.
  Only returns recipe URLs that match RECIPE_RE.
  Normalizes by stripping trailing slash.
  """
  urls = set()
  # Try XML parse
  try:
    root = ET.fromstring(text)
    for elem in root.iter():
      if elem.tag.endswith("loc"):
        url = (elem.text or "").strip()
        if url and RECIPE_RE.match(url):
          urls.add(url.rstrip("/"))
    return urls
  except ET.ParseError:
    pass  # fallback to regex

  # Fallback regex
  for m in re.finditer(r"<loc>(.*?)</loc>", text, flags=re.I|re.S):
    url = (m.group(1) or "").strip()
    if url and RECIPE_RE.match(url):
      urls.add(url.rstrip("/"))
  return urls

def load_recipe_urls_from_sitemaps(paths):
  all_urls = []
  for p in paths:
    path = Path(p)
    if not path.exists():
      print(f"[warn] sitemap file not found: {path}")
      continue
    try:
      text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
      text = path.read_bytes().decode("utf-8", errors="ignore")
    urls = extract_recipe_urls_from_xml_text(text)
    print(f"Found {len(urls):,} recipe URLs in {path.name}")
    all_urls.extend(urls)
  # Deduplicate while preserving order
  seen, unique = set(), []
  for u in all_urls:
    if u not in seen:
      seen.add(u)
      unique.append(u)
  print(f"Total unique recipe URLs: {len(unique):,}")
  return unique

# ---------------- Extractors ----------------

def extract_from_jsonld(soup: BeautifulSoup):
  """
  Return a dict with fields:
  title, ingredients, steps, image_url,
  prep_time_min, cook_time_min, total_time_min, servings,
  calories_per_serving, fat_g, carbs_g, protein_g
  (Some may be empty strings.)
  """
  for tag in soup.find_all("script", type="application/ld+json"):
    raw = tag.string or ""
    if not raw.strip():
      continue
    try:
      data = json.loads(raw)
    except Exception:
      continue

    nodes = []
    if isinstance(data, dict):
      nodes = [data] + (data.get("@graph") or [])
    elif isinstance(data, list):
      nodes = data

    for node in nodes:
      if not isinstance(node, dict):
        continue
      types = node.get("@type")
      if isinstance(types, str):
        types = [types]
      if types and "Recipe" in types:
        title = (node.get("name") or "").strip() or None

        # Ingredients
        ingredients = node.get("recipeIngredient") or []
        if isinstance(ingredients, list):
          ingredients = [_clean_text(i) for i in ingredients if isinstance(i, str) and _clean_text(i)]
        else:
          ingredients = []

        # Steps
        steps = []
        instr = node.get("recipeInstructions")
        if instr:
          steps = _flatten_instructions(instr)

        # Image
        image_url = _image_from_jsonld(node.get("image"))

        # Times (ISO-8601 durations)
        prep_time_min = iso8601_to_minutes(node.get("prepTime"))
        cook_time_min = iso8601_to_minutes(node.get("cookTime"))
        total_time_min = iso8601_to_minutes(node.get("totalTime"))

        # Servings
        servings = normalize_servings(node.get("recipeYield"))

        # Nutrition
        n = node.get("nutrition") or {}
        calories_per_serving = clean_calories(n.get("calories"))
        fat_g = clean_grams(n.get("fatContent"))
        carbs_g = clean_grams(n.get("carbohydrateContent") or n.get("carbs"))
        protein_g = clean_grams(n.get("proteinContent"))

        result = {
          "title": title,
          "ingredients": ingredients,
          "steps": steps,
          "image_url": image_url or "",
          "prep_time_min": str(prep_time_min) if prep_time_min is not None else "",
          "cook_time_min": str(cook_time_min) if cook_time_min is not None else "",
          "total_time_min": str(total_time_min) if total_time_min is not None else "",
          "servings": servings,
          "calories_per_serving": calories_per_serving,
          "fat_g": fat_g,
          "carbs_g": carbs_g,
          "protein_g": protein_g,
        }
        if title and ingredients:
          return result
  return None

def extract_from_html_fallback(soup: BeautifulSoup):
  """
  Fallback extraction for all fields when JSON-LD is missing/partial.
  Uses meta tags, itemprops, and common Allrecipes DOM patterns.
  """
  # Title
  title = None
  og_title = soup.find("meta", property="og:title")
  if og_title and og_title.get("content"):
    title = og_title["content"].strip()
  if not title and soup.title and soup.title.string:
    title = soup.title.string.strip().replace(" - Allrecipes", "").strip()

  # Ingredients
  ingredients = []
  for tag in soup.select('[itemprop="recipeIngredient"]'):
    txt = _clean_text(tag.get_text(" ", strip=True))
    if txt:
      ingredients.append(txt)
  if not ingredients:
    for li in soup.select("li"):
      cls = " ".join(li.get("class", []))
      if "ingredient" in cls:
        txt = _clean_text(li.get_text(" ", strip=True))
        if txt:
          ingredients.append(txt)
  if not ingredients:
    ingredients = None

  # Steps
  steps = []
  for li in soup.select("li.instructions-section-item"):
    txt = _clean_text(li.get_text(" ", strip=True))
    if txt:
      steps.append(txt)
  if not steps:
    for tag in soup.select('[itemprop="recipeInstructions"]'):
      lis = tag.find_all("li")
      if lis:
        for li in lis:
          txt = _clean_text(li.get_text(" ", strip=True))
          if txt:
            steps.append(txt)
      else:
        blob = _clean_text(tag.get_text("\n", strip=True))
        if blob:
          parts = [p.strip() for p in re.split(r"[\r\n]+", blob) if p.strip()]
          steps.extend(parts)
  if not steps:
    steps = None

  # Image
  image_url = None
  og_img = soup.find("meta", property="og:image")
  if og_img and og_img.get("content"):
    image_url = og_img["content"].strip()
  if not image_url:
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
      image_url = img_tag["src"].strip()

  # Times & Servings via common DOM pattern: .recipe-meta-item
  # Example: header = 'prep time', body = '15 mins'
  prep_time_min = cook_time_min = total_time_min = None
  servings = ""
  for box in soup.select(".recipe-meta-item"):
    header = _clean_text((box.find(class_=re.compile(r"recipe-meta-item-header", re.I)) or {}).get_text(" ", strip=True) if box else "")
    body = _clean_text((box.find(class_=re.compile(r"recipe-meta-item-body", re.I)) or {}).get_text(" ", strip=True) if box else "")
    h = header.lower()
    if "prep" in h and not prep_time_min:
      prep_time_min = duration_text_to_minutes(body)
    elif "cook" in h and not cook_time_min:
      cook_time_min = duration_text_to_minutes(body)
    elif "total" in h and not total_time_min:
      total_time_min = duration_text_to_minutes(body)
    elif "servings" in h and not servings:
      servings = normalize_servings(body)

  # Try meta/itemprop fallbacks for servings/time if still empty
  if not servings:
    y = soup.find(attrs={"itemprop": "recipeYield"})
    if y:
      servings = normalize_servings(y.get_text(" ", strip=True))

  # Nutrition via itemprop or text heuristics
  def find_itemprop(prop):
    t = soup.find(attrs={"itemprop": prop})
    if t:
      return _clean_text(t.get_text(" ", strip=True))
    return ""

  calories_per_serving = clean_calories(find_itemprop("calories"))
  fat_g = clean_grams(find_itemprop("fatContent"))
  carbs_g = clean_grams(find_itemprop("carbohydrateContent"))
  protein_g = clean_grams(find_itemprop("proteinContent"))

  # If itemprops not found, try a loose text search section that contains "Nutrition" / "Calories"
  if not any([calories_per_serving, fat_g, carbs_g, protein_g]):
    text = soup.get_text(" ", strip=True)
    # Very forgiving patterns like "Calories: 433", "Protein: 19 g"
    cal_m = re.search(r"Calories?\s*:\s*(\d+)", text, flags=re.I)
    pro_m = re.search(r"Protein\s*:\s*([-+]?\d*\.?\d+)\s*g", text, flags=re.I)
    fat_m = re.search(r"Fat\s*:\s*([-+]?\d*\.?\d+)\s*g", text, flags=re.I)
    carb_m = re.search(r"(Carbohydrates?|Carbs?)\s*:\s*([-+]?\d*\.?\d+)\s*g", text, flags=re.I)
    if cal_m: calories_per_serving = cal_m.group(1)
    if pro_m: protein_g = pro_m.group(1)
    if fat_m: fat_g = fat_m.group(1)
    if carb_m: carbs_g = carb_m.group(2) if carb_m.lastindex and carb_m.lastindex >= 2 else ""

  return {
    "title": title,
    "ingredients": ingredients or [],
    "steps": steps or [],
    "image_url": image_url or "",
    "prep_time_min": str(prep_time_min) if prep_time_min is not None else "",
    "cook_time_min": str(cook_time_min) if cook_time_min is not None else "",
    "total_time_min": str(total_time_min) if total_time_min is not None else "",
    "servings": servings,
    "calories_per_serving": calories_per_serving,
    "fat_g": fat_g,
    "carbs_g": carbs_g,
    "protein_g": protein_g,
  }

def duration_text_to_minutes(text: str | None) -> int | None:
  """
  Heuristic for human-readable durations like '1 hr 15 mins', '45 mins', '2 h', '1h 5m'
  """
  if not text:
    return None
  t = text.lower()
  # Convert unicode fractions or weird spacing
  t = t.replace("hrs", "h").replace("hr", "h").replace("hours", "h").replace("hour", "h")
  t = t.replace("mins", "m").replace("min", "m").replace("minutes", "m").replace("minute", "m")
  t = t.replace(" ", "")
  h = re.search(r"(\d+)\s*h", t)
  m = re.search(r"(\d+)\s*m", t)
  total = 0
  if h: total += int(h.group(1)) * 60
  if m: total += int(m.group(1))
  if total == 0:
    # maybe it's just a number like "45"
    n = parse_int(t)
    return n
  return total

# ---------------- Main ----------------

def main(argv):
  # Files can be passed via CLI; otherwise use defaults
  paths = argv[1:] if len(argv) > 1 else DEFAULT_SITEMAPS

  # Load + filter recipe URLs from sitemaps
  recipe_urls = load_recipe_urls_from_sitemaps(paths)
  #recipe_urls = recipe_urls[:25]
  if not recipe_urls:
    print("No recipe URLs found in provided sitemaps (with 6-digit ID filter).")
    return

  rows = []
  print(f"Scraping {len(recipe_urls)} recipe pages...")

  for idx, link in enumerate(recipe_urls, start=1):
    resp = fetch(link)
    if not resp:
      print(f"[{idx}] Failed: {link}")
      continue

    rsoup = BeautifulSoup(resp.text, "html.parser")
    data = extract_from_jsonld(rsoup)
    if not data:
      data = extract_from_html_fallback(rsoup)

    title = data.get("title")
    ingredients = data.get("ingredients") or []
    steps = data.get("steps") or []
    image_url = data.get("image_url", "")

    if not title or not ingredients:
      print(f"[{idx}] Skipped (missing title/ingredients): {link}")
      continue

    row = {
      "title": title,
      "url": link,
      "image": image_url or "",
      "ingredients": " | ".join(ingredients),
      "steps": " | ".join(steps),
      # new fields
      "prep_time_min": data.get("prep_time_min", ""),
      "cook_time_min": data.get("cook_time_min", ""),
      "total_time_min": data.get("total_time_min", ""),
      "servings": data.get("servings", ""),
      "calories_per_serving": data.get("calories_per_serving", ""),
      "fat_g": data.get("fat_g", ""),
      "carbs_g": data.get("carbs_g", ""),
      "protein_g": data.get("protein_g", ""),
    }
    rows.append(row)

    if idx % 100 == 0:
      print(f"...processed {idx} recipes")

  if rows:
    fieldnames = [
      "title", "url", "image", "ingredients", "steps",
      "prep_time_min", "cook_time_min", "total_time_min",
      "servings", "calories_per_serving", "fat_g", "carbs_g", "protein_g",
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
      w = csv.DictWriter(f, fieldnames=fieldnames)
      w.writeheader()
      w.writerows(rows)
    print(f"Done. Wrote {len(rows)} recipes to {OUT_CSV}")
  else:
    print("No recipes scraped.")

if __name__ == "__main__":
  sys.exit(main(sys.argv))

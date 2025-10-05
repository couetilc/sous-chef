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
DEFAULT_SITEMAPS = ["sitemaps/sitemap1.txt", "sitemaps/sitemap2.txt", "sitemaps/sitemap3.txt", "sitemaps/sitemap4.txt"]

OUT_CSV = "recipes.csv"
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
  """Return (title, ingredients, steps, image_url) if available"""
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

        ingredients = node.get("recipeIngredient") or []
        if isinstance(ingredients, list):
          ingredients = [_clean_text(i) for i in ingredients if isinstance(i, str) and _clean_text(i)]
        else:
          ingredients = []

        steps = []
        instr = node.get("recipeInstructions")
        if instr:
          steps = _flatten_instructions(instr)

        image_url = _image_from_jsonld(node.get("image"))

        if title and ingredients:
          return title, ingredients, steps or [], image_url
  return None, None, None, None

def extract_from_html_fallback(soup: BeautifulSoup):
  """Fallback extraction for title, ingredients, steps, image_url"""
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
    # try typical <img> on page
    img_tag = soup.find("img")
    if img_tag and img_tag.get("src"):
      image_url = img_tag["src"].strip()

  return title, ingredients, steps, image_url

# ---------------- Main ----------------

def main(argv):
  # Files can be passed via CLI; otherwise use defaults
  paths = argv[1:] if len(argv) > 1 else DEFAULT_SITEMAPS

  # Load + filter recipe URLs from sitemaps
  recipe_urls = load_recipe_urls_from_sitemaps(paths)
  # recipe_urls = recipe_urls[:50]
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
    title, ingredients, steps, image_url = extract_from_jsonld(rsoup)
    if not title or not ingredients:
      t2, ing2, st2, img2 = extract_from_html_fallback(rsoup)
      title = title or t2
      ingredients = ingredients or (ing2 or [])
      steps = steps or (st2 or [])
      image_url = image_url or img2

    if not title or not ingredients:
      print(f"[{idx}] Skipped (missing title/ingredients): {link}")
      continue

    row = {
      "title": title,
      "url": link,
      "image": image_url or "",
      "ingredients": " | ".join(ingredients),
      "steps": " | ".join(steps),
    }
    rows.append(row)

    if idx % 100 == 0:
      print(f"...processed {idx} recipes")

  if rows:
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
      w = csv.DictWriter(f, fieldnames=["title", "url", "image", "ingredients", "steps"])
      w.writeheader()
      w.writerows(rows)
    print(f"Done. Wrote {len(rows)} recipes to {OUT_CSV}")
  else:
    print("No recipes scraped.")

if __name__ == "__main__":
  sys.exit(main(sys.argv))

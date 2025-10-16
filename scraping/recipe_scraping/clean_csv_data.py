#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "ftfy"
# ]
# ///

import ftfy
import unicodedata

input_path = "scraping/recipe_scraping/recipe_csv_files/recipes.csv"
output_path = "scraping/recipe_scraping/recipe_csv_files/recipes_clean.csv"

def cleanup_text(s: str) -> str:
    # first, let ftfy try to fix as much as it can
    s = ftfy.fix_text(s)
    # normalize Unicode
    s = unicodedata.normalize("NFC", s)

    # manual mapping for known bad → good chars
    mappings = {
        "Ã¤": "ä",
        "Ã¶": "ö",
        "Ã¼": "ü",
        "ÃŸ": "ß",
        "Ã„": "Ä",
        "Ã–": "Ö",
        "Ãœ": "Ü",
        "Ã©": "é",
        "Ã¨": "è",
        "Ã¢": "â",
        "Ã´": "ô",
        "Ã¹": "ù",
        "Ã©": "é",
        "Ã ": "à",
        "Ã‡": "Ç",
        "Ã§": "ç",
        "Â®": "®",
        "Â©": "©",
        "â€™": "’",
        "â€“": "–",
        "â€”": "—",
        "â€œ": "“",
        "â€\u009d": "”",   # sometimes weird trailing bytes
        "â€˜": "‘",
        "â€\u0098": "‘",
        "â€¦": "…",
        "â€¢": "•",
        # add more as you find them...
    }

    # apply replacements (in a simple loop)
    for bad, good in mappings.items():
        s = s.replace(bad, good)

    # also cleanup HTML entities
    html_entities = {
        "&#39;": "'",
        "&quot;": '"',
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&reg;": "®",
        "&copy;": "©",
    }
    for bad, good in html_entities.items():
        s = s.replace(bad, good)

    return s

# read, clean, and write
with open(input_path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

cleaned = cleanup_text(text)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(cleaned)

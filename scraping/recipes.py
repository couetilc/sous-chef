#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "beautifulsoup4",
#   "requests",
# ]
# ///
import requests
from bs4 import BeautifulSoup

# URL you want to scrape
url = "https://www.allrecipes.com/recipes/1284/everyday-cooking/more-meal-ideas/30-minute-meals/chicken/"

# Send HTTP request
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    with open("output.txt", "w", encoding="utf-8") as f:
        for link in soup.find_all("a"):
            text = link.get_text(strip=True)
            href = link.get("href")
            if "https://www.allrecipes.com/recipe/" in href:
                f.write(f"{text} -> {href}\n")

else:
    print(f"Failed to retrieve page. Status code: {response.status_code}")

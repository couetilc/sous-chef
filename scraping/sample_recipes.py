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
url = "https://www.epicurious.com/recipes-menus/30-minute-meals-gallery"

# Send HTTP request
response = requests.get(url)

# Check if request was successful
if response.status_code == 200:
    # Parse HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Open a text file to write output
    with open("output.txt", "w", encoding="utf-8") as f:
        # Example: get page title
        title = soup.title.string if soup.title else "No title"
        f.write(f"Page title: {title}\n\n")

        # Example: find all links
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)
            f.write(f"{text} -> {href}\n")
else:
    print(f"Failed to retrieve page. Status code: {response.status_code}")

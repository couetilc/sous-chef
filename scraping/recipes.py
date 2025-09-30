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
url = "https://news.ycombinator.com"

# Send HTTP request
response = requests.get(url)

# Check if request was successful
if response.status_code == 200:
    # Parse HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Example: get page title
    title = soup.title.string if soup.title else "No title"
    print("Page title:", title)

    # Example: find all links
    for link in soup.find_all("a"):
        href = link.get("href")
        text = link.get_text(strip=True)
        print(f"{text} -> {href}")
else:
    print(f"Failed to retrieve page. Status code: {response.status_code}")
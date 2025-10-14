#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# ///

import subprocess

# List of scripts to run
scripts = [
    "scraping/ingredient_scraping/load_data.py",
    "scraping/price_scraping/load_data.py",
    "scraping/production/load_ingredients.py",
    "scraping/recipe_scraping/load_data.py"
]

for script in scripts:
    print(f"Running {script} with uv...")
    result = subprocess.run(["uv", "run", script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)
    print(f"Finished running {script}\n{'-'*50}\n")

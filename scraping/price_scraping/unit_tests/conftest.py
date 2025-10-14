import csv
import os
import re
import pytest
from decimal import Decimal, InvalidOperation

def pytest_addoption(parser):
    parser.addoption(
        "--csv",
        action="store",
        default=os.getenv("PRICES_CSV", "ingredient_prices.csv"),
        help="Path to the generated price CSV (default: ingredient_prices.csv)",
    )

@pytest.fixture(scope="session")
def csv_path(request):
    path = request.config.getoption("--csv")
    if not os.path.exists(path):
        pytest.skip(f"CSV not found at {path}; run gen_prices.py first or pass --csv")
    return path

@pytest.fixture(scope="session")
def rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        data = list(r)
    assert len(data) > 0, "CSV has a header but no data rows."
    return data

PRICE_RE = re.compile(r"^\d+(?:\.\d{2})$")

def as_decimal_or_none(s):
    if s is None or s == "":
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return "INVALID"

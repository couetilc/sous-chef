import re
import pytest
from decimal import Decimal
from conftest import PRICE_RE, as_decimal_or_none

EXPECTED_HEADER = ["food_id","ingredient_name","quantity_other","quantity_oz","price"]

def test_header_columns(csv_path):
    # Validate exact header order
    import csv
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == EXPECTED_HEADER, f"Header mismatch. Got {header}"

def test_required_fields_present(rows):
    for i, row in enumerate(rows, 2):
        assert row.get("ingredient_name", "").strip() != "", f"Empty ingredient_name at line {i}"
        # food_id may be empty; when present must be digits
        fid = (row.get("food_id") or "").strip()
        assert fid == "" or fid.isdigit(), f"Non-numeric food_id at line {i}: {fid}"

def test_quantity_oz_numeric_if_present(rows):
    for i, row in enumerate(rows, 2):
        qoz = (row.get("quantity_oz") or "").strip()
        if qoz != "":
            try:
                val = float(qoz)
            except ValueError:
                pytest.fail(f"quantity_oz not numeric at line {i}: {qoz}")
            assert val > 0.0, f"quantity_oz must be > 0 at line {i}: {qoz}"

def test_price_format_and_bounds(rows):
    # Price can be blank; if present must be 0.00+ with two decimals and sane bounds.
    for i, row in enumerate(rows, 2):
        p = (row.get("price") or "").strip()
        if p == "":
            continue
        assert PRICE_RE.match(p), f"Bad price format (need two decimals) at line {i}: {p}"
        dec = as_decimal_or_none(p)
        assert dec != "INVALID", f"Unparseable price at line {i}: {p}"
        # Reasonable retail sanity bounds (tune as needed)
        assert Decimal("0.10") <= dec <= Decimal("2000.00"), f"Outlier price at line {i}: {p}"

def test_quantity_other_reasonable_length(rows):
    for i, row in enumerate(rows, 2):
        qo = (row.get("quantity_other") or "")
        assert len(qo) <= 64, f"quantity_other too long (>64 chars) at line {i}"

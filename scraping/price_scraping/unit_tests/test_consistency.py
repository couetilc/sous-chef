import re
from collections import defaultdict

CT_WORDS = ("ct", "count", "bottle", "bottles", "pack", "packs", "stick", "sticks")

def test_duplicate_names_have_consistent_results(rows):
    """
    Your generator caches by ingredient_name, so any duplicates should emit
    identical (quantity_other, quantity_oz, price). This test enforces that.
    """
    seen = {}
    for i, row in enumerate(rows, 2):
        name = row["ingredient_name"]
        tup = (row.get("quantity_other") or "",
               row.get("quantity_oz") or "",
               row.get("price") or "")
        if name in seen:
            assert seen[name] == tup, (
                f"Inconsistent duplicate for '{name}' at line {i}: "
                f"{tup} vs {seen[name]}"
            )
        else:
            seen[name] = tup

def test_ct_without_oz_is_ok_but_lb_or_oz_words_expect_oz(rows):
    """
    Heuristic: if quantity_other references count-like packaging, missing oz is fine.
    But if it references weight measures ('lb', 'oz'), we expect quantity_oz to be present.
    """
    for i, row in enumerate(rows, 2):
        qo = (row.get("quantity_other") or "").lower()
        qoz = (row.get("quantity_oz") or "").strip()
        if qo == "":
            continue
        if any(w in qo for w in CT_WORDS):
            # Packages like "6 bottles" can legitimately have blank oz (multi-pack variety)
            continue
        if "lb" in qo or re.search(r"\boz\b", qo):
            assert qoz != "", f"Likely missing quantity_oz where weight is implied at line {i}: {qo}"

def test_price_present_for_majority(rows):
    """
    Loose quality gate: At least 40% of rows should have a price.
    Adjust threshold to your real coverage; it's just to catch regressions.
    """
    priced = sum(1 for r in rows if (r.get("price") or "").strip() != "")
    ratio = priced / len(rows)
    assert ratio >= 0.40, f"Too few priced rows ({ratio:.1%}); scraper may be failing."

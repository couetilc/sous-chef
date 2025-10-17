import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import ScrapedInventory


REQUIRED_COLUMNS = [
    "food_id",
    "ingredient_name",
    "quantity_other",
    "quantity_oz",
    "price",
]


class Command(BaseCommand):
    help = 'Load inventory rows from ingredient_prices_cleaned.csv into the database (ScrapedInventory)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: /scraping/price_scraping/ingredient_prices_cleaned.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='bulk_create batch size (default: 1000)',
        )

    # ---- small parsers (safe no-op on blanks) ----
    def _parse_decimal(self, s: str) -> Optional[Decimal]:
        s = (s or "").strip()
        if not s:
            return None
        try:
            # allow plain numbers like "3.49" (your cleaner outputs this)
            return Decimal(s)
        except (InvalidOperation, ValueError):
            return None

    def _parse_float(self, s: str) -> Optional[float]:
        s = (s or "").strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    def handle(self, *args, **options):
        # Determine CSV path
        csv_path_opt = options.get('csv_path')
        if not csv_path_opt:
            # Default path inside container
            csv_path = Path('/scraping/price_scraping/ingredient_prices_cleaned.csv')
        else:
            csv_path = Path(csv_path_opt)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading Inventory from: {csv_path}')

        # Read and process CSV
        rows = []
        try:
            with csv_path.open('r', encoding='utf-8', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                for col in REQUIRED_COLUMNS:
                    if col not in reader.fieldnames:
                        raise CommandError(f'CSV must have a "{col}" column')

                for row in reader:
                    # Extract raw values
                    food_id_raw = (row.get('food_id') or '').strip()
                    name_raw = (row.get('ingredient_name') or '').strip()
                    qty_other_raw = (row.get('quantity_other') or '').strip()
                    qty_oz_raw = (row.get('quantity_oz') or '').strip()
                    price_raw = (row.get('price') or '').strip()

                    # Light parsing (keeps None if blank)
                    quantity_oz = self._parse_float(qty_oz_raw)
                    price_dec = self._parse_decimal(price_raw)

                    # Build model instance; leave types flexible (None ok)
                    rows.append(
                        ScrapedInventory(
                            food_id=food_id_raw or None,
                            ingredient_name=name_raw,
                            quantity_other=qty_other_raw or None,
                            quantity_oz=quantity_oz,
                            price=price_dec if price_dec is not None else None,
                        )
                    )

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(rows)} rows')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            preview = min(10, len(rows))
            self.stdout.write(f'Sample rows (first {preview}):')
            for inst in rows[:preview]:
                self.stdout.write(
                    f'  - food_id={inst.food_id!r}, '
                    f'ingredient_name={inst.ingredient_name!r}, '
                    f'quantity_other={inst.quantity_other!r}, '
                    f'quantity_oz={inst.quantity_oz!r}, '
                    f'price={str(inst.price) if inst.price is not None else None}'
                )
            return

        # Persist
        batch_size = options['batch_size']
        with transaction.atomic():
            ScrapedInventory.objects.bulk_create(rows, batch_size=batch_size)

        # Report results
        total = ScrapedInventory.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded inventory:\n'
                f'  - Inserted: {len(rows)}\n'
                f'  - Total in database: {total}'
            )
        )

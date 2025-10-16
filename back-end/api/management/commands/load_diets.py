from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Diet 

diet_names = ["Vegetarian", "Vegan", "Gluten-Free", "Kosher", "Halal"]

class Command(BaseCommand):
    help = 'Load predefined diets into Postgres Database'

    def handle(self, *args, **options):

         # Load into database
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for name in diet_names:
                obj, created = Diet.objects.get_or_create(name=name)
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded diets:\n'
                f'  - Created: {created_count}\n'
                f'  - Skipped (already exists): {skipped_count}\n'
                f'  - Total in database: {Diet.objects.count()}'
            )
        )


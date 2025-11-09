from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create users for developers working on this project'

    def handle(self, *args, **options):
        users = [
            # username, password, is_superuser
            ('Dalbert', 'Password', False),
            ('Andrew', 'Password', False),
        ]
        # Step 1: Delete existing demo user if exists
        for username, password, is_superuser in users:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    f'Found existing user "{username}".'
                )
            else:
                # create, optionally set superuser status
                User.objects.create(username=username, password=password, is_superuser=is_superuser)
                self.stdout.write(
                    f'Created user "{username}".'
                )

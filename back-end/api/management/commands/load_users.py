from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create users for developers working on this project'

    def handle(self, *args, **options):
        users = [
            # username, password, is_superuser
            ('demo', 'cs307team21', False),
            ('purdue', 'cs307team21', True),
        ]
        # Step 1: Delete existing demo user if exists
        for username, password, is_superuser in users:
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    f'Found existing user "{username}".'
                )
            else:
                # create, optionally set superuser status
                if is_superuser:
                    User.objects.create_superuser(username = username, password = password)
                else:
                    User.objects.create_user(username=username, password=password)
                self.stdout.write(
                    f'Created user "{username}".'
                )

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from api.models import Recipe, MealPlan, MealPlanEntry


class Command(BaseCommand):
    help = 'Create demo meal plan using existing recipes from database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username to create meal plan for'
        )

    def handle(self, *args, **options):
        username = options['username']

        # Get or create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing user: {username}'))

        # Get available recipes from database
        recipes = list(Recipe.objects.all())
        
        if not recipes:
            self.stdout.write(self.style.ERROR('No recipes found in database. Please add recipes first.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(recipes)} recipes in database'))

        # Calculate Monday of current week
        today = datetime.now().date()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)

        # Get or create meal plan for this week
        meal_plan, created = MealPlan.objects.get_or_create(
            user=user,
            week_start=monday,
            defaults={'created_at': timezone.now()}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created meal plan for week starting {monday}'))
        else:
            self.stdout.write(self.style.WARNING(f'Meal plan already exists for week {monday}'))
            return

        # Add meals to the plan (3 meals per day for 7 days = 21 entries)
        # Days: 0=Monday, 1=Tuesday, ..., 6=Sunday
        entry_count = 0

        for day in range(7):
            for meal_index in range(1, 4):
                # Cycle through available recipes
                recipe = recipes[(day * 3 + meal_index - 1) % len(recipes)]
                
                entry = MealPlanEntry.objects.create(
                    meal_plan=meal_plan,
                    day_of_week=day,
                    meal_index=meal_index,
                    recipe=recipe
                )
                entry_count += 1

        self.stdout.write(self.style.SUCCESS(f'Added {entry_count} meal plan entries'))
        self.stdout.write(self.style.SUCCESS(f'Meal plan is {"complete" if meal_plan.is_complete else "incomplete"}'))
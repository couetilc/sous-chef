from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from api.models import Recipe, MealPlan, MealPlanEntry


class Command(BaseCommand):
    help = 'Create demo meal plan for this week AND next week using existing recipes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='recipe_history',
            help='Username to create meal plan for (default: recipe_history)'
        )

    def handle(self, *args, **options):
        username = options['username']

        # Get or create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Using existing user: {username}'))

        # Load recipes
        recipes = list(Recipe.objects.all())
        if not recipes:
            self.stdout.write(self.style.ERROR("No recipes found. Add some first."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(recipes)} recipes."))

        # Determine current Monday
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())

        # Create meal plan
        def create_plan_for_week(start_date, randomize=False):
            meal_plan, created = MealPlan.objects.get_or_create(
                user=user,
                week_start=start_date,
                defaults={'created_at': timezone.now()}
            )

            if not created:
                self.stdout.write(
                    self.style.WARNING(f"Meal plan already exists for week starting {start_date}")
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f"Created meal plan for week starting {start_date}")
            )

            # Insert entries
            entry_count = 0

            for day in range(7):
                for meal_index in range(1, 4):
                    if randomize:
                        recipe = random.choice(recipes)
                    else:
                        # Cycling as before
                        recipe = recipes[(day * 3 + meal_index - 1) % len(recipes)]

                    MealPlanEntry.objects.create(
                        meal_plan=meal_plan,
                        day_of_week=day,
                        meal_index=meal_index,
                        recipe=recipe,
                        servings=3.0
                    )
                    entry_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Added {entry_count} entries to week {start_date}"
            ))

        # Create current week plan
        create_plan_for_week(monday, randomize=True)

        # Create next week's plan
        next_monday = monday + timedelta(days=7)
        create_plan_for_week(next_monday, randomize=True)

        self.stdout.write(self.style.SUCCESS("Done! Both weeks prepared."))

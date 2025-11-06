from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import Recipe, CookedRecipe, Meal


class Command(BaseCommand):
    help = 'Create demo data for recipe history feature with user "recipe_history"'

    def handle(self, *args, **options):
        username = 'recipe_history'
        password = 'password123'

        # Step 1: Delete existing demo user if exists
        self.stdout.write('Checking for existing demo user...')
        try:
            existing_user = User.objects.get(username=username)
            cooked_count = CookedRecipe.objects.filter(user=existing_user).count()
            meal_count = Meal.objects.filter(cooked_recipe__user=existing_user).count()

            self.stdout.write(
                f'Found existing user "{username}" with {cooked_count} cooked recipes '
                f'and {meal_count} meals. Deleting...'
            )
            existing_user.delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing demo data cleaned up'))
        except User.DoesNotExist:
            self.stdout.write('No existing demo user found')

        # Step 2: Check if recipes are loaded
        recipe_count = Recipe.objects.count()
        if recipe_count < 8:
            self.stdout.write(
                self.style.WARNING(
                    f'\nWarning: Only {recipe_count} recipes in database. '
                    'At least 8 recipes recommended.\n'
                    'Run: python manage.py load_recipes\n'
                )
            )
            if recipe_count == 0:
                self.stdout.write(self.style.ERROR('No recipes available. Cannot create demo data.'))
                return

        # Step 3: Select 8 diverse recipes (or however many are available)
        self.stdout.write('\nSelecting recipes for demo...')
        available_recipes = list(Recipe.objects.all()[:8])

        if len(available_recipes) < 8:
            self.stdout.write(
                self.style.WARNING(
                    f'Only {len(available_recipes)} recipes available. '
                    'Using what we have.'
                )
            )

        # Step 4: Create demo user
        self.stdout.write('\nCreating demo user...')
        demo_user = User.objects.create_user(
            username=username,
            password=password,
            email='recipe_history@example.com',
            first_name='Recipe',
            last_name='History'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created user "{username}"'))

        # Step 5 & 6: Create cooked recipes and meals
        self.stdout.write('\nCreating cooked recipes and meals...')
        now = timezone.now()

        # Define the meal plans for each cooked recipe
        meal_plans = [
            {
                'name': 'Untouched',
                'days_ago': 2,
                'total_servings_cooked': 1,
                'meals': []  # No meals
            },
            {
                'name': 'Fully consumed (many small portions)',
                'days_ago': 12,
                'total_servings_cooked': 20,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.15')},
                    {'days_after_cooked': 1, 'portion': Decimal('0.20')},
                    {'days_after_cooked': 2, 'portion': Decimal('0.15')},
                    {'days_after_cooked': 3, 'portion': Decimal('0.25')},
                    {'days_after_cooked': 4, 'portion': Decimal('0.15')},
                    {'days_after_cooked': 5, 'portion': Decimal('0.10')},
                ]
            },
            {
                'name': 'Almost finished (90%)',
                'days_ago': 8,
                'total_servings_cooked': 3,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.40')},
                    {'days_after_cooked': 2, 'portion': Decimal('0.30')},
                    {'days_after_cooked': 3, 'portion': Decimal('0.20')},
                ]
            },
            {
                'name': 'Half consumed',
                'days_ago': 6,
                'total_servings_cooked': 8,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.25')},
                    {'days_after_cooked': 1, 'portion': Decimal('0.25')},
                ]
            },
            {
                'name': 'Barely started (10%)',
                'days_ago': 3,
                'total_servings_cooked': 10,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.10')},
                ]
            },
            {
                'name': 'Quarter consumed',
                'days_ago': 10,
                'total_servings_cooked': 4,
                'meals': [
                    {'days_after_cooked': 1, 'portion': Decimal('0.25')},
                ]
            },
            {
                'name': 'Mostly consumed (75%)',
                'days_ago': 7,
                'total_servings_cooked': 6,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.33')},
                    {'days_after_cooked': 1, 'portion': Decimal('0.33')},
                    {'days_after_cooked': 3, 'portion': Decimal('0.09')},
                ]
            },
            {
                'name': 'Over half consumed (60%)',
                'days_ago': 0,
                'total_servings_cooked': 10,
                'meals': [
                    {'days_after_cooked': 0, 'portion': Decimal('0.35')},
                    {'days_after_cooked': 0, 'portion': Decimal('0.25')},
                ]
            },
        ]

        created_cooked_recipes = []
        total_meals = 0

        for i, meal_plan in enumerate(meal_plans):
            # Use available recipes, cycling if we have fewer than 8
            recipe = available_recipes[i % len(available_recipes)]

            # Create cooked recipe with timestamp in the past
            cooked_at = now - timedelta(days=meal_plan['days_ago'])
            cooked_recipe = CookedRecipe.objects.create(
                user=demo_user,
                recipe=recipe,
                total_servings_cooked=meal_plan['total_servings_cooked'],
            )
            # Manually set cooked_at since it's auto_now_add
            CookedRecipe.objects.filter(pk=cooked_recipe.pk).update(cooked_at=cooked_at)
            cooked_recipe.refresh_from_db()

            # Create meals for this cooked recipe
            meals_created = 0
            total_portion = Decimal('0')
            for meal_data in meal_plan['meals']:
                eaten_at = cooked_at + timedelta(days=meal_data['days_after_cooked'])
                servings = round(meal_data['portion'] *
                    cooked_recipe.total_servings_cooked, 2)

                meal = Meal.objects.create(
                    cooked_recipe=cooked_recipe,
                    servings=servings
                )
                # Manually set eaten_at since it's auto_now_add
                Meal.objects.filter(pk=meal.pk).update(eaten_at=eaten_at)
                meals_created += 1
                total_portion += servings

            created_cooked_recipes.append({
                'recipe': recipe.title,
                'cooked_at': cooked_at,
                'meals': meals_created,
                'consumed': f"{float(total_portion * 100):.1f}%"
            })
            total_meals += meals_created

        # Step 7: Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write('='*60)

        self.stdout.write(f'\n{self.style.HTTP_INFO("Login Credentials:")}')
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')

        self.stdout.write(f'\n{self.style.HTTP_INFO("Summary:")}')
        self.stdout.write(f'  Cooked recipes: {len(created_cooked_recipes)}')
        self.stdout.write(f'  Total meals: {total_meals}')

        self.stdout.write(f'\n{self.style.HTTP_INFO("Cooked Recipes Created:")}')
        for i, cr in enumerate(created_cooked_recipes, 1):
            days_ago = (now - cr['cooked_at']).days
            self.stdout.write(
                f"  {i}. {cr['recipe'][:50]:<50} | "
                f"{days_ago:2d} days ago | "
                f"{cr['meals']} meals | "
                f"{cr['consumed']:>6} consumed"
            )

        self.stdout.write(f'\n{self.style.HTTP_INFO("Next Steps:")}')
        self.stdout.write('  1. Start the backend server (if not running)')
        self.stdout.write('  2. Login with the credentials above')
        self.stdout.write('  3. Navigate to GET /api/recipe_history/ to view the data')
        self.stdout.write('  4. Try creating new meals with POST /api/recipe_history/<id>/meal/')
        self.stdout.write('\n' + '='*60 + '\n')

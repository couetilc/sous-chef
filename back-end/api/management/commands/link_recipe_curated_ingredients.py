from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Recipe, CuratedIngredient, RecipeCuratedIngredient


class Command(BaseCommand):
    help = 'Link curated ingredients to recipes by searching ingredient text'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--approved-only',
            action='store_true',
            default=True,
            help='Only link approved curated ingredients (default: True)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        approved_only = options['approved_only']

        # Get curated ingredients to link
        if approved_only:
            curated_ingredients = CuratedIngredient.objects.filter(is_approved=True)
            self.stdout.write(f'Linking approved curated ingredients to recipes...')
        else:
            curated_ingredients = CuratedIngredient.objects.all()
            self.stdout.write(f'Linking all curated ingredients to recipes...')

        curated_count = curated_ingredients.count()
        self.stdout.write(f'Found {curated_count} curated ingredients to process')

        # Get all recipes
        recipes = Recipe.objects.all()
        recipe_count = recipes.count()
        self.stdout.write(f'Found {recipe_count} recipes to search\n')

        # Track statistics
        links_created = 0
        links_skipped = 0
        ingredients_with_matches = 0
        ingredient_matches = {}  # Track which ingredients matched which recipes

        # Process each curated ingredient
        for idx, curated_ingredient in enumerate(curated_ingredients, 1):
            ingredient_name = curated_ingredient.name.lower()
            matches_for_ingredient = []

            # Search for this ingredient in all recipes
            for recipe in recipes:
                # Case-insensitive partial substring match
                if ingredient_name in recipe.ingredients.lower():
                    matches_for_ingredient.append(recipe)

            # Report progress every 50 ingredients
            if idx % 50 == 0:
                self.stdout.write(f'  Processed {idx}/{curated_count} ingredients...')

            if matches_for_ingredient:
                ingredients_with_matches += 1
                ingredient_matches[curated_ingredient.name] = len(matches_for_ingredient)

                if not dry_run:
                    # Create links for all matching recipes
                    with transaction.atomic():
                        for recipe in matches_for_ingredient:
                            # Check if link already exists
                            exists = RecipeCuratedIngredient.objects.filter(
                                recipe=recipe,
                                curated_ingredient=curated_ingredient
                            ).exists()

                            if exists:
                                links_skipped += 1
                            else:
                                RecipeCuratedIngredient.objects.create(
                                    recipe=recipe,
                                    curated_ingredient=curated_ingredient
                                )
                                links_created += 1

        # Dry run report
        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            self.stdout.write(f'\nMatching Summary:')
            self.stdout.write(f'  Curated ingredients with matches: {ingredients_with_matches}/{curated_count}')

            # Show top 20 ingredients by match count
            self.stdout.write(f'\nTop ingredients by recipe matches (first 20):')
            sorted_ingredients = sorted(
                ingredient_matches.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for name, count in sorted_ingredients[:20]:
                self.stdout.write(f'  - {name}: {count} recipes')

            if len(sorted_ingredients) > 20:
                self.stdout.write(f'  ... and {len(sorted_ingredients) - 20} more')

            # Calculate total potential links
            total_potential_links = sum(ingredient_matches.values())
            self.stdout.write(f'\nTotal potential links to create: {total_potential_links}')
            return

        # Report results
        total_links = RecipeCuratedIngredient.objects.count()

        result_msg = ['\n=== Linking Complete ===']
        result_msg.append(f'Created: {links_created} new recipe-ingredient links')
        result_msg.append(f'Skipped: {links_skipped} existing links')
        result_msg.append(f'Curated ingredients with matches: {ingredients_with_matches}/{curated_count}')
        result_msg.append(f'Total links in database: {total_links}')

        # Show top matched ingredients
        if ingredient_matches:
            result_msg.append('\nTop 10 ingredients by recipe matches:')
            sorted_ingredients = sorted(
                ingredient_matches.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for name, count in sorted_ingredients[:10]:
                result_msg.append(f'  - {name}: {count} recipes')

        self.stdout.write(self.style.SUCCESS('\n'.join(result_msg)))

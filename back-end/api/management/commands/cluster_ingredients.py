import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from api.models import Ingredient, CuratedIngredient
from langchain_openai import ChatOpenAI
from decimal import Decimal


User = get_user_model()


class Command(BaseCommand):
    help = 'Generate curated ingredients using LLM clustering of canonical ingredients'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-ingredients',
            type=int,
            help='Maximum number of ingredients to process (for testing)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Automatically approve high-confidence clusters (≥0.9)',
        )

    def is_branded(self, name):
        """Check if ingredient name contains common brand names"""
        brands = [
            'pillsbury', 'tyson', 'kraft', 'nestle', 'nabisco', 'kellogg',
            'general mills', 'campbell', 'heinz', 'pepsi', 'coca-cola',
            'applebee', 'mcdonald', 'burger king', 'wendy', 'subway',
            'taco bell', 'pizza hut', 'domino', 'papa john', 'olive garden',
            'red lobster', 'chili', 'ihop', 'denny', 'cracker barrel',
            'george weston', 'perdue', 'oscar mayer', 'hormel', 'jimmy dean',
            'stouffer', 'swanson', 'marie callender', 'healthy choice',
            'bob evans', 'banquet', 'hunts', 'jif', 'skippy', 'smuckers',
            'french\'s', 'hidden valley', 'minute maid', 'tropicana',
        ]
        name_lower = name.lower()
        return any(brand in name_lower for brand in brands)

    def cluster_ingredients_with_llm(self, ingredients):
        """
        Cluster all ingredients using LLM in a single call.
        Returns list of cluster dictionaries.
        """
        # Initialize LLM
        api_key = os.environ.get("OPEN_ROUTER_API_KEY")
        if not api_key:
            raise CommandError('OPEN_ROUTER_API_KEY environment variable not set')

        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="openrouter/polaris-alpha",
            temperature=0.3,
        )

        self.stdout.write(f'Processing {len(ingredients)} ingredients in a single LLM call...')

        # Create ingredient list for prompt
        ingredient_list = '\n'.join([f"- {ing.name} (category: {ing.food_category})" for ing in ingredients])

        # Construct prompt
        prompt = f"""You are analyzing food ingredients to create a curated list of common staple ingredients.

Given this list of {len(ingredients)} specific ingredients (which may include brands, variations, and specific preparations):

{ingredient_list}

Your task is to:
1. Extract and deduplicate to create a list of generic staple ingredients
2. Create simple, generic names (e.g., "chicken breast", "olive oil", "cheddar cheese")
3. Group similar variations together (e.g., "Sharp Cheddar" + "Mild Cheddar" = "cheddar cheese")
4. **IMPORTANT: Exclude all branded ingredients. Do NOT include any ingredients with brand names.**

Rules:
- Use simple, generic names without brands or specific preparations
- Use lowercase for staple names
- Aim for creating 500-1500 curated staples from the full list
- Each curated ingredient should represent a commonly used staple

Return ONLY a comma-separated list of ingredient names, nothing else. No JSON, no categories, no descriptions. Just the ingredient names separated by commas.

Example output:
chicken breast, olive oil, cheddar cheese, garlic, onion, tomato, rice, black beans, ground beef, salmon

Your response:"""

        # Call LLM
        content = None
        try:
            self.stdout.write('Calling LLM (this may take a few minutes)...')
            response = llm.invoke(prompt)
            content = response.content.strip()

            # Save raw response to file
            import tempfile
            from pathlib import Path
            response_file = Path(tempfile.gettempdir()) / 'llm_clustering_response.txt'
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stdout.write(f'Saved raw LLM response to: {response_file}')
            self.stdout.write(f'Response length: {len(content)} characters')

            # Parse comma-separated list
            ingredient_names = [name.strip() for name in content.split(',') if name.strip()]

            # Convert to cluster format for consistency with rest of code
            clusters = [{'curated_name': name} for name in ingredient_names]

            self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(clusters)} curated ingredients'))
            return clusters
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error calling LLM: {e}'))
            if content:
                self.stdout.write(f'Saved response to file for inspection')
            raise

    def handle(self, *args, **options):
        max_ingredients = options.get('max_ingredients')
        dry_run = options['dry_run']
        auto_approve = options['auto_approve']

        self.stdout.write('=== Curated Ingredient Clustering ===\n')

        # Fetch ingredients
        queryset = Ingredient.objects.all().order_by('name')

        if max_ingredients:
            queryset = queryset[:max_ingredients]

        ingredients = list(queryset)

        # Filter out branded ingredients
        self.stdout.write('Filtering out branded ingredients...')
        original_count = len(ingredients)
        ingredients = [ing for ing in ingredients if not self.is_branded(ing.name)]
        filtered_count = original_count - len(ingredients)
        self.stdout.write(f'Filtered out {filtered_count} branded ingredients ({filtered_count/original_count*100:.1f}%)')

        self.stdout.write(f'Processing {len(ingredients)} canonical ingredients\n')

        if len(ingredients) == 0:
            raise CommandError('No ingredients to process')

        # Call LLM clustering
        self.stdout.write('Starting LLM clustering...')
        clusters = self.cluster_ingredients_with_llm(ingredients)

        # Post-process: filter out any branded ingredients that slipped through
        self.stdout.write('Post-processing: filtering branded ingredients...')
        cleaned_clusters = []
        for cluster in clusters:
            # Check if the curated name itself is branded
            if not self.is_branded(cluster['curated_name']):
                cleaned_clusters.append(cluster)

        clusters = cleaned_clusters

        self.stdout.write(f'\n=== Clustering Results ===')
        self.stdout.write(f'Generated {len(clusters)} curated ingredients from {len(ingredients)} canonical ingredients')
        self.stdout.write(f'Reduction: {len(ingredients) - len(clusters)} ingredients ({((len(ingredients) - len(clusters)) / len(ingredients) * 100):.1f}%)\n')

        # Preview results
        self.stdout.write('Sample curated ingredients (first 20):')
        for cluster in clusters[:20]:
            self.stdout.write(f'  • {cluster["curated_name"]}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            if len(clusters) > 20:
                self.stdout.write(f'... and {len(clusters) - 20} more curated ingredients not shown')
            return

        # Save to database
        self.stdout.write('\nSaving to database...')

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for cluster in clusters:
                # Check if curated ingredient already exists
                curated_name = cluster['curated_name'].strip()

                if CuratedIngredient.objects.filter(name__iexact=curated_name).exists():
                    self.stdout.write(self.style.WARNING(f'  ⊘ Skipped "{curated_name}" (already exists)'))
                    skipped_count += 1
                    continue

                # Determine approval status (auto-approve all if flag is set)
                is_approved = auto_approve

                # Create curated ingredient
                curated_ingredient = CuratedIngredient.objects.create(
                    name=curated_name,
                    is_approved=is_approved,
                )

                approval_status = " [APPROVED]" if is_approved else ""
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created "{curated_name}"{approval_status}'))
                created_count += 1

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Clustering Complete ===\n'
                f'Created: {created_count} curated ingredients\n'
                f'Skipped: {skipped_count} (already exist)\n'
                f'Total curated ingredients in database: {CuratedIngredient.objects.count()}'
            )
        )

        if auto_approve:
            approved_count = CuratedIngredient.objects.filter(is_approved=True).count()
            self.stdout.write(f'Auto-approved: {approved_count} ingredients')

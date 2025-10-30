from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

# Create your models here.
class Recipe(models.Model):
    title = models.TextField()
    ingredients = models.TextField()
    instructions = models.TextField()
    # optional image for the recipe; requires Pillow to be installed
    image_url = models.URLField(null=True, blank=True, max_length=400)
    # original source URL for the recipe (where it was found)
    source_url = models.URLField(null=True, blank=True, max_length=400)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ScrapedRecipe(models.Model):
    title = models.TextField()
    url = models.TextField()
    image = models.TextField()
    ingredients = models.TextField()
    steps = models.TextField()

    def __str__(self):
        return self.title

class ScrapedIngredient(models.Model):
    description = models.TextField()
    food_category = models.TextField()

    def __str__(self):
        return self.description

class ScrapedNutritionalInfo(models.Model):
    description = models.TextField(default = "")
    calories = models.TextField()
    protein_g = models.TextField()
    fat_g = models.TextField()
    carbs_g = models.TextField()

    def __str__(self):
        return self.description

class Ingredient(models.Model):
    """Canonical ingredient reference - base ingredient list"""
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class DietaryIngredient(models.Model):
    """User-specific restricted ingredients based on dietary preferences"""
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='dietary_restrictions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restricted_ingredients')

    class Meta:
        ordering = ['ingredient__name']
        unique_together = ['user', 'ingredient']

    def __str__(self):
        return f"{self.user.username} restricts {self.ingredient.name}"

class RecipeIngredient(models.Model):
    """Ingredient as used in a specific recipe with quantity"""
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipe_uses')
    quantity = models.CharField(max_length=50)
    recipe = models.ForeignKey(Recipe, related_name='ingredients_list', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quantity} of {self.ingredient.name} for {self.recipe.title}"


class Diet(models.Model):
    """Canonical diet reference"""
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class UserDiet(models.Model):
    """User-specific diet based on selected preferences"""
    diet = models.ForeignKey(Diet, on_delete=models.CASCADE, related_name='related_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selected_diets')

    class Meta:
        ordering = ['diet__name']
        unique_together = ['user', 'diet']

    def __str__(self):
        return f"{self.user.username} restricts {self.diet.name}"

class UserInventory(models.Model):
    # User-specific inventory of ingredients they have on hand
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='in_inventories')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')

    class Meta:
        ordering = ['ingredient__name']
        unique_together = ['user', 'ingredient']
    def __str__(self):
        return f"{self.user.username} has {self.ingredient.name} in inventory"

class ScrapedInventory(models.Model):
    # Optional external/CSV id if present
    food_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    # Keep length consistent with Ingredient.name
    ingredient_name = models.CharField(max_length=200)

    # Mirror your RecipeIngredient.quantity length
    quantity_other = models.CharField(max_length=50, null=True, blank=True)

    # Numeric ounces if present
    quantity_oz = models.FloatField(null=True, blank=True)

    # Plain price as a decimal (e.g., "3.49")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['ingredient_name']

    def __str__(self):
        p = f"{self.price}" if self.price is not None else "—"
        return f"{self.ingredient_name} (${p})"

class CookedRecipe(models.Model):
    """Record of a recipe that was cooked by a user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cooked_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='cooking_instances')
    cooked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cooked_at']  # Most recent first

    def __str__(self):
        return f"{self.user.username} cooked {self.recipe.title} on {self.cooked_at.strftime('%Y-%m-%d')}"

class Meal(models.Model):
    """Record of a meal eaten from a cooked recipe"""
    cooked_recipe = models.ForeignKey(CookedRecipe, on_delete=models.CASCADE, related_name='meals')
    portion = models.DecimalField(max_digits=5, decimal_places=4)  # e.g., 0.2500 for 25%
    eaten_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-eaten_at']  # Most recent first

    def clean(self):
        """Validate that portion is valid and total portions don't exceed 1.0"""
        # Ensure portion is a Decimal
        if not isinstance(self.portion, Decimal):
            self.portion = Decimal(str(self.portion))

        # Validate portion is greater than 0 and less than or equal to 1
        if self.portion <= 0:
            raise ValidationError({'portion': 'Portion must be greater than 0.'})
        if self.portion > 1:
            raise ValidationError({'portion': 'Portion cannot exceed 1.0.'})

        # Validate total portions for this cooked recipe don't exceed 1.0
        existing_meals = Meal.objects.filter(cooked_recipe=self.cooked_recipe)
        if self.pk:  # If updating existing meal, exclude it from the sum
            existing_meals = existing_meals.exclude(pk=self.pk)

        total_consumed = sum((meal.portion for meal in existing_meals), Decimal('0'))
        if total_consumed + self.portion > Decimal('1.0'):
            remaining = Decimal('1.0') - total_consumed
            raise ValidationError({
                'portion': f'Only {remaining} of this cooked recipe remains. Cannot consume {self.portion}.'
            })

    def save(self, *args, **kwargs):
        """Call full_clean() to ensure validation runs"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portion * 100}% of {self.cooked_recipe.recipe.title} eaten on {self.eaten_at.strftime('%Y-%m-%d')}"

class FavoriteRecipe(models.Model):
    """Record of a recipe that was favorited by a user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='user_favorites')

    class Meta:
        ordering = ['recipe__title']
        unique_together = ['user', 'recipe']

    def __str__(self):
        return f"{self.user_name} favorited {self.recipe_name}"
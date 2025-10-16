from django.db import models
from django.contrib.auth.models import User

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
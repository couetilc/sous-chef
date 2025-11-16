from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal

#title,url,image,ingredients,steps,prep_time_min,cook_time_min,total_time_min,servings,
#calories_per_serving,fat_g,carbs_g,protein_g,price_per_serving_usd,total_price_usd

# Create your models here.
class RecipeManager(models.Manager):
    def order_by_ingredient_accessibility(self):
        """
        Order recipes by how accessible their ingredients are.

        Uses square root normalization: accessibility_score = avg_frequency * sqrt(curated_count)
        This penalizes recipes with very few ingredients while still rewarding common ingredients.

        The sqrt penalty means a 1-ingredient recipe needs ingredients 9x more common than a
        9-ingredient recipe to rank equally (since sqrt(9) = 3, and 3^2 = 9).

        Higher scores = more commonly available ingredients with reasonable complexity.
        Recipes without curated ingredients get a score of 0 and sort to the bottom.

        Returns:
            QuerySet of Recipe objects ordered by ingredient accessibility (highest first)
        """
        from django.db.models import Count, Avg, FloatField, F, ExpressionWrapper, Case, When, Value
        from django.db.models.functions import Sqrt, Coalesce

        return self.annotate(
            curated_count=Count('curated_ingredients'),
            frequency_avg=Avg('curated_ingredients__curated_ingredient__frequency', output_field=FloatField()),
            accessibility_score=Case(
                # If recipe has no curated ingredients, score is 0
                When(curated_count=0, then=Value(0.0)),
                # Otherwise, calculate: avg_frequency * sqrt(count)
                default=ExpressionWrapper(
                    Coalesce(F('frequency_avg'), Value(0.0)) * Sqrt(F('curated_count')),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).order_by('-accessibility_score', 'title')

class Recipe(models.Model):
    objects = RecipeManager()
    title = models.TextField()
    ingredients = models.TextField()
    instructions = models.TextField()
    deliciousness_score = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
        help_text="LLM-assessed deliciousness score from 0-100"
    )
    deliciousness_notes = models.TextField(
        blank=True,
        default="",
        help_text="LLM justification for deliciousness score (5-25 words)"
    )
    image_url = models.URLField(null=True, blank=True, max_length=400)
    source_url = models.URLField(null=True, blank=True, max_length=400)
    prep_time_min = models.IntegerField(default=0)
    cook_time_min = models.IntegerField(default=0)
    total_time_min = models.IntegerField(default=0)
    servings = models.IntegerField(default=0)
    calories_per_serving = models.IntegerField(default=0)
    fat_g = models.IntegerField(default=0)
    carbs_g = models.IntegerField(default=0)
    protein_g = models.IntegerField(default=0)
    price_per_serving_usd = models.DecimalField(decimal_places=2, max_digits=10, default=0.00)
    total_price_usd = models.DecimalField(decimal_places=2, max_digits=10, default=0.00)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class UserRecipe(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_recipes')
  original_recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='user_recipes')
  ingredients = models.TextField()
  instructions = models.TextField()

  def title(self):
      return self.original_recipe.title
  def image_url(self):
      return self.original_recipe.image_url
  def source_url(self):
      return self.original_recipe.source_url
  def prep_time_min(self):
      return self.original_recipe.prep_time_min
  def cook_time_min(self):
      return self.original_recipe.cook_time_min
  def total_time_min(self):
      return self.original_recipe.total_time_min
  def servings(self):
      return self.original_recipe.servings
  def calories_per_serving(self):
      return self.original_recipe.calories_per_serving
  def fat_g(self):
      return self.original_recipe.fat_g
  def carbs_g(self):
      return self.original_recipe.carbs_g
  def protein_g(self):
      return self.original_recipe.protein_g
  def price_per_serving_usd(self):
      return self.original_recipe.price_per_serving
  def total_price_usd(self):
      return self.original_recipe.total_price_usd
  def is_private(self):
      return self.original_recipe.is_private
  def created_at(self):
      return self.original_recipe.created_at
  def updated_at(self):
      return self.original_recipe.created_at

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
    food_category = models.TextField(default="")
    quantity_other = models.TextField(default="")
    calories = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    protein_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fat_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_g = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CuratedIngredient(models.Model):
    """
    Simplified, generic ingredient representing a staple.
    Independent from Ingredient model - no foreign key relationship.
    Examples: 'chicken breast', 'olive oil', 'garlic', 'cheddar cheese'
    """
    name = models.CharField(max_length=200, unique=True, db_index=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    frequency = models.IntegerField(default=0, db_index=True, help_text="Number of recipes using this ingredient")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Percentage of recipes using this ingredient")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-frequency', 'name']  # Sort by frequency descending, then name

    def __str__(self):
        return self.name


class RecipeCuratedIngredient(models.Model):
    """
    Links recipes to curated ingredients - parallel to RecipeIngredient.
    Enables simplified recipe search and matching based on staple ingredients.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='curated_ingredients'
    )
    curated_ingredient = models.ForeignKey(
        CuratedIngredient,
        on_delete=models.CASCADE,
        related_name='recipe_uses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['recipe', 'curated_ingredient__name']
        unique_together = ['recipe', 'curated_ingredient']

    def __str__(self):
        return f"{self.curated_ingredient.name} in {self.recipe.title}"


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

class UserCuratedInventory(models.Model):
    """User-specific inventory of curated ingredients they have on hand"""
    curated_ingredient = models.ForeignKey(CuratedIngredient, on_delete=models.CASCADE, related_name='in_curated_inventories')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='curated_inventory_items')

    class Meta:
        ordering = ['curated_ingredient__name']
        unique_together = ['user', 'curated_ingredient']

    def __str__(self):
        return f"{self.user.username} has {self.curated_ingredient.name} in curated inventory"

class CookingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cooking_sessions')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='cooking_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.recipe.title} ({'active' if self.is_active else 'completed'})"

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cooked_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='cooking_instances')
    cooked_at = models.DateTimeField(auto_now_add=True)

    total_servings_cooked = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1.0'))

    class Meta:
        ordering = ['-cooked_at']

    def __str__(self):
        return f"{self.user.username} cooked {self.recipe.title} on {self.cooked_at.strftime('%Y-%m-%d')}"


class Meal(models.Model):
    """Record of a meal eaten from a cooked recipe"""
    cooked_recipe = models.ForeignKey(CookedRecipe, on_delete=models.CASCADE, related_name='meals')
    servings = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1.0'))
    eaten_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-eaten_at']

    def clean(self):
        """Validate that servings > 0 and total does not exceed total_servings_cooked."""
        if not isinstance(self.servings, Decimal):
            self.servings = Decimal(str(self.servings))

        if self.servings <= 0:
            raise ValidationError({'servings': 'Servings must be greater than 0.'})

        # total_servings_cooked on the parent cooked_recipe
        total_allowed = getattr(self.cooked_recipe, 'total_servings_cooked', 1)
        existing_meals = Meal.objects.filter(cooked_recipe=self.cooked_recipe)
        if self.pk:
            existing_meals = existing_meals.exclude(pk=self.pk)

        total_consumed = sum((meal.servings for meal in existing_meals), Decimal('0'))
        if total_consumed + self.servings > total_allowed:
            remaining = total_allowed - total_consumed
            raise ValidationError({
                'servings': f'Only {remaining} servings remain. Cannot consume {self.servings}.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.servings} servings of {self.cooked_recipe.recipe.title} eaten on {self.eaten_at.strftime('%Y-%m-%d')}"


class FavoriteRecipe(models.Model):
    """Record of a recipe that was favorited by a user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='user_favorites')

    class Meta:
        ordering = ['recipe__title']
        unique_together = ['user', 'recipe']

    def __str__(self):
        return f"(user:{self.user.id},recipe:{self.recipe.id})"


class OnboardingSubmission(models.Model):
    """Record of whether a user has completed onboarding"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onboarded')
    has_onboarded = models.BooleanField(default=False)
    skipped = models.BooleanField(default=False)

    def __str__(self):
        return f"user {user} has_onboarded is {self.has_onboarded}"


class HealthDetails(models.Model):
    """Record of user's health details"""
    ACTIVITY_CHOICES = [
        ('low', 'Low'),
        ('light', 'Light'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ]
    GOAL_CHOICES =  [
      ('lose', 'Lose Weight'),
      ('maintain', 'Maintain Weight'),
      ('gain', 'Gain Weight'),
    ]
    SEX_CHOICES = [
      ('male', 'Male'),
      ('female',  'Female'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health')
    age = models.IntegerField(default=0)
    height_ft = models.IntegerField(default=0)
    height_in = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)
    activity_level = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default='low')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='maintain')
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, default='male')

    def __str__(self):
        return f"age: {age}, height: {height_ft} feet {height_in} inches, weight: {weight}, {activity_level} activity, goal: {goal}"


class RecipeTag(models.Model):
    """Connects a User to their created tags"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_tag')
    name = models.CharField(max_length=200)

class TaggedRecipe(models.Model):
    tag = models.ForeignKey(RecipeTag, on_delete=models.CASCADE, related_name='recipes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='tagged')

    def __str__(self):
        return f"user {self.user} placed tag {self.tag} on recipe {self.recipe}"


class ChatConversation(models.Model):
    """AI chat conversation for a user (nutritionist, souschef, etc.)"""
    CHANNEL_CHOICES = [
        ('nutritionist', 'Nutritionist'),
        ('souschef', 'SousChef'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    channel = models.CharField(
        max_length=32,
        choices=CHANNEL_CHOICES,
        default='nutritionist',
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.user.username}'s {self.channel} chat ({status}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"



class ChatMessage(models.Model):
    """Individual message in a chat conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_calls = models.JSONField(null=True, blank=True, help_text="Tool calls made by the assistant (name, parameters, results, timestamp)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

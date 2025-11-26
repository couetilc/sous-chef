from django.contrib.auth.models import User, Group
from django.contrib import admin
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Ingredient, Diet, CookedRecipe, Meal, Recipe, FavoriteRecipe, OnboardingSubmission, UserInventory, UserCuratedInventory, RecipeTag, UserRecipe, ChatConversation, ChatMessage, CuratedIngredient, RecipeCuratedIngredient, MealPlan, MealPlanEntry, InProgressRecipe, InProgressRecipeIngredient

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', "first_name", "last_name")

class OnboardSerializer(serializers.ModelSerializer):
    class Meta:
      model = OnboardingSubmission
      fields = ('has_onboarded')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name", )

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'food_category', 'quantity_other', 'calories', 'protein_g', 'fat_g', 'carbs_g', 'price', 'price_g')
        read_only_fields = ('id',)


class CuratedIngredientSerializer(serializers.ModelSerializer):
    """Serializer for curated (staple) ingredients"""
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = CuratedIngredient
        fields = ('id', 'name', 'is_approved', 'frequency', 'percentage', 'created_at', 'display_name')
        read_only_fields = ('id', 'created_at')

    def get_display_name(self, obj):
        if obj.name:
            return ' '.join(word.capitalize() for word in obj.name.split(' '))
        return None


class RecipeCuratedIngredientSerializer(serializers.ModelSerializer):
    """Serializer for recipe-curated ingredient relationships"""
    curated_ingredient_name = serializers.CharField(source='curated_ingredient.name', read_only=True)

    class Meta:
        model = RecipeCuratedIngredient
        fields = ('id', 'curated_ingredient', 'curated_ingredient_name', 'created_at')
        read_only_fields = ('id', 'created_at')


class DietSerializer(serializers.ModelSerializer):
    is_restricted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Diet
        fields = ('id', 'name', 'is_restricted')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate password match and strength"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Use Django's built-in password validators
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=True,
        )
        return user

class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField('check_favorited')
    accessibility_score = serializers.SerializerMethodField('get_accessibility_score')

    @property
    def user(self):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            user = request.user
        else:
            user = None
        return user

    def check_favorited(self, instance):
        if not self.user: return False

        userQuery = instance.user_favorites.all()
        userQuery = userQuery.filter(user=self.user)
        return userQuery.first() != None

    def get_accessibility_score(self, instance):
        # Return the annotated accessibility_score if it exists
        return getattr(instance, 'accessibility_score', None)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'ingredients', 'instructions',
            'deliciousness_score',
            'deliciousness_notes',
            'turkey_score',
            'turkey_notes',
            'accessibility_score',
            'image_url', 'source_url',
            'servings',
            'is_favorited',
            'calories_per_serving',
            'fat_g',
            'carbs_g',
            'protein_g',
            'prep_time_min',
            'cook_time_min',
            'total_time_min',
            'price_per_serving_usd',
            'total_price_usd',
        )
        read_only_fields = ('id',)


class UserRecipeSerializer(serializers.ModelSerializer):
    original_recipe=RecipeSerializer()

    class Meta:
        model=UserRecipe
        fields=('id', 'original_recipe', 'ingredients', 'instructions')


class MealSerializer(serializers.ModelSerializer):
    servings = serializers.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        model = Meal
        fields = ('id', 'cooked_recipe', 'servings', 'eaten_at')
        read_only_fields = ('id', 'cooked_recipe', 'eaten_at')


class CookedRecipeSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    meals = MealSerializer(many=True, read_only=True)
    total_servings_cooked = serializers.DecimalField(max_digits=6, decimal_places=2)  # <-- add this

    class Meta:
        model = CookedRecipe
        fields = (
            'id',
            'recipe',
            'cooked_at',
            'meals',
            'total_servings_cooked',
        )
        read_only_fields = ('id', 'cooked_at')

class SettingsIngredientSerializer(serializers.ModelSerializer):
    is_restricted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'is_restricted')

class UserInventorySerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()

    class Meta:
        model = UserInventory
        fields = ('id', 'ingredient')

class UserCuratedInventorySerializer(serializers.ModelSerializer):
    curated_ingredient = CuratedIngredientSerializer()

    class Meta:
        model = UserCuratedInventory
        fields = ('id', 'curated_ingredient')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeTag
        fields = ('id', 'name')


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'role', 'content', 'created_at', 'tool_calls')
        read_only_fields = ('id', 'created_at')


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = ('id', 'messages')
        read_only_fields = ('id',)


class MealPlanEntrySerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = MealPlanEntry
        fields = ('id', 'day_of_week', 'day_name', 'meal_index', 'recipe', 'servings')

    def get_day_name(self, obj):
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return days[obj.day_of_week]


class MealPlanSerializer(serializers.ModelSerializer):
    entries = MealPlanEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = MealPlan
        fields = ['id', 'week_start', 'entries', 'is_complete', 'created_at']


class InProgressRecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='curated_ingredient.name', read_only=True)

    class Meta:
        model = InProgressRecipeIngredient
        fields = ('id', 'name', 'quantity', 'unit')
        read_only_fields = ('id',)


class InProgressRecipeSerializer(serializers.ModelSerializer):
    ingredients = InProgressRecipeIngredientSerializer(many=True, read_only=True)
    instructions_list = serializers.SerializerMethodField()

    class Meta:
        model = InProgressRecipe
        fields = (
            'id', 'title', 'instructions', 'instructions_list',
            'prep_time_min', 'cook_time_min', 'total_time_min',
            'servings', 'status', 'ingredients', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_instructions_list(self, obj):
        """Return instructions as a list of steps."""
        if not obj.instructions:
            return []
        return [step.strip() for step in obj.instructions.split('|') if step.strip()]
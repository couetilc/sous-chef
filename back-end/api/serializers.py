from django.contrib.auth.models import User, Group
from django.contrib import admin
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Ingredient, Diet, CookedRecipe, Meal, Recipe, FavoriteRecipe, OnboardingSubmission, UserRecipe

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
        fields = ('id', 'name')
        read_only_fields = ('id',)

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

    @property
    def user(self):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            user = request.user
        else:
            user = None

    def check_favorited(self, instance):
        if not self.user: return False

        userQuery = instance.user_favorites.all()
        userQuery = userQuery.filter(user__id=user.id)
        return userQuery.first() != None

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'ingredients', 'instructions',
            'image_url', 'source_url',
            'servings',
            'is_favorited',
            'calories_per_serving',
            'fat_g',
            'carbs_g',
            'protein_g',
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

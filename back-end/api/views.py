import os
from django.shortcuts import render, redirect
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Exists, OuterRef, Case, When, Value, IntegerField, Q, BooleanField
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User, Group
from .serializers import UserSerializer, GroupSerializer, UserRegistrationSerializer, IngredientSerializer, DietSerializer, CookedRecipeSerializer, MealSerializer, OnboardSerializer, SettingsIngredientSerializer, UserInventorySerializer, TagSerializer, UserRecipeSerializer
from decimal import Decimal, InvalidOperation
from .models import (
    Ingredient, DietaryIngredient, Diet, UserDiet,
    Recipe, CookedRecipe, Meal, FavoriteRecipe, UserInventory, OnboardingSubmission, RecipeIngredient, HealthDetails, RecipeTag, TaggedRecipe,
    ChatConversation, ChatMessage
)
from .serializers import (
    UserSerializer, GroupSerializer, UserRegistrationSerializer,
    IngredientSerializer, DietSerializer,
    CookedRecipeSerializer, MealSerializer, RecipeSerializer,
    ChatConversationSerializer, ChatMessageSerializer
)
from .utils.recommended import compute_recommendations
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

class Paginator(PageNumberPagination):
    page_size = 100

class UserRegistrationView(generics.CreateAPIView):
    """Public endpoint for user registration"""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        OnboardingSubmission.objects.create(user=user, has_onboarded=False, skipped=False)
        return Response({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Public endpoint for user login"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        # Check if sent username is actually the email
        if user is None:
            users = User.objects.filter(email=username)
            if users.exists():
                username = User.objects.get(email=username).username
                user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if not user.onboarded.exists():
                OnboardingSubmission.objects.create(user=user)
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """Endpoint for user logout"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """Get current authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_200_OK)

class OnboardedView(APIView):
    """Get user's onboarding completion status"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        print("onboard: ", user.onboarded.first().has_onboarded)
        print("skip: ", user.onboarded.first().skipped)
        return Response({
            'onboarded': user.onboarded.first().has_onboarded,
            'skipped': user.onboarded.first().skipped
        }, status=status.HTTP_200_OK)

class UpdateOnboardedView(APIView):
    """Update user's onboarding completion status"""
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        user = request.user
        user.onboarded.first().has_onboarded=request.data['new_onboarded']
        user.onboarded.first().skipped=request.data['new_skipped']
        print("new onboard: ", user.onboarded.first().has_onboarded)
        print("new skip: ", user.onboarded.first().skipped)
        return Response({ 'message': 'Successfully completed onboarding'}, status=status.HTTP_200_OK)

class HealthView(APIView):
    """"Get user's health information"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        health = HealthDetails.objects.filter(user=request.user).order_by('-id').first()
        if not health:
             return Response({
                'age': 0,
                'height_ft': 0,
                'height_in': 0,
                'weight': 0,
                'activity_level': 'low',
                'goal': 'maintain',
                'sex': 'lose'
            }, status=status.HTTP_200_OK)
        return Response({
            'age': health.age,
            'height_ft': health.height_ft,
            'height_in': health.height_in,
            'weight': health.weight,
            'activity_level': health.activity_level,
            'goal': health.goal,
            'sex': health.sex
        }, status=status.HTTP_200_OK)

class UpdateHealthView(APIView):
    """Update user's health information"""
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        user = request.user
        print(user)
        if user.health.first() is None:
            HealthDetails.objects.create(
              user = user,
              age=0,
              height_ft = 0,
              height_in = 0,
              weight = 0,
              activity_level = 'low',
              goal = 'maintain',
              sex = 'male'
            )
        user.refresh_from_db()
        health = user.health.first()

        print(request.data)

        health.age = request.data['age']
        health.height_ft = request.data['height_ft']
        health.height_in = request.data['height_in']
        health.weight = request.data['weight']
        health.activity_level = request.data['activity_level']
        health.goal = request.data['goal']
        health.sex = request.data['sex']

        return Response({}, status=status.HTTP_200_OK)

class HealthRecommendationsView(APIView):
    """Compute calorie/protein recommendations from the user's HealthDetails"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        health = HealthDetails.objects.filter(user=request.user).order_by('-id').first()
        if not health:
            return Response({'error': 'No health profile found'}, status=status.HTTP_404_NOT_FOUND)
        data = compute_recommendations(health)
        return Response(data, status=status.HTTP_200_OK)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFTokenView(APIView):
    """Public endpoint to get CSRF token"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)}, status=status.HTTP_200_OK)

class UserList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UpdateUserEmail(APIView):
    """Get current authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get('email')
        user = request.user

        user.email = email
        user.save()

        return Response({'message': 'Successfully updated email'}, status=status.HTTP_200_OK)

class UpdateUserPassword(APIView):
    """Get current authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        user = request.user

        user.set_password(password)
        user.save()

        return Response({'message': 'Successfully updated password'}, status=status.HTTP_200_OK)

class DeleteUser(APIView):
    """Delete current authenticated ueser"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if user is not None:
            user = request.user
            user.delete()
            return Response({'message': 'Successfully deleted'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class GroupList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class IngredientList(generics.ListAPIView):
    """List all available ingredients in the database"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = Paginator
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', '^name']
    ordering = ['name']

class DietaryIngredientList(generics.ListAPIView):
    """List restricted ingredients for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IngredientSerializer

    def get_queryset(self):
        """Filter dietary ingredients to only those restricted by the current user"""
        dietary_ingredient_ids = DietaryIngredient.objects.filter(
            user=self.request.user
        ).values_list('ingredient_id', flat=True)

        return Ingredient.objects.filter(id__in=dietary_ingredient_ids)

class UpdateDietaryIngredientList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        added = request.data.get('added')
        removed = request.data.get('removed')

        addedIngredients = Ingredient.objects.filter(id__in=added)
        for ingredient in addedIngredients:
            DietaryIngredient.objects.get_or_create(ingredient=ingredient, user=self.request.user)

        removedIngredients = Ingredient.objects.filter(id__in=removed)
        for ingredient in removedIngredients:
            target = DietaryIngredient.objects.filter(ingredient=ingredient, user=self.request.user)
            target.delete()

        return Response({'message': 'Successfully updated ingredients'}, status=status.HTTP_200_OK)

class DietList(generics.ListAPIView):
    """List all available diets in the database"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DietSerializer

    def get_queryset(self):
        return Diet.objects.annotate(
            is_restricted=Exists(
                UserDiet.objects.filter(
                    diet=OuterRef('pk'),
                    user=self.request.user
                )
            )
        )

class DietListSync(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        diet_ids = request.data.get('diet_ids', [])

        if not isinstance(diet_ids, list):
            return Response(
                {'error': 'diet_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(diet_ids) > 0 and not Diet.objects.filter(id__in=diet_ids).exists():
            return Response(
                {'error': 'One or more diet IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            current_diet_ids = set(
                UserDiet.objects
                    .filter(user=request.user)
                    .values_list('diet_id', flat=True)
            )
            request_diet_ids = set(diet_ids)

            to_create = request_diet_ids - current_diet_ids
            to_delete = current_diet_ids - request_diet_ids

            UserDiet.objects.filter(user=request.user, diet_id__in=to_delete).delete()
            UserDiet.objects.bulk_create(
                UserDiet(user=request.user, diet_id=diet_id)
                for diet_id in to_create
            )

        return Response(
            {'message': 'Successfully updated diets'},
            status=status.HTTP_200_OK
        )



class SelectedDietList(generics.ListAPIView):
    """List selected diets for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DietSerializer

    def get_queryset(self):
        selected_diet_ids = UserDiet.objects.filter(
            user=self.request.user
        ).values_list('diet_id', flat=True)

        return Ingredient.objects.filter(id__in=selected_diet_ids)

class UpdateDiets(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        added = request.data.get('added')
        removed = request.data.get('removed')

        addedDiets= Diet.objects.filter(id__in=added)
        for diet in addedDiets:
            UserDiet.objects.get_or_create(diet=diet, user=self.request.user)

        removedDiets = Diet.objects.filter(id__in=removed)
        for diet in removedDiets:
            target = UserDiet.objects.filter(diet=diet, user=self.request.user)
            target.delete()

        return Response({'message': 'Successfully updated diets'}, status=status.HTTP_200_OK)

class RecipeHistoryView(generics.ListAPIView):
    """List all cooked recipes for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CookedRecipeSerializer

    def get_queryset(self):
        return CookedRecipe.objects.filter(user=self.request.user)

class RecipeNutritionPreviewView(APIView):
    """
    GET /api/recipes/<id>/nutrition/?servings=1.25
    Returns scaled nutrition for the given number of servings.
    Uses per-serving fields on Recipe (calories_per_serving, protein_g, fat_g, carbs_g).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        servings_param = request.query_params.get('servings', '1')
        try:
            servings = Decimal(servings_param)
            if servings <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return Response({'error': 'servings must be a positive number'}, status=status.HTTP_400_BAD_REQUEST)

        # Scale numeric nutrition fields by servings
        def scale(val):
            try:
                return float(Decimal(val) * servings)
            except (InvalidOperation, ValueError, TypeError):
                return 0.0

        nutrition = {
            'calories': scale(recipe.calories_per_serving),
            'protein_g': scale(recipe.protein_g),
            'fat_g': scale(recipe.fat_g),
            'carbs_g': scale(recipe.carbs_g),
        }

        return Response({'nutrition': nutrition}, status=status.HTTP_200_OK)

class CreateMealView(APIView):
    """Create a meal from a cooked recipe."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, cooked_recipe_id):
        try:
            cooked_recipe = CookedRecipe.objects.get(id=cooked_recipe_id)
        except CookedRecipe.DoesNotExist:
            return Response({'error': 'Cooked recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        if cooked_recipe.user != request.user:
            return Response({'error': 'You do not have permission to create a meal from this cooked recipe'},
                            status=status.HTTP_403_FORBIDDEN)

        # Validate servings
        servings = request.data.get('servings')
        if servings is None:
            return Response({'error': 'Servings is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: eaten_at (ISO 8601). If provided, we will overwrite the default timestamp after creation.
        eaten_at_raw = request.data.get('eaten_at')
        parsed_eaten_at = None
        if eaten_at_raw:
            parsed_eaten_at = parse_datetime(eaten_at_raw)
            if parsed_eaten_at is None:
                return Response({'error': 'Invalid eaten_at; expected ISO 8601 datetime'}, status=status.HTTP_400_BAD_REQUEST)

        # Create and validate the Meal
        meal = Meal(cooked_recipe=cooked_recipe, servings=servings)
        try:
            meal.save()  # runs model validation (clean)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If client provided a specific eaten_at, set it after initial save (auto_now_add doesn’t block manual updates)
        if parsed_eaten_at:
            meal.eaten_at = parsed_eaten_at
            meal.save(update_fields=['eaten_at'])

        serializer = MealSerializer(meal)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetRecipesFiltered(APIView):
    """List recipes matching the posted filter"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        queryset = Recipe.objects.order_by('-created_at')

        title = request.data.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        ingredients = request.data.get('ingredients')
        if ingredients:
            for ingredient_id in ingredients:
                queryset = queryset.filter(
                    ingredients_list__ingredient_id=ingredient_id
                )

        searchInventory = request.data.get('searchInventory')
        if searchInventory:
            ingredient_ids = request.user.inventory_items.values_list('ingredient_id')
            queryset = queryset.filter(
                ingredients_list__ingredient_id__in=ingredient_ids
            )

        searchFavorite = request.data.get('searchFavorite')
        if searchFavorite:
            queryset = queryset.filter(user_favorites__isnull=False)

        paginator = Paginator()
        page = paginator.paginate_queryset(queryset, request)

        serializer = RecipeSerializer(page, many=True, context = {'request': request})
        return paginator.get_paginated_response(serializer.data)

class CreateFavoriteRecipe(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        recipeID = request.data.get('recipeID')
        recipe = Recipe.objects.get(id=recipeID)

        oldFavorite = FavoriteRecipe.objects.filter(recipe=recipe).first()
        if (oldFavorite != None) :
            oldFavorite.delete()
            return Response({'message': 'Successfully unfavorited recipe'}, status=status.HTTP_200_OK)
        else:
            user = request.user
            newFavorite = FavoriteRecipe(user=user, recipe=recipe)
            newFavorite.save()
            return Response({'message': 'Successfully favorited recipe'}, status=status.HTTP_200_OK)



class UserInventoryList(APIView):
    """List user inventory for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        inventories = UserInventory.objects.filter(user=request.user).order_by('ingredient__name')
        serialized = UserInventorySerializer(inventories, many = True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        ingredient_ids = request.data.get('ingredient_ids')

        if not isinstance(ingredient_ids, list):
            return Response(
                {'error': 'ingredient_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(ingredient_ids) > 0 and not Ingredient.objects.filter(id__in=ingredient_ids).exists():
            return Response(
                {'error': 'One or more ingredient IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for ingredient_id in ingredient_ids:
                UserInventory.objects.get_or_create(
                    user=request.user,
                    ingredient_id=ingredient_id
                )

        return Response(
            {'message': 'successfully created inventory items'},
            status=status.HTTP_201_CREATED,
        )

class UserInventoryDetail(APIView):
    """Retrieve, update or delete a user inventory item"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            inventory = UserInventory.objects.get(id=id, user=request.user)
        except UserInventory.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'id': inventory.id,
            'ingredient': IngredientSerializer(inventory.ingredient).data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            inventory = UserInventory.objects.get(id=id, user=request.user)
        except UserInventory.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        inventory.delete()
        return Response(
            {'message': 'Successfully deleted inventory item'},
            status=status.HTTP_200_OK,
        )

class NutritionLastDayView(APIView):
    """Get calories, fats, carbs, and proteins consumed in the last day"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.localtime(timezone.now())
        today = now.date()

        # Start is today at midnight
        start_time = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        end_time = now

        meals = Meal.objects.filter(
            cooked_recipe__user=request.user,
            eaten_at__range=(start_time, end_time)
        ).select_related("cooked_recipe__recipe")

        total_calories = 0.0
        total_fats = 0.0
        total_carbs = 0.0
        total_proteins = 0.0

        for meal in meals:
            recipe = meal.cooked_recipe.recipe
            if recipe.calories_per_serving is not None:
                total_calories += float(recipe.calories_per_serving) * float(meal.servings)
            if recipe.fat_g is not None:
                total_fats += float(recipe.fat_g) * float(meal.servings)
            if recipe.carbs_g is not None:
                total_carbs += float(recipe.carbs_g) * float(meal.servings)
            if recipe.protein_g is not None:
                total_proteins += float(recipe.protein_g) * float(meal.servings)

        return Response({
            'calories': total_calories,
            'fats': total_fats,
            'carbs': total_carbs,
            'proteins': total_proteins
        }, status=status.HTTP_200_OK)

class CaloriesLastWeekView(APIView):
    """Get total calories consumed for each of the past 7 days"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.localtime(timezone.now())
        today = now.date()

        # Start is 6 days before today at midnight
        start_time = timezone.make_aware(
            timezone.datetime.combine(today - timezone.timedelta(days=6), timezone.datetime.min.time())
        )
        end_time = now

        # Fetch meals from the last 7 days including today
        meals = Meal.objects.filter(
            cooked_recipe__user=request.user,
            eaten_at__range=(start_time, end_time)
        ).select_related("cooked_recipe__recipe")

        daily_calories = {}
        for i in range(7):
            day = (today - timezone.timedelta(days=6 - i)).isoformat()
            daily_calories[day] = 0.0

        # Calculate calories per day
        for meal in meals:
            meal_day = timezone.localtime(meal.eaten_at).date().isoformat()
            recipe = meal.cooked_recipe.recipe
            if recipe.calories_per_serving is not None and meal_day in daily_calories:
                daily_calories[meal_day] += float(recipe.calories_per_serving) * float(meal.servings)

        # Sort by day order
        sorted_daily = [
            {'date': date, 'calories': daily_calories[date]}
            for date in sorted(daily_calories.keys())
        ]

        return Response({'daily_calories': sorted_daily}, status=status.HTTP_200_OK)

class SettingsRestrictedIngredients(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Ingredient.objects.annotate(
            is_restricted=Exists(
                DietaryIngredient.objects.filter(
                    ingredient=OuterRef('pk'),
                    user=request.user
                )
            )
        )

        include_ids = request.query_params.getlist('include')
        include_ids = [int(id) for id in include_ids if id.isdigit()]

        queryset = queryset.annotate(
            is_included=Case(
                When(id__in=include_ids, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )

        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(is_restricted=True) | Q(is_included=True) | Q(name__icontains=search)
            )

        queryset = queryset.annotate(
            priority=Case(
                When(is_restricted=True, then=Value(0)),
                When(is_included=True, then=Value(1)),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by('priority', 'name')

        paginator = Paginator()
        paginated = paginator.paginate_queryset(queryset, request)
        serialized = SettingsIngredientSerializer(paginated, many = True)
        return paginator.get_paginated_response(serialized.data)

    def post(self, request):
        ingredient_ids = request.data.get('ingredient_ids')

        if not isinstance(ingredient_ids, list):
            return Response(
                {'error': 'ingredient_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(ingredient_ids) > 0 and not Ingredient.objects.filter(id__in=ingredient_ids).exists():
            return Response(
                {'error': 'One or more ingredient IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            current_ingredient_ids = set(
                DietaryIngredient.objects.filter(user=request.user).values_list('ingredient_id', flat=True)
            )
            request_ingredient_ids = set(ingredient_ids)

            to_create = request_ingredient_ids - current_ingredient_ids
            to_delete = current_ingredient_ids - request_ingredient_ids

            DietaryIngredient.objects.filter(user=request.user, ingredient_id__in=to_delete).delete()
            DietaryIngredient.objects.bulk_create(
                DietaryIngredient(user=request.user, ingredient_id=ingredient_id)
                for ingredient_id in to_create
            )

        return Response(
            {'message':'Successfully updated restricted ingredients'},
            status.HTTP_200_OK,
        )

class RecipeDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

class GetTags(APIView):
    """Retrieve list of the current user's recipe tags"""
    permission_classes = [permissions.IsAuthenticated]

class GetUserRecipes(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        userRecipe = UserRecipe.objects.filter(user=request.user).all()
        serialized = UserRecipeSerializer(userRecipe, many=True)


        if not userRecipe:
            return Response({'error': 'No user recipe found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialized.data, status=status.HTTP_200_OK)

class UpdateUserRecipe(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, id):
        print(id)
        user = request.user
        ingredients = request.data['ingredients']
        instructions = request.data['instructions']
        original_recipe = request.data['original_recipe']
        # check if user already has a custom recipe saved
        print(f'REQUEST: {request}')
        user_recipe = UserRecipe.objects.filter(user=request.user).filter(original_recipe=Recipe.objects.get(original_recipe))
        if not user_recipe:
            # create new entry
            user_recipe = UserRecipe.objects.create(
              ingredients=ingredients,
              instructions=instructions,
              original_recipe=original_recipe
            )
        user_recipe.ingredients=ingredients
        user_recipe.instructions=instructions
        user_recipe.original_recipe=request.original_recipe

        return Response({}, status=status.HTTP_200_OK)
class TagList(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        queryset = RecipeTag.objects.order_by('name').filter(user=request.user)
        serialized = RecipeTagSerializer(queryset, many = True)
        return Response(
            serialized.data,
            status.HTTP_200_OK
        )

    def post(self, request):
        name = request.data.get('name')
        if not name:
            return Response(
                {'error': 'must specify a name in the request'},
                status.HTTP_400_BAD_REQUEST,
            )

        RecipeTag.objects.get_or_create(name=request.data.get('name'))
        return Response(
            {'message': f'successfully created tag {name}'},
            status.HTTP_200_OK,
        )

class TagDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk):
        queryset = RecipeTag.objects.filter(id=pk)
        if not queryset.exists():
            return Response(
                {'error': 'must pass a valid tag id'},
                status.HTTP_400_BAD_REQUEST
            )
        queryset.delete()
        return Response(
            {'message': 'successfully delete tag'},
            status.HTTP_200_OK
        )

class TaggedRecipeDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, tag_id, recipe_id):
        if not RecipeTag.objects.filter(id=tag_id).exists():
            return Response(
                {'error': 'invalid tag id'},
                status.HTTP_400_BAD_REQUEST
            )
        if not Recipe.objects.filter(id=recipe_id).exists():
            return Response(
                {'error': 'invalid recipe id'},
                status.HTTP_400_BAD_REQUEST
            )

        TaggedRecipe.objects.get_or_create(user=request.user, tag_id=tag_id, recipe_id=recipe_id)

        return Response(
            {'message': 'successfully tagged recipe'},
            status.HTTP_200_OK
        )

    def delete(self, request, tag_id, recipe_id):
        queryset = TaggedRecipe.objects.filter(
            user=request.user,
            tag_id=tag_id,
            recipe_id=recipe_id
        )

        if not queryset.exists():
            return Response(
                {'error': 'unable to find tagged recipe'},
                status.HTTP_400_BAD_REQUEST
            )

        queryset.delete()
        return Response(
            {'message': 'successfully untagged recipe'},
            status.HTTP_200_OK
        )

@tool
def search_recipes_tool(
    title_query: str = "",
    max_calories: int = None,
    min_protein: int = None,
    max_fat: int = None,
    max_carbs: int = None
) -> str:
    """Search for recipes in the recipe library.

    Use this tool to find recipes based on title keywords and nutritional criteria.
    Returns up to 5 recipes with complete details including ingredients and instructions.

    Args:
        title_query: Keywords to search in recipe titles (e.g., "chicken pasta", "salad")
        max_calories: Maximum calories per serving (optional)
        min_protein: Minimum protein in grams (optional)
        max_fat: Maximum fat in grams (optional)
        max_carbs: Maximum carbohydrates in grams (optional)

    Returns:
        A formatted string containing recipe details (id, title, nutrition, ingredients, instructions)
    """
    # Start with base queryset
    queryset = Recipe.objects.all().order_by('-created_at')

    # Apply filters
    if title_query and title_query.strip():
        queryset = queryset.filter(title__icontains=title_query.strip())

    if max_calories is not None:
        queryset = queryset.filter(calories_per_serving__lte=max_calories)

    if min_protein is not None:
        queryset = queryset.filter(protein_g__gte=min_protein)

    if max_fat is not None:
        queryset = queryset.filter(fat_g__lte=max_fat)

    if max_carbs is not None:
        queryset = queryset.filter(carbs_g__lte=max_carbs)

    # Limit to 5 results
    recipes = queryset[:5]

    if not recipes:
        return "No recipes found matching the search criteria."

    # Format results
    results = []
    for recipe in recipes:
        recipe_text = f"""
Recipe ID: {recipe.id}
Title: {recipe.title}
Nutrition (per serving): {recipe.calories_per_serving} calories, {recipe.protein_g}g protein, {recipe.carbs_g}g carbs, {recipe.fat_g}g fat
Servings: {recipe.servings}
Ingredients: {recipe.ingredients}
Instructions: {recipe.instructions}
---"""
        results.append(recipe_text.strip())

    return "\n\n".join(results)

template="""
You are a nutritionist, ready to help customers create nutritious, simple recipes they want to cook. The current customer's name is {username}.

{conversation_history}

Current message from {username}: {message}
""".strip()

prompt = PromptTemplate(
    template=template,
    input_variables=["username", "conversation_history", "message"]
)

llm = ChatOpenAI(
  api_key=os.environ.get("OPEN_ROUTER_API_KEY"),
  base_url="https://openrouter.ai/api/v1",
  model="openrouter/polaris-alpha",
)

# Bind tools to LLM
llm_with_tools = llm.bind_tools([search_recipes_tool])

llm_chain = prompt | llm_with_tools

class NutritionistChat(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the current active conversation with all messages"""
        user = request.user

        # Get active conversation
        conversation = ChatConversation.objects.filter(
            user=user,
            is_active=True
        ).first()

        if not conversation:
            # Return empty conversation if none exists
            return Response(
                {'id': None, 'messages': []},
                status=status.HTTP_200_OK
            )

        # Return full conversation
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Validate message parameter
        message = request.data.get('message')
        if not message or not message.strip():
            return Response(
                {'error': 'Message parameter is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        username = user.username

        # Get or create active conversation
        conversation = ChatConversation.objects.filter(
            user=user,
            is_active=True
        ).first()

        if not conversation:
            conversation = ChatConversation.objects.create(user=user)

        # Get previous messages BEFORE adding the new one
        previous_messages = ChatMessage.objects.filter(
            conversation=conversation
        ).order_by('created_at')

        # Format conversation history for LLM context
        conversation_history = ""
        if previous_messages.exists():
            history_lines = []
            for msg in previous_messages:
                role_label = "User" if msg.role == "user" else "Assistant"
                history_lines.append(f"{role_label}: {msg.content}")
            conversation_history = "Previous conversation:\n" + "\n".join(history_lines)

        # Now save the current user message
        ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        # Get LLM response with full context
        response = llm_chain.invoke({
            "username": username,
            "conversation_history": conversation_history,
            "message": message
        })

        # Check if the response contains tool calls
        tool_calls_data = None
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute each tool call and capture data
            tool_messages = []
            tool_calls_data = []

            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                call_timestamp = timezone.now().isoformat()

                # Execute the tool
                if tool_name == 'search_recipes_tool':
                    tool_result = search_recipes_tool.invoke(tool_args)
                    tool_messages.append({
                        'role': 'tool',
                        'content': tool_result,
                        'tool_call_id': tool_call.get('id', 'unknown')
                    })

                    # Capture tool call data for admin visibility
                    tool_calls_data.append({
                        'tool_name': tool_name,
                        'parameters': tool_args,
                        'result': tool_result,
                        'timestamp': call_timestamp
                    })

            # Build conversation with tool results
            from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

            messages = [
                HumanMessage(content=f"Username: {username}\n\n{conversation_history}\n\nCurrent message: {message}")
            ]

            # Add the AI's response with tool calls
            messages.append(response)

            # Add tool results
            for tool_msg in tool_messages:
                messages.append(ToolMessage(
                    content=tool_msg['content'],
                    tool_call_id=tool_msg['tool_call_id']
                ))

            # Get final response from LLM with tool results
            final_response = llm_with_tools.invoke(messages)
            answer_content = final_response.content
        else:
            # No tool calls, use the response directly
            answer_content = response.content

        # Save assistant response with tool call data
        ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=answer_content,
            tool_calls=tool_calls_data
        )

        # Return full conversation
        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClearConversation(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Mark current active conversation as inactive
        ChatConversation.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)

        return Response(
            {'success': True, 'message': 'Conversation cleared'},
            status=status.HTTP_200_OK
        )

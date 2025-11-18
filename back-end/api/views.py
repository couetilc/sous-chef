import os
import logging
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
from django.db.models import Exists, OuterRef, Case, When, Value, IntegerField, Q, BooleanField, F, FloatField, ExpressionWrapper
from django.contrib.postgres.search import SearchQuery, SearchRank
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User, Group

logger = logging.getLogger(__name__)
from .serializers import UserSerializer, GroupSerializer, UserRegistrationSerializer, IngredientSerializer, DietSerializer, CookedRecipeSerializer, MealSerializer, OnboardSerializer, SettingsIngredientSerializer, UserInventorySerializer, UserCuratedInventorySerializer, TagSerializer, UserRecipeSerializer, CuratedIngredientSerializer, MealPlanSerializer, MealPlanEntrySerializer
from decimal import Decimal, InvalidOperation
from .models import (
    Ingredient, DietaryIngredient, Diet, UserDiet,
    Recipe, CookedRecipe, Meal, FavoriteRecipe, UserInventory, UserCuratedInventory, OnboardingSubmission, RecipeIngredient, HealthDetails, RecipeTag, TaggedRecipe,
    ChatConversation, ChatMessage, CuratedIngredient, MealPlan, MealPlanEntry, UserRecipe
)
from .serializers import (
    UserSerializer, GroupSerializer, UserRegistrationSerializer,
    IngredientSerializer, DietSerializer,
    CookedRecipeSerializer, MealSerializer, RecipeSerializer,
    ChatConversationSerializer, ChatMessageSerializer
)
from .utils.recommended import compute_recommendations
from zoneinfo import ZoneInfo
from .ai import NutritionistAgent, SousChefAgent

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

class CuratedIngredientList(generics.ListAPIView):
    """List all curated (staple) ingredients"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CuratedIngredientSerializer
    pagination_class = Paginator
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', '^name']
    # Use model default ordering: ['-frequency', 'name'] (most common first)

    def get_queryset(self):
        """Return only approved curated ingredients by default"""
        queryset = CuratedIngredient.objects.all()

        # Filter by approval status (default: only approved)
        show_unapproved = self.request.query_params.get('show_unapproved', 'false').lower() == 'true'
        if not show_unapproved:
            queryset = queryset.filter(is_approved=True)

        # Exclude ingredients already in user's inventory if requested
        exclude_inventory = self.request.query_params.get('exclude_inventory', 'false').lower() == 'true'
        if exclude_inventory:
            # Get curated ingredient IDs that are already in the user's inventory
            user_inventory_ids = self.request.user.curated_inventory_items.values_list('curated_ingredient_id', flat=True)
            queryset = queryset.exclude(id__in=user_inventory_ids)

        return queryset


class CuratedIngredientDetail(generics.RetrieveAPIView):
    """Retrieve a single curated ingredient"""
    permission_classes = [permissions.IsAuthenticated]
    queryset = CuratedIngredient.objects.all()
    serializer_class = CuratedIngredientSerializer


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
        # Get sort_by parameter (default: "accessibility")
        sort_by = request.data.get('sort_by', 'accessibility')

        # Always start with accessibility annotation (needed for serializer)
        queryset = Recipe.objects.order_by_ingredient_accessibility()

        # Full-text search support (searches title, ingredients, instructions)
        search_query = request.data.get('search_query')
        if search_query and search_query.strip():
            # Use PostgreSQL full-text search
            query = SearchQuery(search_query, config='english')
            queryset = queryset.annotate(
                search_rank=SearchRank('search_vector', query)
            ).filter(
                search_vector=query
            )
            # If search is active and sort_by is relevance, use search ranking
            if sort_by == 'relevance':
                queryset = queryset.order_by('-search_rank', 'title')

        # Legacy title search (kept for backward compatibility)
        title = request.data.get('title')
        if title and not search_query:
            # Only use title__icontains if search_query is not provided
            queryset = queryset.filter(title__icontains=title)

        # NEW: Curated ingredient filtering
        curated_ingredients = request.data.get('curated_ingredients')
        curated_ingredients_match_all = request.data.get('curated_ingredients_match_all', True)
        if curated_ingredients:
            if curated_ingredients_match_all:
                # AND logic: recipe must have ALL selected ingredients
                for curated_ingredient_id in curated_ingredients:
                    queryset = queryset.filter(
                        curated_ingredients__curated_ingredient_id=curated_ingredient_id
                    )
            else:
                # OR logic: recipe must have ANY of the selected ingredients
                q_objects = Q()
                for curated_ingredient_id in curated_ingredients:
                    q_objects |= Q(curated_ingredients__curated_ingredient_id=curated_ingredient_id)
                queryset = queryset.filter(q_objects)

        # OLD: Ingredient filtering (kept for backward compatibility)
        ingredients = request.data.get('ingredients')
        if ingredients:
            for ingredient_id in ingredients:
                queryset = queryset.filter(
                    ingredients_list__ingredient_id=ingredient_id
                )

        # NEW: Curated inventory filtering
        searchCuratedInventory = request.data.get('searchCuratedInventory')
        if searchCuratedInventory:
            curated_ingredient_ids = request.user.curated_inventory_items.values_list('curated_ingredient_id', flat=True)
            queryset = queryset.filter(
                curated_ingredients__curated_ingredient_id__in=curated_ingredient_ids
            )

        # OLD: Inventory filtering (kept for backward compatibility)
        searchInventory = request.data.get('searchInventory')
        if searchInventory:
            ingredient_ids = request.user.inventory_items.values_list('ingredient_id')
            queryset = queryset.filter(
                ingredients_list__ingredient_id__in=ingredient_ids
            )

        searchFavorite = request.data.get('searchFavorite')
        if searchFavorite:
            queryset = queryset.filter(user_favorites__isnull=False)

        # Remove duplicates that can occur from JOIN operations
        queryset = queryset.distinct()

        # Apply sorting based on sort_by parameter
        if sort_by == 'deliciousness':
            # Sort by deliciousness score (highest first)
            queryset = queryset.order_by('-deliciousness_score')
        elif sort_by == 'combined':
            # Sort by combined score (accessibility * deliciousness)
            queryset = queryset.annotate(
                combined_score=ExpressionWrapper(
                    F('accessibility_score') * F('deliciousness_score'),
                    output_field=FloatField()
                )
            ).order_by('-combined_score')
        # else: keep default accessibility ordering from order_by_ingredient_accessibility()

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

class UserCuratedInventoryList(APIView):
    """List user curated inventory for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        inventories = UserCuratedInventory.objects.filter(user=request.user).order_by('curated_ingredient__name')
        serialized = UserCuratedInventorySerializer(inventories, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def post(self, request):
        curated_ingredient_ids = request.data.get('curated_ingredient_ids')

        if not isinstance(curated_ingredient_ids, list):
            return Response(
                {'error': 'curated_ingredient_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(curated_ingredient_ids) > 0 and not CuratedIngredient.objects.filter(id__in=curated_ingredient_ids).exists():
            return Response(
                {'error': 'One or more curated ingredient IDs are invalid'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for curated_ingredient_id in curated_ingredient_ids:
                UserCuratedInventory.objects.get_or_create(
                    user=request.user,
                    curated_ingredient_id=curated_ingredient_id
                )

        return Response(
            {'message': 'successfully created curated inventory items'},
            status=status.HTTP_201_CREATED,
        )

class UserCuratedInventoryDetail(APIView):
    """Retrieve, update or delete a user curated inventory item"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            inventory = UserCuratedInventory.objects.get(id=id, user=request.user)
        except UserCuratedInventory.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'id': inventory.id,
            'curated_ingredient': CuratedIngredientSerializer(inventory.curated_ingredient).data,
        }
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            inventory = UserCuratedInventory.objects.get(id=id, user=request.user)
        except UserCuratedInventory.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        inventory.delete()
        return Response(
            {'message': 'Successfully deleted curated inventory item'},
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
        serialized = TagSerializer(queryset, many = True)
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

class NutritionistChat(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the current active conversation with all messages"""
        user = request.user

        # Get active conversation with messages prefetched to avoid N+1 query
        conversation = ChatConversation.objects.filter(
            user=user,
            channel='nutritionist',
            is_active=True
        ).prefetch_related('messages').first()

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

        # Use atomic transaction to ensure data consistency
        try:
            with transaction.atomic():
                # Get or create active conversation (prevents race condition)
                conversation, created = ChatConversation.objects.get_or_create(
                    user=user,
                    channel='nutritionist',
                    is_active=True
                )

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

                # Save the current user message
                ChatMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=message
                )

                try:
                    agent = NutritionistAgent(user=user)
                    result = agent.chat(
                        message=message,
                        conversation_history=conversation_history
                    )
                except ValueError as e:
                    # Handle missing API key or configuration errors
                    logger.error(f"Configuration error for user {user.username}: {e}")
                    return Response(
                        {'error': 'AI service is not properly configured. Please contact support.'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                except Exception as e:
                    # Handle LLM API failures gracefully
                    logger.error(f"AI agent error for user {user.username}: {e}", exc_info=True)
                    result = {
                        'content': "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
                        'tool_calls': []
                    }

                # Save assistant response with tool call data
                ChatMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=result['content'],
                    tool_calls=result['tool_calls']
                )

                # Prefetch messages to avoid N+1 query when serializing
                conversation = ChatConversation.objects.prefetch_related('messages').get(id=conversation.id)

                # Return full conversation
                serializer = ChatConversationSerializer(conversation)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in nutritionist chat for user {user.username}: {e}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearConversation(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Mark current active conversation as inactive
        ChatConversation.objects.filter(
            user=request.user,
            channel='nutritionist',
            is_active=True
        ).update(is_active=False)

        return Response(
            {'success': True, 'message': 'Conversation cleared'},
            status=status.HTTP_200_OK
        )


class MealPlanListCreateView(APIView):
    """List user's meal plans or create a new one"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        meal_plans = MealPlan.objects.filter(user=request.user).prefetch_related('entries__recipe')
        serializer = MealPlanSerializer(meal_plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        week_start = request.data.get('week_start')
        meal_plan = MealPlan.objects.create(user=request.user, week_start=week_start)
        serializer = MealPlanSerializer(meal_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MealPlanDetailView(APIView):
    """Retrieve or update a specific meal plan"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            meal_plan = MealPlan.objects.get(id=pk, user=request.user)
            meal_plan.entries.prefetch_related('recipe')
        except MealPlan.DoesNotExist:
            return Response({'error': 'Meal plan not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = MealPlanSerializer(meal_plan)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MealPlanEntryCreateView(APIView):
    """Add a recipe to a meal plan"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            meal_plan = MealPlan.objects.get(id=pk, user=request.user)
        except MealPlan.DoesNotExist:
            return Response({'error': 'Meal plan not found'}, status=status.HTTP_404_NOT_FOUND)

        day_of_week = request.data.get('day_of_week')
        meal_index = request.data.get('meal_index')
        recipe_id = request.data.get('recipe_id')
        servings = request.data.get('servings', 1)

        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

        entry, created = MealPlanEntry.objects.get_or_create(
            meal_plan=meal_plan,
            day_of_week=day_of_week,
            meal_index=meal_index,
            defaults={'recipe': recipe, 'servings': servings}
        )

        if not created:
            entry.recipe = recipe
            entry.servings = servings
            entry.save()

        serializer = MealPlanEntrySerializer(entry)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MealPlanEntryDeleteView(APIView):
    """Remove a recipe from a meal plan"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, entry_id):
        try:
            meal_plan = MealPlan.objects.get(id=pk, user=request.user)
            entry = MealPlanEntry.objects.get(id=entry_id, meal_plan=meal_plan)
        except (MealPlan.DoesNotExist, MealPlanEntry.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        entry.delete()
        return Response({'message': 'Entry deleted'}, status=status.HTTP_200_OK)

# AI Sous Chef endpoint. WIP.
class SousChefInterpret(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        recipe = request.data.get('recipe')
        curr_step_index = request.data.get('current_step_index', 0)

        # 1. Predict intent
        recipe_step = recipe[curr_step_index]
        #intent = classify_intent(message, recipe_step)

        # 2. Handle the intent
        #result = handle_intent(intent, recipe, curr_step_index)

        # Integrate commented code when with Branton's AI Sous Chef model later.

        return Response({
            "intent": intent.value,
            "new_step_index": result['step_index'],
            "assistant_message": result['message']
        })
class SousChefChat(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the current active SousChef conversation with all messages"""
        user = request.user

        conversation = ChatConversation.objects.filter(
            user=user,
            channel='souschef',
            is_active=True,
        ).prefetch_related('messages').first()

        if not conversation:
            return Response({'id': None, 'messages': []}, status=status.HTTP_200_OK)

        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        message = request.data.get('message')
        if not message or not message.strip():
            return Response(
                {'error': 'Message parameter is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        try:
            with transaction.atomic():
                conversation, created = ChatConversation.objects.get_or_create(
                    user=user,
                    channel='souschef',
                    is_active=True,
                )

                previous_messages = ChatMessage.objects.filter(
                    conversation=conversation
                ).order_by('created_at')

                conversation_history = ""
                if previous_messages.exists():
                    history_lines = []
                    for msg in previous_messages:
                        role_label = "User" if msg.role == "user" else "Assistant"
                        history_lines.append(f"{role_label}: {msg.content}")
                    conversation_history = "Previous conversation:\n" + "\n".join(history_lines)

                ChatMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=message,
                )

                try:
                    agent = SousChefAgent(user=user)
                    result = agent.chat(
                        message=message,
                        conversation_history=conversation_history,
                    )
                except ValueError as e:
                    logger.error(f"SousChef config error for user {user.username}: {e}")
                    return Response(
                        {'error': 'AI service is not properly configured. Please contact support.'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
                except Exception as e:
                    logger.error(f"SousChef agent error for user {user.username}: {e}", exc_info=True)
                    result = {
                        'content': "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
                        'tool_calls': [],
                    }

                ChatMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=result['content'],
                    tool_calls=result['tool_calls'],
                )

                conversation = ChatConversation.objects.prefetch_related('messages').get(id=conversation.id)
                serializer = ChatConversationSerializer(conversation)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in SousChef chat for user {user.username}: {e}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ClearSousChefConversation(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ChatConversation.objects.filter(
            user=request.user,
            channel='souschef',
            is_active=True,
        ).update(is_active=False)

        return Response(
            {'success': True, 'message': 'SousChef conversation cleared'},
            status=status.HTTP_200_OK,
        )

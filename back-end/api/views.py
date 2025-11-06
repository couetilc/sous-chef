from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User, Group
from .serializers import UserSerializer, GroupSerializer, UserRegistrationSerializer, IngredientSerializer, DietSerializer, CookedRecipeSerializer, MealSerializer, OnboardSerializer
from decimal import Decimal, InvalidOperation
from .models import (
    Ingredient, DietaryIngredient, Diet, UserDiet,
    Recipe, CookedRecipe, Meal, FavoriteRecipe, UserInventory, OnboardingSubmission, RecipeIngredient, HealthDetails
)
from .serializers import (
    UserSerializer, GroupSerializer, UserRegistrationSerializer,
    IngredientSerializer, DietSerializer,
    CookedRecipeSerializer, MealSerializer, RecipeSerializer
)
from .utils.recommended import compute_recommendations

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
        OnboardingSubmission.create(user=user, has_onboarded=False, skipped=False)
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
            return Response({'error': 'No health profile found'}, status=status.HTTP_404_NOT_FOUND)
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
        user.health.first().age = request.data['age']
        user.health.first().height_ft = request.data['height_ft']
        user.health.first().height_in = request.data['height_in']
        user.health.first().weight = request.data['weight']
        user.health.first().activity_level = request.data['activity_level']
        user.health.first().goal = request.data['goal']
        user.health.first().sex = request.data['sex']

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
    queryset = Diet.objects.all()
    serializer_class = DietSerializer

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

        ingredients = request.POST.getlist('ingredients')
        if ingredients:
            for id in ingredients:
                recipes = Recipe.objects.filter(ingredients_list__ingredient__id=id)
                queryset = queryset.intersection(recipes)

        searchInventory = request.data.get('searchInventory')
        if searchInventory and searchInventory == 'True':
            inventoryRecipes = Recipe.objects.none()
            ingredients = Ingredient.objects.filter(in_inventories__user=request.user)
            for ingredient in ingredients:
                recipes = Recipe.objects.filter(ingredients_list__ingredient=ingredient)
                inventoryRecipes = inventoryRecipes.union(recipes)
            queryset = queryset.intersection(inventoryRecipes)

        searchFavorite = request.data.get('searchFavorite')
        if searchFavorite and searchFavorite == 'True':
            queryset = queryset.filter(user_favorites__isnull=False)

        paginator = Paginator()
        page = paginator.paginate_queryset(queryset, request)
        
        serializer = RecipeSerializer(page, many=True, context = {'user': request.user})
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

        data = []
        for item in inventories:
            data.append({
                'id': item.id,
                'ingredient': IngredientSerializer(item.ingredient).data,
            })

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        ingredient_id = request.data.get('ingredient_id')
        if ingredient_id is None:
            return Response({'error': 'ingredient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return Response({'error': 'Ingredient not found'}, status=status.HTTP_404_NOT_FOUND)

        inventory, created = UserInventory.objects.get_or_create(user=request.user, ingredient=ingredient)

        serializer_data = {
            'id': inventory.id,
            'ingredient': IngredientSerializer(inventory.ingredient).data,
        }

        return Response(serializer_data, status=status.HTTP_201_CREATED)

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
        return Response(status=status.HTTP_204_NO_CONTENT)

class NutritionLastDayView(APIView):
    """Get total calories consumed in the last day"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        end_time = timezone.now()
        start_time = end_time - timedelta(days=1)

        meals = Meal.objects.filter(
            cooked_recipe__user=request.user,
            eaten_at__range=(start_time, end_time)
        )

        total_calories = 0.0
        for meal in meals:
            recipe = meal.cooked_recipe.recipe
            if recipe.calories_per_serving is not None:
                total_calories += float(recipe.calories_per_serving) * float(meal.servings)

        return Response({'calories': total_calories}, status=status.HTTP_200_OK)

class NutritionLastWeekView(APIView):
    """Get total calories consumed in the last week"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        end_time = timezone.now()
        start_time = end_time - timedelta(days=7)

        meals = Meal.objects.filter(
            cooked_recipe__user=request.user,
            eaten_at__range=(start_time, end_time)
        )

        print("meals: ", meals)

        total_calories = 0.0
        for meal in meals:
            recipe = meal.cooked_recipe.recipe
            if recipe.calories_per_serving is not None:
                total_calories += float(recipe.calories_per_serving) * float(meal.servings)

        return Response({'calories': total_calories}, status=status.HTTP_200_OK)
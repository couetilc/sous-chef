from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User, Group
from .models import Ingredient, DietaryIngredient, Diet, UserDiet, CookedRecipe, Meal
from .serializers import UserSerializer, GroupSerializer, UserRegistrationSerializer, IngredientSerializer, DietSerializer, CookedRecipeSerializer, MealSerializer, OnboardSerializer

# Create your views here.
def index(request):
    return HttpResponse("<h1>Hello, World!</h1>")

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
    permission_class = [permissions.IsAuthenticated]
    def get(self, request):
        print("here")
        user = request.user
        print(user.onboarded.first().has_onboarded)
        print(user)
        return Response({
            'onboarded': user.onboarded.first().has_onboarded
        }, status=status.HTTP_200_OK)

class UpdateOnboardedView(APIView):
    """Update user's onboarding completion status"""
    permission_class = [permissions.IsAuthenticated]
    def post(self, request):
        user = request.user
        user.onboarded.has_onboarded=request.new_onboarded,
        return Response({ 'message': 'Successfully completed onboarding'}, status=status.HTTP_200_OK)


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


class DietaryIngredientList(generics.ListAPIView):
    """List restricted ingredients for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = IngredientSerializer

    def get_queryset(self):
        """Filter dietary ingredients to only those restricted by the current user"""
        # Get the DietaryIngredient objects for the current user, then extract just the Ingredient objects
        dietary_ingredient_ids = DietaryIngredient.objects.filter(
            user=self.request.user
        ).values_list('ingredient_id', flat=True)

        return Ingredient.objects.filter(id__in=dietary_ingredient_ids)

class UpdateDietaryIngredientList(APIView):
    permission_classes = [permissions.IsAuthenticated]   

    def post(self, request):
        added = request.data.get('added')
        removed = request.data.get('removed')

        print(added)
        print(removed)

        addedIngredients = Ingredient.objects.filter(id__in=added)
        for ingredient in addedIngredients:
            DietaryIngredient.objects.get_or_create(ingredient=ingredient, user=self.request.user)
        
        removedIngredients = Ingredient.objects.filter(id__in=removed)
        for ingredient in removedIngredients:
            target = DietaryIngredient.objects.filter(ingredient=ingredient, user=self.request.user)
            target.delete()


        print(DietaryIngredient.objects.all())

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
        """Filter diets to only those selected by the current user"""
        # Get the DietaryIngredient objects for the current user, then extract just the Ingredient objects
        selected_diet_ids = UserDiet.objects.filter(
            user=self.request.user
        ).values_list('diet_id', flat=True)

        return Ingredient.objects.filter(id__in=selected_diet_ids)

class UpdateDiets(APIView):
    permission_classes = [permissions.IsAuthenticated]   

    def post(self, request):
        added = request.data.get('added')
        removed = request.data.get('removed')

        print(added)
        print(removed)

        addedDiets= Diet.objects.filter(id__in=added)
        for diet in addedDiets:
            UserDiet.objects.get_or_create(diet=diet, user=self.request.user)
        
        removedDiets = Diet.objects.filter(id__in=removed)
        for diet in removedDiets:
            target = UserDiet.objects.filter(diet=diet, user=self.request.user)
            target.delete()


        print(UserDiet.objects.all())

        return Response({'message': 'Successfully updated diets'}, status=status.HTTP_200_OK)

class RecipeHistoryView(generics.ListAPIView):
    """List all cooked recipes for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CookedRecipeSerializer

    def get_queryset(self):
        """Filter cooked recipes to only those for the current user"""
        return CookedRecipe.objects.filter(user=self.request.user)

class CreateMealView(APIView):
    """Create a meal from a cooked recipe"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, cooked_recipe_id):
        try:
            cooked_recipe = CookedRecipe.objects.get(id=cooked_recipe_id)
        except CookedRecipe.DoesNotExist:
            return Response(
                {'error': 'Cooked recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify that the cooked recipe belongs to the authenticated user
        if cooked_recipe.user != request.user:
            return Response(
                {'error': 'You do not have permission to create a meal from this cooked recipe'},
                status=status.HTTP_403_FORBIDDEN
            )

        portion = request.data.get('portion')
        if portion is None:
            return Response(
                {'error': 'Portion is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the meal
        meal = Meal(cooked_recipe=cooked_recipe, portion=portion)

        try:
            meal.save()  # This will call full_clean() which validates portion constraints
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MealSerializer(meal)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

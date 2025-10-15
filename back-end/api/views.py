from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User, Group
from .models import Ingredient, DietaryIngredient, Diet, UserDiet
from .serializers import UserSerializer, GroupSerializer, UserRegistrationSerializer, IngredientSerializer, DietSerializer

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

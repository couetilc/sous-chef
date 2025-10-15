from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('csrf/', views.CSRFTokenView.as_view(), name='csrf-token'),
    # User and group management
    path('users/', views.UserList.as_view()),
    path('users/<pk>/', views.UserDetails.as_view()),
    path('groups/', views.GroupList.as_view()),
    # Ingredient endpoints
    path('ingredients/', views.IngredientList.as_view(), name='ingredient-list'),
    path('ingredients/restricted/', views.DietaryIngredientList.as_view(), name='restricted-ingredients'),
    path('ingredients/updateRestricted/', views.UpdateDietaryIngredientList.as_view(), name='restricted-ingredients-update'),
    # Diet endpoints
    path('diets/', views.DietList.as_view(), name='diet-list'),
    path('diets/selected/', views.SelectedDietList.as_view(), name='selected-diet-list')
]

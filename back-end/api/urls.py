from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.LoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('user/updateEmail/', views.UpdateUserEmail.as_view(), name='user-update-email'),
    path('user/updatePassword/', views.UpdateUserPassword.as_view(), name='user-update-password'),
    path('user/delete/', views.DeleteUser.as_view(), name='user-delete'),
    path('user/isOnboarded/', views.OnboardedView.as_view(), name='user-is-onboarded'),
    path('user/updateOnboarded/', views.UpdateOnboardedView.as_view(), name='user-update-onboarded'),
    path('user/health/', views.HealthView.as_view(), name='user-health'),
    path('user/updateHealth/', views.UpdateHealthView.as_view(), name="user-update-health"),
    path('user/health/recommendations/', views.HealthRecommendationsView.as_view(), name='user-health-recommendations'),
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
    path('diets/selected/', views.SelectedDietList.as_view(), name='selected-diet-list'),
    path('diets/updateSelected/', views.UpdateDiets.as_view(), name='selected-diet-update'),
    path('diets/sync/', views.DietListSync.as_view(), name="diet-list-sync"),

    # Recipe endpoints
    path('recipes/searchFiltered/', views.GetRecipesFiltered.as_view(), name='recipes-search-filtered'),
    path('recipes/createFavorite/', views.CreateFavoriteRecipe.as_view(), name='recipes-create-favorite'),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe-detail'),

    # Nutrition preview endpoint
    path('recipes/<int:id>/nutrition/', views.RecipeNutritionPreviewView.as_view(), name='recipe-nutrition'),

    # Recipe history endpoints
    path('recipe_history/', views.RecipeHistoryView.as_view(), name='recipe-history'),
    path('recipe_history/<int:cooked_recipe_id>/meal/', views.CreateMealView.as_view(), name='create-meal'),

    # User inventory endpoints
    path('user_inventory/', views.UserInventoryList.as_view(), name='user-inventory-list'),
    path('user_inventory/<int:id>/', views.UserInventoryDetail.as_view(), name='user-inventory-detail'),

    # Nutrition Summary endpoints
    path('nutrition/nutrition_last_day/', views.NutritionLastDayView.as_view(), name='nutrition-last-day'),
    path('nutrition/calories_last_week/', views.CaloriesLastWeekView.as_view(), name='calories-last-week'),
    # Settings endpoints
    path('settings/restricted_ingredients/',
         views.SettingsRestrictedIngredients.as_view(),
         name='settings-restricted-ingredients'),
]
